from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Callable, Awaitable
import time
from collections import defaultdict
from backend.app.config import settings
from backend.app.utils.logger import logger

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited"""
        now = time.time()
        
        # Remove old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < settings.RATE_LIMIT_PERIOD
        ]
        
        # Check rate limit
        return len(self.requests[client_ip]) >= settings.RATE_LIMIT_REQUESTS
    
    def add_request(self, client_ip: str) -> None:
        """Record a new request"""
        self.requests[client_ip].append(time.time())

class SecurityMiddleware:
    """Security middleware for request validation and protection"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[JSONResponse]]
    ) -> JSONResponse:
        client_ip = request.client.host
        
        try:
            # Rate limiting
            if self.rate_limiter.is_rate_limited(client_ip):
                logger.warning("rate_limit_exceeded", client_ip=client_ip)
                return JSONResponse(
                    status_code=429,
                    content={"error": "Too many requests"}
                )
            
            # File size validation for uploads
            if request.method == "POST":
                content_length = request.headers.get("content-length", 0)
                if int(content_length) > settings.MAX_UPLOAD_SIZE:
                    logger.warning("file_too_large", client_ip=client_ip)
                    return JSONResponse(
                        status_code=413,
                        content={"error": "File too large"}
                    )
            
            # Add security headers
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # Record request for rate limiting
            self.rate_limiter.add_request(client_ip)
            
            return response
            
        except Exception as e:
            logger.error(
                "security_middleware_error",
                client_ip=client_ip,
                error=str(e)
            )
            raise HTTPException(status_code=500, detail="Internal server error")

def validate_file_extension(filename: str) -> bool:
    """Validate file extension against allowed types"""
    return filename.lower().endswith(tuple(settings.ALLOWED_EXTENSIONS))

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    return "".join(c for c in filename if c.isalnum() or c in "._-")
