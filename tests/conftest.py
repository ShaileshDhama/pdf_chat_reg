import pytest
from pathlib import Path
from backend.app.ai.document_analyzer import DocumentAnalyzer
from backend.app.utils.cache import Cache
from backend.app.config import settings

@pytest.fixture
def test_data_dir() -> Path:
    """Fixture for test data directory"""
    data_dir = Path(__file__).parent / "test_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

@pytest.fixture
def sample_pdf(test_data_dir: Path) -> Path:
    """Fixture for sample PDF file"""
    pdf_path = test_data_dir / "sample.pdf"
    if not pdf_path.exists():
        # Create a simple PDF for testing
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 750, "Test Document")
        c.drawString(100, 700, "This is a sample document for testing.")
        c.save()
    return pdf_path

@pytest.fixture
def document_analyzer() -> DocumentAnalyzer:
    """Fixture for DocumentAnalyzer instance"""
    return DocumentAnalyzer()

@pytest.fixture
def cache() -> Cache:
    """Fixture for Cache instance"""
    return Cache(cache_dir=Path("tests/test_cache"))

@pytest.fixture(autouse=True)
def cleanup_temp_files(request):
    """Cleanup temporary files after tests"""
    def cleanup():
        import shutil
        temp_dirs = [
            Path("tests/test_cache"),
            Path("tests/test_data"),
            settings.TEMP_DIR,
            settings.UPLOAD_DIR
        ]
        for dir_path in temp_dirs:
            if dir_path.exists():
                shutil.rmtree(dir_path)
    
    request.addfinalizer(cleanup)
