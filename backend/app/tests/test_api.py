import os
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from ..main import app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

client = TestClient(app)

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"

def setup_module():
    """Create test data directory and files."""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    # Create a test PDF
    pdf_path = TEST_DATA_DIR / "test_contract.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    
    # Add content
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

def teardown_module():
    """Clean up test data."""
    for file in TEST_DATA_DIR.glob("*"):
        file.unlink()
    TEST_DATA_DIR.rmdir()

def test_analyze_document():
    """Test document analysis endpoint."""
    pdf_path = TEST_DATA_DIR / "test_contract.pdf"
    
    with open(pdf_path, "rb") as f:
        files = {"file": ("test_contract.pdf", f, "application/pdf")}
        response = client.post("/api/documents/analyze", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    assert "file_info" in data
    assert "metadata" in data
    assert "content" in data
    assert "analysis" in data
    
    # Check content analysis
    assert "LEGAL CONTRACT" in data["content"]["text"]
    assert data["metadata"]["page_count"] == 1
    
    # Check entity extraction
    entities = data["analysis"]["entities"]
    assert any(e["text"] == "XYZ Corp" for e in entities)
    
    # Check clause extraction
    assert "clause_analysis" in data["analysis"]
    clause_types = [c["type"] for c in data["analysis"]["clause_analysis"]["by_type"]]
    assert "definition" in clause_types
    assert "obligation" in clause_types
    assert "confidentiality" in clause_types
    assert "termination" in clause_types

def test_extract_clauses():
    """Test clause extraction endpoint."""
    pdf_path = TEST_DATA_DIR / "test_contract.pdf"
    
    with open(pdf_path, "rb") as f:
        files = {"file": ("test_contract.pdf", f, "application/pdf")}
        response = client.post(
            "/api/documents/extract-clauses",
            files=files,
            params={"clause_types": ["definition", "obligation"]}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "clauses" in data
    assert "analysis" in data
    
    # Check extracted clauses
    clauses = data["clauses"]
    clause_types = [c["type"] for c in clauses]
    assert "definition" in clause_types
    assert "obligation" in clause_types
    
    # Check analysis
    analysis = data["analysis"]
    assert "risk_assessment" in analysis
    assert "recommendations" in analysis

def test_compare_documents():
    """Test document comparison endpoint."""
    # Create a second test PDF for comparison
    pdf_path2 = TEST_DATA_DIR / "test_contract2.pdf"
    c = canvas.Canvas(str(pdf_path2), pagesize=letter)
    c.drawString(100, 750, "LEGAL CONTRACT - VERSION 2")
    c.drawString(100, 700, "1. Definitions")
    c.drawString(120, 680, "'Company' shall mean ABC Corp.")
    c.drawString(100, 650, "2. Obligations")
    c.drawString(120, 630, "The Company must provide services.")
    c.save()
    
    pdf_path1 = TEST_DATA_DIR / "test_contract.pdf"
    
    with open(pdf_path1, "rb") as f1, open(pdf_path2, "rb") as f2:
        files = {
            "file1": ("test_contract.pdf", f1, "application/pdf"),
            "file2": ("test_contract2.pdf", f2, "application/pdf")
        }
        response = client.post("/api/documents/compare", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check comparison results
    assert "similarity_score" in data
    assert "common_entities" in data
    assert "structural_differences" in data
    assert "risk_comparison" in data
    
    # Similarity score should be between 0 and 1
    assert 0 <= data["similarity_score"] <= 1
    
    # Should detect some common sections
    assert len(data["structural_differences"]["matching_sections"]) > 0

def test_error_handling():
    """Test error handling for invalid files."""
    # Test with invalid file
    with open(__file__, "rb") as f:
        files = {"file": ("test.py", f, "text/plain")}
        response = client.post("/api/documents/analyze", files=files)
    
    assert response.status_code == 500
    assert "error" in response.json()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
