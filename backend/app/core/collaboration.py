from typing import Dict, List, Optional
from fastapi import WebSocket
from datetime import datetime
import json
import asyncio
from pydantic import BaseModel

class CollaborationSession(BaseModel):
    document_id: str
    participants: List[str]
    cursors: Dict[str, Dict[str, int]]  # user_id -> {line, column}
    comments: List[Dict]
    created_at: datetime
    last_activity: datetime

class CollaborationManager:
    def __init__(self):
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.connections: Dict[str, Dict[str, WebSocket]] = {}  # document_id -> {user_id: websocket}
        self.document_locks: Dict[str, str] = {}  # document_id -> user_id

    async def create_session(self, document_id: str, creator_id: str) -> CollaborationSession:
        """Create a new collaboration session for a document."""
        if document_id in self.active_sessions:
            return self.active_sessions[document_id]

        session = CollaborationSession(
            document_id=document_id,
            participants=[creator_id],
            cursors={},
            comments=[],
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.active_sessions[document_id] = session
        self.connections[document_id] = {}
        
        return session

    async def join_session(self, document_id: str, user_id: str, websocket: WebSocket) -> Dict:
        """Add a user to a collaboration session."""
        if document_id not in self.active_sessions:
            return {
                "success": False,
                "error": "Session not found"
            }

        session = self.active_sessions[document_id]
        
        if user_id not in session.participants:
            session.participants.append(user_id)
        
        self.connections[document_id][user_id] = websocket
        
        # Notify other participants
        await self.broadcast_message(document_id, {
            "type": "user_joined",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_user=None)
        
        return {
            "success": True,
            "session": session.dict()
        }

    async def leave_session(self, document_id: str, user_id: str):
        """Remove a user from a collaboration session."""
        if document_id in self.active_sessions:
            session = self.active_sessions[document_id]
            
            if user_id in session.participants:
                session.participants.remove(user_id)
                
            if document_id in self.connections and user_id in self.connections[document_id]:
                del self.connections[document_id][user_id]
                
            # Release lock if user had it
            if document_id in self.document_locks and self.document_locks[document_id] == user_id:
                del self.document_locks[document_id]
            
            # Remove session if no participants left
            if not session.participants:
                del self.active_sessions[document_id]
                del self.connections[document_id]
            else:
                # Notify other participants
                await self.broadcast_message(document_id, {
                    "type": "user_left",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude_user=user_id)

    async def update_cursor(self, document_id: str, user_id: str, position: Dict[str, int]):
        """Update a user's cursor position."""
        if document_id in self.active_sessions:
            session = self.active_sessions[document_id]
            session.cursors[user_id] = position
            
            # Broadcast cursor update to other participants
            await self.broadcast_message(document_id, {
                "type": "cursor_update",
                "user_id": user_id,
                "position": position,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude_user=user_id)

    async def add_comment(self, document_id: str, user_id: str, comment: Dict) -> Dict:
        """Add a comment to the document."""
        if document_id not in self.active_sessions:
            return {
                "success": False,
                "error": "Session not found"
            }

        session = self.active_sessions[document_id]
        
        comment_data = {
            "id": len(session.comments) + 1,
            "user_id": user_id,
            "content": comment["content"],
            "position": comment.get("position", {}),
            "created_at": datetime.utcnow().isoformat(),
            "replies": []
        }
        
        session.comments.append(comment_data)
        
        # Broadcast comment to all participants
        await self.broadcast_message(document_id, {
            "type": "new_comment",
            "comment": comment_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "comment": comment_data
        }

    async def acquire_lock(self, document_id: str, user_id: str) -> bool:
        """Attempt to acquire document lock for editing."""
        if document_id not in self.document_locks:
            self.document_locks[document_id] = user_id
            
            # Notify participants about lock
            await self.broadcast_message(document_id, {
                "type": "document_locked",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
        return False

    async def release_lock(self, document_id: str, user_id: str) -> bool:
        """Release document lock."""
        if document_id in self.document_locks and self.document_locks[document_id] == user_id:
            del self.document_locks[document_id]
            
            # Notify participants about lock release
            await self.broadcast_message(document_id, {
                "type": "document_unlocked",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
        return False

    async def broadcast_message(self, document_id: str, message: Dict, exclude_user: Optional[str] = None):
        """Broadcast a message to all participants in a session."""
        if document_id in self.connections:
            for user_id, websocket in self.connections[document_id].items():
                if exclude_user is None or user_id != exclude_user:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        print(f"Error broadcasting to user {user_id}: {str(e)}")
                        await self.leave_session(document_id, user_id)

    def get_session_info(self, document_id: str) -> Optional[Dict]:
        """Get information about a collaboration session."""
        if document_id in self.active_sessions:
            session = self.active_sessions[document_id]
            return {
                "document_id": session.document_id,
                "participants": session.participants,
                "cursors": session.cursors,
                "comments": session.comments,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "locked_by": self.document_locks.get(document_id)
            }
        return None
