from redis import Redis
from typing import Optional, Any
import json
from app.core.config import settings

class RedisManager:
    def __init__(self):
        self.redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    def set_chat_context(self, user_id: str, context: dict, expire: int = 3600):
        """Store chat context in Redis with expiration"""
        key = f"chat:context:{user_id}"
        self.redis_client.setex(key, expire, json.dumps(context))

    def get_chat_context(self, user_id: str) -> Optional[dict]:
        """Retrieve chat context from Redis"""
        key = f"chat:context:{user_id}"
        context = self.redis_client.get(key)
        return json.loads(context) if context else None

    def add_to_chat_history(self, user_id: str, message: dict):
        """Add message to user's chat history"""
        key = f"chat:history:{user_id}"
        self.redis_client.lpush(key, json.dumps(message))
        self.redis_client.ltrim(key, 0, 49)  # Keep last 50 messages

    def get_chat_history(self, user_id: str, limit: int = 50) -> list:
        """Get user's chat history"""
        key = f"chat:history:{user_id}"
        history = self.redis_client.lrange(key, 0, limit - 1)
        return [json.loads(msg) for msg in history]

    def set_typing_status(self, user_id: str, is_typing: bool):
        """Set user's typing status"""
        key = f"chat:typing:{user_id}"
        self.redis_client.setex(key, 10, str(int(is_typing)))

    def get_typing_status(self, user_id: str) -> bool:
        """Get user's typing status"""
        key = f"chat:typing:{user_id}"
        status = self.redis_client.get(key)
        return bool(int(status)) if status else False

redis_manager = RedisManager()
