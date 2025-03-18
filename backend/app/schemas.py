from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from backend.app.config import settings

class DocumentAnalysisRequest(BaseModel):
    """Request model for document analysis"""
    file_path: Path = Field(..., description="Path to the document file")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    language: str = Field(default="en", description="Document language")
    
    @validator("file_path")
    def validate_file_path(cls, v):
        if not v.exists():
            raise ValueError("File does not exist")
        if not v.is_file():
            raise ValueError("Path is not a file")
        if not v.suffix[1:] in settings.ALLOWED_EXTENSIONS:
            raise ValueError("Invalid file type")
        return v
    
    @validator("analysis_type")
    def validate_analysis_type(cls, v):
        allowed_types = {"overview", "content", "entities", "legal", "metrics"}
        if v not in allowed_types:
            raise ValueError(f"Invalid analysis type. Must be one of: {allowed_types}")
        return v
    
    @validator("language")
    def validate_language(cls, v):
        allowed_languages = {"en", "es", "fr", "de"}
        if v not in allowed_languages:
            raise ValueError(f"Unsupported language. Must be one of: {allowed_languages}")
        return v

class DocumentComparisonRequest(BaseModel):
    """Request model for document comparison"""
    file_path_1: Path = Field(..., description="Path to the first document")
    file_path_2: Path = Field(..., description="Path to the second document")
    comparison_types: List[str] = Field(
        default=["content"],
        description="Types of comparison to perform"
    )
    
    @validator("comparison_types")
    def validate_comparison_types(cls, v):
        allowed_types = {"content", "structure", "style"}
        if not all(t in allowed_types for t in v):
            raise ValueError(f"Invalid comparison type. Must be from: {allowed_types}")
        return v

class DocumentAnalysis(BaseModel):
    """Model for document analysis data"""
    id: str = Field(..., description="Unique identifier for the analysis")
    filename: str = Field(..., description="Original document filename")
    file_path: Path = Field(..., description="Path to the stored document")
    file_size: int = Field(..., description="Size of the document in bytes")
    file_type: str = Field(..., description="Type/extension of the document")
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    analysis_date: Optional[datetime] = Field(None, description="When analysis was performed")
    analysis_status: str = Field(default="pending", description="Status of the analysis")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")

class AnalysisResult(BaseModel):
    """Model for document analysis results"""
    success: bool = Field(..., description="Whether the analysis was successful")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    error: Optional[str] = Field(None, description="Error message if analysis failed")

class ComparisonResult(BaseModel):
    """Model for document comparison results"""
    success: bool = Field(..., description="Whether the comparison was successful")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    similarity_score: float = Field(..., description="Overall similarity score")
    differences: Dict[str, Any] = Field(..., description="Detailed differences")
    common_elements: Dict[str, Any] = Field(..., description="Common elements")
    error: Optional[str] = Field(None, description="Error message if comparison failed")
