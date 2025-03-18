import asyncio
from typing import Dict, List, Any, Optional
from fastapi import WebSocket
import json
from datetime import datetime
import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription
from backend.app.utils.logger import logger

class CollaborationManager:
    """Manages real-time collaboration features"""
    
    def __init__(self):
        self.active_sessions: Dict[str, List[WebSocket]] = {}
        self.document_states: Dict[str, Dict[str, Any]] = {}
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.sio = socketio.AsyncServer(async_mode='asgi')
    
    async def connect_client(self, websocket: WebSocket, session_id: str):
        """Connect a new client to a collaboration session"""
        try:
            await websocket.accept()
            
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = []
                self.document_states[session_id] = {
                    "content": "",
                    "annotations": [],
                    "cursors": {},
                    "chat_history": []
                }
            
            self.active_sessions[session_id].append(websocket)
            
            # Notify other clients
            await self.broadcast_message(
                session_id,
                "user_joined",
                {"timestamp": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            logger.error("client_connection_failed", error=str(e))
            raise
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming collaboration messages"""
        try:
            session_id = message.get("session_id")
            action = message.get("action")
            data = message.get("data", {})
            
            if action == "update_content":
                await self._handle_content_update(session_id, data)
            elif action == "add_annotation":
                await self._handle_annotation(session_id, data)
            elif action == "cursor_move":
                await self._handle_cursor_move(session_id, websocket, data)
            elif action == "chat_message":
                await self._handle_chat_message(session_id, data)
            elif action == "video_offer":
                await self._handle_video_offer(session_id, websocket, data)
            
        except Exception as e:
            logger.error("message_handling_failed", error=str(e))
            await websocket.send_json({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_content_update(self, session_id: str, data: Dict[str, Any]):
        """Handle document content updates"""
        self.document_states[session_id]["content"] = data["content"]
        await self.broadcast_message(session_id, "content_updated", data)
    
    async def _handle_annotation(self, session_id: str, data: Dict[str, Any]):
        """Handle document annotations"""
        annotation = {
            "id": data["id"],
            "text": data["text"],
            "position": data["position"],
            "author": data["author"],
            "timestamp": datetime.utcnow().isoformat()
        }
        self.document_states[session_id]["annotations"].append(annotation)
        await self.broadcast_message(session_id, "annotation_added", annotation)
    
    async def _handle_cursor_move(
        self,
        session_id: str,
        websocket: WebSocket,
        data: Dict[str, Any]
    ):
        """Handle cursor position updates"""
        user_id = str(id(websocket))
        self.document_states[session_id]["cursors"][user_id] = {
            "position": data["position"],
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_message(
            session_id,
            "cursor_moved",
            {"user_id": user_id, **data}
        )
    
    async def _handle_chat_message(self, session_id: str, data: Dict[str, Any]):
        """Handle chat messages"""
        message = {
            "id": data["id"],
            "text": data["text"],
            "author": data["author"],
            "timestamp": datetime.utcnow().isoformat()
        }
        self.document_states[session_id]["chat_history"].append(message)
        await self.broadcast_message(session_id, "chat_message", message)
    
    async def _handle_video_offer(
        self,
        session_id: str,
        websocket: WebSocket,
        data: Dict[str, Any]
    ):
        """Handle WebRTC video chat offers"""
        try:
            peer_connection = RTCPeerConnection()
            self.peer_connections[str(id(websocket))] = peer_connection
            
            @peer_connection.on("icecandidate")
            async def on_ice_candidate(event):
                if event.candidate:
                    await websocket.send_json({
                        "type": "ice_candidate",
                        "candidate": event.candidate.sdp,
                        "sdpMid": event.candidate.sdpMid,
                        "sdpMLineIndex": event.candidate.sdpMLineIndex
                    })
            
            offer = RTCSessionDescription(
                sdp=data["sdp"],
                type=data["type"]
            )
            await peer_connection.setRemoteDescription(offer)
            
            answer = await peer_connection.createAnswer()
            await peer_connection.setLocalDescription(answer)
            
            await websocket.send_json({
                "type": "video_answer",
                "sdp": peer_connection.localDescription.sdp
            })
            
        except Exception as e:
            logger.error("video_offer_failed", error=str(e))
            raise
    
    async def broadcast_message(
        self,
        session_id: str,
        action: str,
        data: Dict[str, Any]
    ):
        """Broadcast message to all clients in a session"""
        if session_id in self.active_sessions:
            message = {
                "action": action,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for websocket in self.active_sessions[session_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(
                        "broadcast_failed",
                        client=str(id(websocket)),
                        error=str(e)
                    )
    
    async def disconnect_client(self, websocket: WebSocket, session_id: str):
        """Handle client disconnection"""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].remove(websocket)
                
                # Cleanup WebRTC if exists
                client_id = str(id(websocket))
                if client_id in self.peer_connections:
                    await self.peer_connections[client_id].close()
                    del self.peer_connections[client_id]
                
                # Remove cursor position
                if client_id in self.document_states[session_id]["cursors"]:
                    del self.document_states[session_id]["cursors"][client_id]
                
                # Notify other clients
                await self.broadcast_message(
                    session_id,
                    "user_left",
                    {"user_id": client_id}
                )
                
        except Exception as e:
            logger.error("disconnect_failed", error=str(e))
            raise

collaboration_manager = CollaborationManager()
