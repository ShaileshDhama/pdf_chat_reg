from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class FileInfo(BaseModel):
    name: str
    size: int
    type: str
    created_at: str
    modified_at: str

class Metadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int

class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int

class Section(BaseModel):
    type: str
    heading: str
    content: str

class ContentInfo(BaseModel):
    text: str
    summary: Optional[str] = None
    language: str
    structure: List[Section]

class AnalysisResult(BaseModel):
    entities: List[Entity]
    topics: List[str]
    key_phrases: List[str]
    sentiment: Dict[str, Any]
    readability: float

class TableInfo(BaseModel):
    rows: int
    cols: int
    cells: List[List[Dict[str, Any]]]

class ImageInfo(BaseModel):
    bbox: List[float]
    size: int
    width: int
    height: int
    ocr_text: Optional[str] = None
    format: str

class Elements(BaseModel):
    tables: List[TableInfo]
    images: List[ImageInfo]

class ComplianceInfo(BaseModel):
    compliant: bool
    warnings: List[str]
    violations: List[str]

class RiskFactor(BaseModel):
    severity: str
    text: str
    context: str

class DocumentAnalysis(BaseModel):
    file_info: FileInfo
    metadata: Metadata
    content: ContentInfo
    analysis: AnalysisResult
    elements: Elements
    compliance: ComplianceInfo
    risks: List[RiskFactor]

class ClauseAnalysis(BaseModel):
    type: str
    text: str
    context: str
    section: str
    position: Dict[str, int]

class ClauseRisk(BaseModel):
    clause_type: str
    severity: str
    text: str
    reason: str

class ClauseRecommendation(BaseModel):
    clause_type: str
    severity: str
    recommendation: str

class ClauseAnalysisResult(BaseModel):
    by_type: Dict[str, List[ClauseAnalysis]]
    risk_assessment: List[ClauseRisk]
    recommendations: List[ClauseRecommendation]

class DocumentComparison(BaseModel):
    similarity_score: float
    common_entities: Dict[str, List[str]]
    structural_differences: Dict[str, Any]
    risk_comparison: Dict[str, List[str]]
