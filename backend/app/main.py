from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
import asyncio
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.socket_manager import manager
from app.core.redis_manager import redis_manager
from app.core.ai_service import ai_service
from app.api.endpoints import document

app = FastAPI(title=settings.PROJECT_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add document analysis routes
app.include_router(document.router, prefix="/api/documents", tags=["documents"])

@app.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Store message in Redis
            redis_manager.add_to_chat_history(client_id, message)
            
            # Generate AI response
            if not message.get("is_typing", False):
                # Send typing indicator
                await manager.update_typing_status(client_id, True)
                
                try:
                    ai_response = await ai_service.generate_response(
                        message["content"],
                        client_id
                    )
                    
                    response_message = {
                        "id": str(datetime.now().timestamp()),
                        "content": ai_response,
                        "timestamp": datetime.now().isoformat(),
                        "is_user": False,
                        "username": "AI Assistant"
                    }
                    
                    # Store AI response in Redis
                    redis_manager.add_to_chat_history(client_id, response_message)
                    
                    # Send response back to client
                    await manager.send_personal_message(response_message, client_id)
                except Exception as e:
                    error_message = {
                        "error": str(e),
                        "type": "error"
                    }
                    await manager.send_personal_message(error_message, client_id)
                finally:
                    await manager.update_typing_status(client_id, False)
            
            # Broadcast message to other clients if needed
            # await manager.broadcast(message)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast({
            "type": "system",
            "content": f"Client #{client_id} left the chat"
        })

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not any(file.filename.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
            return JSONResponse(
                status_code=400,
                content={"error": f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"}
            )
        
        # Validate file size
        file_size = 0
        content = b""
        
        while chunk := await file.read(8192):
            content += chunk
            file_size += len(chunk)
            
            if file_size > settings.MAX_UPLOAD_SIZE:
                return JSONResponse(
                    status_code=400,
                    content={"error": "File too large"}
                )
        
        # Save file
        file_path = f"{settings.UPLOAD_DIR}/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {"filename": file.filename, "size": file_size}
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis_connected": redis_manager.redis_client.ping()
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
