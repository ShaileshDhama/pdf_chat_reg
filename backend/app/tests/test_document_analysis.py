import os
import pytest
import asyncio
from fastapi import UploadFile
from pathlib import Path
from ..core.document_service import DocumentService
from ..core.document_parser import DocumentParser

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"

@pytest.fixture(scope="module")
def test_files():
    """Create test PDF files with known content."""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    # Create test files
    files = {
        "simple": TEST_DATA_DIR / "simple.pdf",
        "complex": TEST_DATA_DIR / "complex.pdf",
        "contract": TEST_DATA_DIR / "contract.pdf"
    }
    
    # Generate test PDFs using reportlab
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    def create_simple_pdf():
        c = canvas.Canvas(str(files["simple"]), pagesize=letter)
        c.drawString(100, 750, "This is a simple test document.")
        c.drawString(100, 700, "It contains basic text for testing.")
        c.save()
    
    def create_complex_pdf():
        c = canvas.Canvas(str(files["complex"]), pagesize=letter)
        c.drawString(100, 750, "Complex Document")
        c.drawString(100, 700, "This document contains multiple sections:")
        c.drawString(120, 670, "1. Introduction")
        c.drawString(120, 650, "2. Analysis")
        c.drawString(120, 630, "3. Conclusion")
        c.drawString(100, 600, "It also includes some entities like:")
        c.drawString(120, 580, "- John Smith (Person)")
        c.drawString(120, 560, "- Microsoft Corporation (Organization)")
        c.drawString(120, 540, "- January 15, 2025 (Date)")
        c.save()
    
    def create_contract_pdf():
        c = canvas.Canvas(str(files["contract"]), pagesize=letter)
        c.drawString(100, 750, "LEGAL CONTRACT")
        c.drawString(100, 700, "1. Definitions")
        c.drawString(120, 680, "'Company' shall mean XYZ Corp.")
        c.drawString(100, 650, "2. Obligations")
        c.drawString(120, 630, "The Company shall provide services.")
        c.drawString(100, 600, "3. Confidentiality")
        c.drawString(120, 580, "All information shall be kept confidential.")
        c.drawString(100, 550, "4. Termination")
        c.drawString(120, 530, "This agreement may be terminated with 30 days notice.")
        c.save()
    
    # Create the test files
    create_simple_pdf()
    create_complex_pdf()
    create_contract_pdf()
    
    yield files
    
    # Cleanup test files
    for file in files.values():
        if file.exists():
            file.unlink()
    if TEST_DATA_DIR.exists():
        TEST_DATA_DIR.rmdir()

@pytest.fixture
def document_service():
    return DocumentService()

@pytest.mark.asyncio
async def test_simple_document_analysis(document_service, test_files):
    """Test basic document analysis functionality."""
    # Create UploadFile from test file
    class MockUploadFile(UploadFile):
        async def read(self):
            return open(test_files["simple"], "rb").read()
    
    file = MockUploadFile(filename="simple.pdf")
    result = await document_service.process_document(file)
    
    assert result is not None
    assert "content" in result.dict()
    assert "This is a simple test document" in result.dict()["content"]["text"]
    assert result.dict()["metadata"]["page_count"] == 1

@pytest.mark.asyncio
async def test_complex_document_analysis(document_service, test_files):
    """Test analysis of a more complex document."""
    class MockUploadFile(UploadFile):
        async def read(self):
            return open(test_files["complex"], "rb").read()
    
    file = MockUploadFile(filename="complex.pdf")
    result = await document_service.process_document(file)
    
    analysis = result.dict()
    
    # Check structure detection
    assert len(analysis["content"]["structure"]) >= 3  # Should detect at least 3 sections
    
    # Check entity extraction
    entities = analysis["analysis"]["entities"]
    assert any(e["text"] == "John Smith" and e["label"] == "PERSON" for e in entities)
    assert any(e["text"] == "Microsoft Corporation" and e["label"] == "ORG" for e in entities)

@pytest.mark.asyncio
async def test_contract_analysis(document_service, test_files):
    """Test legal document analysis features."""
    class MockUploadFile(UploadFile):
        async def read(self):
            return open(test_files["contract"], "rb").read()
    
    file = MockUploadFile(filename="contract.pdf")
    result = await document_service.process_document(file)
    
    # Extract clauses
    clauses = await document_service.extract_clauses(str(test_files["contract"]))
    
    # Analyze clauses
    clause_analysis = await document_service.analyze_clauses(clauses)
    
    # Verify clause extraction
    assert any(c["type"] == "definition" for c in clauses)
    assert any(c["type"] == "obligation" for c in clauses)
    assert any(c["type"] == "confidentiality" for c in clauses)
    assert any(c["type"] == "termination" for c in clauses)
    
    # Verify clause analysis
    assert "by_type" in clause_analysis
    assert "risk_assessment" in clause_analysis
    assert "recommendations" in clause_analysis

@pytest.mark.asyncio
async def test_document_comparison(document_service, test_files):
    """Test document comparison functionality."""
    comparison = await document_service.compare_documents(
        str(test_files["contract"]),
        str(test_files["complex"])
    )
    
    assert "similarity_score" in comparison
    assert "common_entities" in comparison
    assert "structural_differences" in comparison
    assert "risk_comparison" in comparison
    
    # Similarity score should be between 0 and 1
    assert 0 <= comparison["similarity_score"] <= 1

@pytest.mark.asyncio
async def test_cached_analysis(document_service, test_files):
    """Test that document analysis results are properly cached."""
    class MockUploadFile(UploadFile):
        async def read(self):
            return open(test_files["simple"], "rb").read()
    
    file = MockUploadFile(filename="simple.pdf")
    
    # First analysis
    start_time = asyncio.get_event_loop().time()
    result1 = await document_service.process_document(file)
    first_duration = asyncio.get_event_loop().time() - start_time
    
    # Second analysis (should use cache)
    start_time = asyncio.get_event_loop().time()
    result2 = await document_service.process_document(file)
    second_duration = asyncio.get_event_loop().time() - start_time
    
    # Cached analysis should be faster
    assert second_duration < first_duration
    
    # Results should be identical
    assert result1.dict() == result2.dict()

@pytest.mark.asyncio
async def test_error_handling(document_service):
    """Test error handling for invalid documents."""
    class MockUploadFile(UploadFile):
        async def read(self):
            return b"Invalid PDF content"
    
    file = MockUploadFile(filename="invalid.pdf")
    
    with pytest.raises(Exception) as exc_info:
        await document_service.process_document(file)
    
    assert "Error processing document" in str(exc_info.value)

def test_supported_file_types(document_service, test_files):
    """Test handling of different file types."""
    supported_extensions = [".pdf", ".docx", ".txt"]
    
    for ext in supported_extensions:
        test_file = TEST_DATA_DIR / f"test{ext}"
        with open(test_file, "wb") as f:
            f.write(b"Test content")
        
        assert document_service._is_supported_file(str(test_file))
        
        os.unlink(test_file)

@pytest.mark.asyncio
async def test_large_document_handling(document_service):
    """Test handling of large documents."""
    # Create a large test PDF
    large_file = TEST_DATA_DIR / "large.pdf"
    c = canvas.Canvas(str(large_file), pagesize=letter)
    
    # Add many pages with content
    for i in range(50):  # 50 pages
        c.drawString(100, 750, f"Page {i+1}")
        c.drawString(100, 700, "Lorem ipsum " * 100)  # Lots of text
        c.showPage()
    c.save()
    
    class MockUploadFile(UploadFile):
        async def read(self):
            return open(large_file, "rb").read()
    
    file = MockUploadFile(filename="large.pdf")
    result = await document_service.process_document(file)
    
    assert result is not None
    assert result.dict()["metadata"]["page_count"] == 50
    
    os.unlink(large_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
