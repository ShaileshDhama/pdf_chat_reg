from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from ...core.document_service import DocumentService
from ...schemas import DocumentAnalysis

router = APIRouter()
document_service = DocumentService()

@router.post("/analyze", response_model=DocumentAnalysis)
async def analyze_document(
    file: UploadFile = File(...),
    extract_clauses: bool = True,
    analyze_risks: bool = True
):
    """
    Analyze a document and return comprehensive analysis results.
    """
    try:
        # Process document
        result = await document_service.process_document(file)
        
        # Extract clauses if requested
        if extract_clauses:
            file_path = await document_service._save_upload(file)
            clauses = await document_service.extract_clauses(file_path)
            
            # Analyze clauses if requested
            if analyze_risks:
                clause_analysis = await document_service.analyze_clauses(clauses)
                result.analysis["clause_analysis"] = clause_analysis
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_documents(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...)
):
    """
    Compare two documents and identify similarities and differences.
    """
    try:
        # Save uploaded files
        file1_path = await document_service._save_upload(file1)
        file2_path = await document_service._save_upload(file2)
        
        # Compare documents
        comparison = await document_service.compare_documents(file1_path, file2_path)
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-clauses")
async def extract_document_clauses(
    file: UploadFile = File(...),
    clause_types: Optional[List[str]] = None
):
    """
    Extract specific types of clauses from a document.
    """
    try:
        # Save uploaded file
        file_path = await document_service._save_upload(file)
        
        # Extract clauses
        clauses = await document_service.extract_clauses(file_path, clause_types)
        
        # Analyze clauses
        analysis = await document_service.analyze_clauses(clauses)
        
        return {
            "clauses": clauses,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
