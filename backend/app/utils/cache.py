from functools import lru_cache
from typing import Dict, Any, Optional
import hashlib
import json
import time
from pathlib import Path
from backend.app.config import settings
from backend.app.utils.logger import logger

class Cache:
    """Simple file-based cache with TTL"""
    
    def __init__(self, cache_dir: Path = settings.TEMP_DIR / "cache"):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, key: str) -> str:
        """Generate a cache key"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get path for cache file"""
        return self.cache_dir / f"{self._get_cache_key(key)}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        try:
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                return None
            
            with cache_path.open("r") as f:
                cached_data = json.load(f)
            
            # Check TTL
            if time.time() - cached_data["timestamp"] > settings.CACHE_TTL:
                cache_path.unlink()
                return None
            
            logger.debug("cache_hit", key=key)
            return cached_data["value"]
            
        except Exception as e:
            logger.error("cache_error", error=str(e), key=key)
            return None
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set value in cache"""
        try:
            cache_path = self._get_cache_path(key)
            
            cached_data = {
                "timestamp": time.time(),
                "value": value
            }
            
            with cache_path.open("w") as f:
                json.dump(cached_data, f)
            
            logger.debug("cache_set", key=key)
            
        except Exception as e:
            logger.error("cache_error", error=str(e), key=key)
    
    def delete(self, key: str) -> None:
        """Delete value from cache"""
        try:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
                logger.debug("cache_delete", key=key)
                
        except Exception as e:
            logger.error("cache_error", error=str(e), key=key)
    
    def clear(self) -> None:
        """Clear all cached values"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("cache_cleared")
            
        except Exception as e:
            logger.error("cache_error", error=str(e))

# Document analysis cache decorator
@lru_cache(maxsize=settings.MAX_CACHE_SIZE)
def cache_document_analysis(file_hash: str) -> Dict[str, Any]:
    """Cache for document analysis results"""
    pass

# Create cache instance
cache = Cache()
