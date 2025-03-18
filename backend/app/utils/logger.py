import logging
import structlog
from typing import Any, Dict
import sys
from pathlib import Path
from datetime import datetime
from backend.app.config import settings

def setup_logging() -> None:
    """Configure structured logging for the application"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(message)s",
        stream=sys.stdout,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a logger instance"""
    return structlog.get_logger(name)

class LoggerMiddleware:
    """Middleware for logging HTTP requests"""
    
    def __init__(self):
        self.logger = get_logger("http")
    
    async def __call__(self, request, call_next):
        start_time = datetime.utcnow()
        
        # Log request
        self.logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            self.logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            return response
            
        except Exception as e:
            # Log error
            self.logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
            raise

class AnalyticsLogger:
    """Logger for tracking analytics events"""
    
    def __init__(self):
        self.logger = get_logger("analytics")
    
    def log_document_analysis(
        self,
        document_id: str,
        analysis_type: str,
        duration_ms: float,
        success: bool,
        metadata: Dict[str, Any]
    ) -> None:
        """Log document analysis event"""
        self.logger.info(
            "document_analyzed",
            document_id=document_id,
            analysis_type=analysis_type,
            duration_ms=duration_ms,
            success=success,
            **metadata
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Log error event"""
        self.logger.error(
            "error_occurred",
            error_type=error_type,
            error_message=error_message,
            **metadata
        )

# Initialize loggers
logger = get_logger(__name__)
analytics = AnalyticsLogger()
