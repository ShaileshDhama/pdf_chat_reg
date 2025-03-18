from typing import Dict, Optional
from eth_account.messages import encode_defunct
from web3 import Web3
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel
import json
from pathlib import Path

class Web3Auth:
    def __init__(self, web3_provider: str, jwt_secret: str):
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        self.jwt_secret = jwt_secret
        self.nonces: Dict[str, str] = {}  # address -> nonce
        
    async def generate_nonce(self, address: str) -> str:
        """Generate a unique nonce for the address."""
        nonce = f"Welcome to LEGALe TROY!\n\nPlease sign this message to verify your ownership of the address: {address}\n\nNonce: {datetime.utcnow().timestamp()}"
        self.nonces[address.lower()] = nonce
        return nonce

    async def verify_signature(self, address: str, signature: str) -> Dict:
        """Verify the signature of a nonce."""
        try:
            address = address.lower()
            if address not in self.nonces:
                return {
                    "success": False,
                    "error": "No nonce found for address"
                }

            nonce = self.nonces[address]
            message = encode_defunct(text=nonce)
            
            # Recover the address from the signature
            recovered_address = self.w3.eth.account.recover_message(message, signature=signature)
            
            if recovered_address.lower() == address:
                # Generate JWT token
                token = self._generate_token(address)
                
                # Clear the used nonce
                del self.nonces[address]
                
                return {
                    "success": True,
                    "token": token,
                    "address": address
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid signature"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_token(self, address: str) -> str:
        """Generate a JWT token for the authenticated address."""
        payload = {
            "address": address,
            "exp": datetime.utcnow() + timedelta(days=1),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_token(self, token: str) -> Dict:
        """Verify a JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return {
                "success": True,
                "address": payload["address"]
            }
        except jwt.ExpiredSignatureError:
            return {
                "success": False,
                "error": "Token has expired"
            }
        except jwt.InvalidTokenError:
            return {
                "success": False,
                "error": "Invalid token"
            }

    async def check_permissions(self, address: str, required_role: str) -> bool:
        """Check if an address has the required role/permissions."""
        try:
            # Load roles contract ABI
            contract_path = Path(__file__).parent / "contracts" / "RoleManager.json"
            with open(contract_path) as f:
                contract_json = json.load(f)
                roles_contract = self.w3.eth.contract(
                    address=contract_json["address"],
                    abi=contract_json["abi"]
                )
            
            # Check role
            has_role = roles_contract.functions.hasRole(
                self.w3.keccak(text=required_role),
                address
            ).call()
            
            return has_role
        except Exception:
            return False

    async def get_user_profile(self, address: str) -> Dict:
        """Get the user's profile and roles."""
        try:
            # Define possible roles
            roles = ["admin", "lawyer", "paralegal", "client"]
            user_roles = []
            
            # Check each role
            for role in roles:
                if await self.check_permissions(address, role):
                    user_roles.append(role)
            
            # Get ENS name if available
            ens_name = None
            if self.w3.is_connected() and self.w3.ens is not None:
                try:
                    ens_name = self.w3.ens.name(address)
                except Exception:
                    pass
            
            return {
                "success": True,
                "profile": {
                    "address": address,
                    "ens_name": ens_name,
                    "roles": user_roles,
                    "joined_at": datetime.utcnow().isoformat()  # In production, get from contract
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def refresh_token(self, token: str) -> Dict:
        """Refresh a JWT token."""
        try:
            # Verify current token
            verification = self.verify_token(token)
            if not verification["success"]:
                return verification
            
            # Generate new token
            new_token = self._generate_token(verification["address"])
            
            return {
                "success": True,
                "token": new_token,
                "address": verification["address"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class RoleManager:
    def __init__(self, web3_provider: str, contract_address: str):
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        
        # Load contract ABI
        contract_path = Path(__file__).parent / "contracts" / "RoleManager.json"
        with open(contract_path) as f:
            contract_json = json.load(f)
            self.contract = self.w3.eth.contract(
                address=contract_address,
                abi=contract_json["abi"]
            )

    async def grant_role(self, address: str, role: str, admin_key: str) -> Dict:
        """Grant a role to an address."""
        try:
            # Create transaction
            role_hash = self.w3.keccak(text=role)
            
            tx = self.contract.functions.grantRole(
                role_hash,
                address
            ).build_transaction({
                'from': self.w3.eth.account.from_key(admin_key).address,
                'nonce': self.w3.eth.get_transaction_count(
                    self.w3.eth.account.from_key(admin_key).address
                ),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, admin_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "success": True,
                "transaction_hash": receipt["transactionHash"].hex()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
