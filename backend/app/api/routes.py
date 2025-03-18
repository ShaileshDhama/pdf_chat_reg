from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, WebSocket, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict
import uuid
import os
from datetime import datetime
import json

from ..core.config import settings
from ..schemas.documents import FileUpload, DocumentAnalysis, DocumentVerification
from ..schemas.auth import AuthRequest, AuthResponse
from ..ai.document_analyzer import DocumentAnalyzer
from ..blockchain.document_registry import DocumentRegistry
from ..core.collaboration import CollaborationManager
from ..security.web3_auth import Web3Auth

api_router = APIRouter()
security = HTTPBearer()
document_analyzer = DocumentAnalyzer()
document_registry = DocumentRegistry(
    settings.WEB3_PROVIDER_URL,
    settings.DOCUMENT_REGISTRY_ADDRESS,
    settings.IPFS_URL
)
collaboration_manager = CollaborationManager()
web3_auth = Web3Auth(settings.WEB3_PROVIDER_URL, settings.JWT_SECRET)

# Auth Routes
@api_router.post("/auth/nonce", response_model=Dict)
async def get_nonce(address: str):
    """Get a nonce for Web3 authentication."""
    nonce = await web3_auth.generate_nonce(address)
    return {"nonce": nonce}

@api_router.post("/auth/verify", response_model=AuthResponse)
async def verify_signature(auth_request: AuthRequest):
    """Verify Web3 signature and issue JWT token."""
    result = await web3_auth.verify_signature(
        auth_request.address,
        auth_request.signature
    )
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

# Document Routes
@api_router.post("/documents/upload/", response_model=FileUpload)
async def upload_document(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload and process a legal document."""
    # Verify JWT token
    auth_result = web3_auth.verify_token(credentials.credentials)
    if not auth_result["success"]:
        raise HTTPException(status_code=401, detail=auth_result["error"])

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    upload_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{upload_id}.pdf")
    
    try:
        # Save file
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process with AI
        analysis_result = await document_analyzer.process_document(file_path)
        if not analysis_result["success"]:
            raise Exception(analysis_result["error"])
        
        # Register on blockchain
        blockchain_result = await document_registry.register_document(
            file_path,
            auth_result["address"],
            settings.BLOCKCHAIN_PRIVATE_KEY
        )
        if not blockchain_result["success"]:
            raise Exception(blockchain_result["error"])
        
        return FileUpload(
            filename=file.filename,
            file_size=os.path.getsize(file_path),
            file_type=file.content_type,
            upload_id=upload_id,
            analysis=analysis_result["analysis"],
            blockchain_hash=blockchain_result["document_hash"],
            ipfs_hash=blockchain_result["ipfs_hash"]
        )
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/documents/{document_id}/analyze", response_model=DocumentAnalysis)
async def analyze_document(
    document_id: str,
    query: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Analyze a document using AI."""
    # Verify JWT token
    auth_result = web3_auth.verify_token(credentials.credentials)
    if not auth_result["success"]:
        raise HTTPException(status_code=401, detail=auth_result["error"])

    file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        if query:
            result = await document_analyzer.query_document(file_path, query)
        else:
            result = await document_analyzer.process_document(file_path)
            
        if not result["success"]:
            raise Exception(result["error"])
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/documents/{document_id}/verify", response_model=DocumentVerification)
async def verify_document(
    document_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify a document's authenticity on the blockchain."""
    # Verify JWT token
    auth_result = web3_auth.verify_token(credentials.credentials)
    if not auth_result["success"]:
        raise HTTPException(status_code=401, detail=auth_result["error"])

    file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        result = await document_registry.verify_document(file_path)
        if not result["success"]:
            raise Exception(result["error"])
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Collaboration Routes
@api_router.websocket("/ws/document/{document_id}")
async def document_collaboration(
    websocket: WebSocket,
    document_id: str,
    token: str = Header(None)
):
    """WebSocket endpoint for real-time document collaboration."""
    # Verify JWT token
    auth_result = web3_auth.verify_token(token)
    if not auth_result["success"]:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    user_id = auth_result["address"]

    try:
        # Join collaboration session
        join_result = await collaboration_manager.join_session(
            document_id,
            user_id,
            websocket
        )
        
        if not join_result["success"]:
            await websocket.close(code=4002, reason=join_result["error"])
            return

        # Handle WebSocket messages
        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data["type"] == "cursor_update":
                    await collaboration_manager.update_cursor(
                        document_id,
                        user_id,
                        data["position"]
                    )
                elif data["type"] == "comment":
                    await collaboration_manager.add_comment(
                        document_id,
                        user_id,
                        data["comment"]
                    )
                elif data["type"] == "acquire_lock":
                    success = await collaboration_manager.acquire_lock(
                        document_id,
                        user_id
                    )
                    await websocket.send_text(json.dumps({
                        "type": "lock_response",
                        "success": success
                    }))
                elif data["type"] == "release_lock":
                    success = await collaboration_manager.release_lock(
                        document_id,
                        user_id
                    )
                    await websocket.send_text(json.dumps({
                        "type": "lock_response",
                        "success": success
                    }))
                
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
            
    finally:
        await collaboration_manager.leave_session(document_id, user_id)
        await websocket.close()
