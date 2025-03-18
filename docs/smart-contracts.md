# Smart Contract Integration Guide

## Overview
LEGALe TROY uses smart contracts for document verification, signatures, and access control. Our contracts are deployed on multiple EVM-compatible chains.

## Smart Contracts

### DocumentRegistry.sol
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract DocumentRegistry {
    struct Document {
        bytes32 hash;
        address owner;
        mapping(address => bool) signatures;
        uint256 timestamp;
        string ipfsCid;
    }

    mapping(bytes32 => Document) public documents;
    
    event DocumentRegistered(bytes32 indexed hash, address indexed owner);
    event DocumentSigned(bytes32 indexed hash, address indexed signer);
    
    function registerDocument(bytes32 hash, string memory ipfsCid) public {
        // Implementation
    }
    
    function signDocument(bytes32 hash) public {
        // Implementation
    }
    
    function verifyDocument(bytes32 hash) public view returns (bool) {
        // Implementation
    }
}
```

### AccessControl.sol
```solidity
pragma solidity ^0.8.19;

contract AccessControl {
    mapping(address => bool) public authorized;
    
    function grantAccess(address user) public {
        // Implementation
    }
    
    function revokeAccess(address user) public {
        // Implementation
    }
}
```

## Integration Steps

### 1. Web3 Connection
```javascript
// frontend/src/services/web3.ts
import { ethers } from 'ethers';
import DocumentRegistry from './abi/DocumentRegistry.json';

export async function connectWallet() {
    if (window.ethereum) {
        const provider = new ethers.providers.Web3Provider(window.ethereum);
        await provider.send("eth_requestAccounts", []);
        return provider;
    }
    throw new Error("Web3 wallet not found");
}
```

### 2. Document Registration
```javascript
export async function registerDocument(hash: string, ipfsCid: string) {
    const contract = new ethers.Contract(
        CONTRACT_ADDRESS,
        DocumentRegistry.abi,
        signer
    );
    
    const tx = await contract.registerDocument(hash, ipfsCid);
    await tx.wait();
}
```

### 3. Document Signing
```javascript
export async function signDocument(hash: string) {
    const contract = new ethers.Contract(
        CONTRACT_ADDRESS,
        DocumentRegistry.abi,
        signer
    );
    
    const tx = await contract.signDocument(hash);
    await tx.wait();
}
```

## Security Considerations

### 1. Gas Optimization
- Batch operations when possible
- Use events for logging
- Optimize storage usage

### 2. Access Control
- Implement role-based access
- Use OpenZeppelin's AccessControl
- Regular security audits

### 3. Privacy
- Store sensitive data off-chain
- Use zero-knowledge proofs
- Implement proxy contracts

## Supported Networks
- Ethereum Mainnet
- Polygon
- Arbitrum
- Optimism

## Gas Fee Management
- Gas estimation API
- Dynamic fee adjustment
- Gas tank for enterprise users

## Testing
```bash
# Run contract tests
npx hardhat test

# Deploy to testnet
npx hardhat run scripts/deploy.ts --network polygon-mumbai
```

## Deployment
1. Deploy contracts
2. Verify on Etherscan
3. Update frontend config
4. Test integration

## Monitoring
- Contract events
- Transaction status
- Gas usage metrics
- Error tracking

## Support
For smart contract support:
- Join our Discord
- Check GitHub issues
- Contact blockchain@legale-troy.com
