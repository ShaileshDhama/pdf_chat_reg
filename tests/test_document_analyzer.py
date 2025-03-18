import pytest
from pathlib import Path
from backend.app.ai.document_analyzer import DocumentAnalyzer
from backend.app.schemas import DocumentAnalysisRequest

def test_document_analyzer_initialization():
    """Test DocumentAnalyzer initialization"""
    analyzer = DocumentAnalyzer()
    assert analyzer is not None
    assert analyzer.embeddings is not None
    assert analyzer.summarizer is not None
    assert analyzer.ner is not None

def test_process_document(document_analyzer, sample_pdf):
    """Test document processing"""
    result = document_analyzer.process_document(str(sample_pdf))
    assert result["success"] is True
    assert "analysis" in result
    assert "summary" in result["analysis"]
    assert "keyPhrases" in result["analysis"]
    assert "entities" in result["analysis"]

def test_invalid_file_type(document_analyzer, test_data_dir):
    """Test processing invalid file type"""
    invalid_file = test_data_dir / "invalid.xyz"
    invalid_file.touch()
    
    with pytest.raises(ValueError) as exc_info:
        document_analyzer.process_document(str(invalid_file))
    assert "Unsupported file format" in str(exc_info.value)

def test_empty_file(document_analyzer, test_data_dir):
    """Test processing empty file"""
    empty_file = test_data_dir / "empty.pdf"
    empty_file.touch()
    
    result = document_analyzer.process_document(str(empty_file))
    assert result["success"] is False
    assert "error" in result

def test_extract_key_phrases(document_analyzer, sample_pdf):
    """Test key phrase extraction"""
    result = document_analyzer.process_document(str(sample_pdf))
    assert result["success"] is True
    assert len(result["analysis"]["keyPhrases"]) > 0

def test_extract_entities(document_analyzer, sample_pdf):
    """Test entity extraction"""
    result = document_analyzer.process_document(str(sample_pdf))
    assert result["success"] is True
    assert len(result["analysis"]["entities"]) > 0

def test_calculate_metrics(document_analyzer, sample_pdf):
    """Test metrics calculation"""
    result = document_analyzer.process_document(str(sample_pdf))
    assert result["success"] is True
    metrics = result["analysis"]["readability"]
    assert "total_words" in metrics
    assert "avg_word_length" in metrics
    assert "flesch_reading_ease" in metrics

def test_input_validation():
    """Test input validation using schemas"""
    with pytest.raises(ValueError):
        DocumentAnalysisRequest(
            file_path=Path("nonexistent.pdf"),
            analysis_type="invalid_type",
            language="invalid_lang"
        )

def test_large_file_handling(document_analyzer, test_data_dir):
    """Test handling of large files"""
    large_file = test_data_dir / "large.pdf"
    with open(large_file, "wb") as f:
        f.write(b"0" * (10 * 1024 * 1024))  # 10MB file
    
    with pytest.raises(ValueError) as exc_info:
        document_analyzer.process_document(str(large_file))
    assert "File too large" in str(exc_info.value)

def test_concurrent_processing(document_analyzer, sample_pdf):
    """Test concurrent document processing"""
    import concurrent.futures
    
    def process_doc():
        return document_analyzer.process_document(str(sample_pdf))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_doc) for _ in range(3)]
        results = [f.result() for f in futures]
    
    assert all(r["success"] for r in results)
