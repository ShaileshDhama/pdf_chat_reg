from pydantic_settings import BaseSettings
from typing import Set, Dict, Any
from pathlib import Path

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "LEGALe TROY"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # Security Settings
    MAX_UPLOAD_SIZE: int = 10_000_000  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {"pdf", "doc", "docx", "txt"}
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour
    
    # File Storage
    UPLOAD_DIR: Path = Path("uploads")
    TEMP_DIR: Path = Path("temp")
    
    # AI Model Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"
    NER_MODEL: str = "en_core_web_sm"
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    MAX_CACHE_SIZE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Feature Flags
    ENABLE_OCR: bool = True
    ENABLE_ADVANCED_ANALYTICS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields

    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI-related configuration"""
        return {
            "embedding_model": self.EMBEDDING_MODEL,
            "summarization_model": self.SUMMARIZATION_MODEL,
            "ner_model": self.NER_MODEL,
            "enable_ocr": self.ENABLE_OCR,
            "enable_advanced_analytics": self.ENABLE_ADVANCED_ANALYTICS
        }

settings = Settings()
