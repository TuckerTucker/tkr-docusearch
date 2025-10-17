"""
Pytest configuration and shared fixtures for tkr-docusearch test suite.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure src is in path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# ============================================================================
# Session-level Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """Project root directory path."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def test_data_dir(project_root_path: Path) -> Path:
    """Test data directory path."""
    data_dir = project_root_path / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def temp_output_dir(tmp_path_factory) -> Path:
    """Temporary output directory for test artifacts."""
    return tmp_path_factory.mktemp("test_output")


# ============================================================================
# Test Environment Configuration
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Configure test environment variables."""
    # Set test mode
    os.environ["TESTING"] = "1"

    # Disable GPU for most tests (override in specific tests if needed)
    if "DEVICE" not in os.environ:
        os.environ["DEVICE"] = "cpu"

    # Set minimal batch sizes for faster testing
    os.environ.setdefault("BATCH_SIZE_VISUAL", "1")
    os.environ.setdefault("BATCH_SIZE_TEXT", "2")

    # Disable progress bars during tests
    os.environ["TQDM_DISABLE"] = "1"

    yield

    # Cleanup
    os.environ.pop("TESTING", None)
    os.environ.pop("TQDM_DISABLE", None)


# ============================================================================
# Mock Embedding Fixtures
# ============================================================================


@pytest.fixture
def mock_embedding_128d() -> np.ndarray:
    """Single 128-dimensional embedding vector."""
    np.random.seed(42)
    return np.random.randn(128).astype(np.float32)


@pytest.fixture
def mock_embedding_sequence() -> np.ndarray:
    """Multi-vector embedding sequence (seq_length, 128)."""
    np.random.seed(42)
    return np.random.randn(30, 128).astype(np.float32)


@pytest.fixture
def mock_image_embedding() -> np.ndarray:
    """Image embedding sequence (1031 tokens × 128 dim)."""
    np.random.seed(42)
    return np.random.randn(1031, 128).astype(np.float32)


@pytest.fixture
def mock_text_embedding() -> np.ndarray:
    """Text embedding sequence (30 tokens × 128 dim)."""
    np.random.seed(42)
    return np.random.randn(30, 128).astype(np.float32)


@pytest.fixture
def mock_query_embedding() -> np.ndarray:
    """Query embedding sequence (22 tokens × 128 dim)."""
    np.random.seed(42)
    return np.random.randn(22, 128).astype(np.float32)


# ============================================================================
# Mock Document Fixtures
# ============================================================================


@pytest.fixture
def sample_pdf_path(test_data_dir: Path) -> Path:
    """Path to a sample PDF file (may not exist, for path testing)."""
    return test_data_dir / "sample.pdf"


@pytest.fixture
def sample_image_path(test_data_dir: Path) -> Path:
    """Path to a sample image file (may not exist, for path testing)."""
    return test_data_dir / "sample.png"


@pytest.fixture
def sample_text_content() -> str:
    """Sample text content for testing."""
    return """
    This is a sample document for testing.
    It contains multiple lines of text.
    Used for text processing and embedding tests.
    """


# ============================================================================
# ChromaDB Fixtures
# ============================================================================


@pytest.fixture
def chromadb_available() -> bool:
    """Check if ChromaDB is available for testing."""
    try:
        import chromadb
        from chromadb.config import Settings

        # Try to create an ephemeral client
        client = chromadb.Client(Settings(is_persistent=False, anonymized_telemetry=False))
        return True
    except Exception:
        return False


@pytest.fixture
def skip_if_no_chromadb(chromadb_available: bool):
    """Skip test if ChromaDB is not available."""
    if not chromadb_available:
        pytest.skip("ChromaDB not available")


# ============================================================================
# GPU/MPS Fixtures
# ============================================================================


@pytest.fixture
def mps_available() -> bool:
    """Check if MPS (Metal Performance Shaders) is available."""
    try:
        import torch

        return torch.backends.mps.is_available() and torch.backends.mps.is_built()
    except Exception:
        return False


@pytest.fixture
def skip_if_no_mps(mps_available: bool):
    """Skip test if MPS is not available."""
    if not mps_available:
        pytest.skip("MPS not available")


# ============================================================================
# Test Isolation
# ============================================================================


@pytest.fixture(autouse=True)
def reset_random_seeds():
    """Reset random seeds before each test for reproducibility."""
    np.random.seed(42)
    try:
        import torch

        torch.manual_seed(42)
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch):
    """Isolate each test's environment variables."""
    # This fixture runs before each test and provides a clean environment
    yield


# ============================================================================
# Pytest Hooks
# ============================================================================


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    for item in items:
        # Add markers based on test path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_real_chromadb" in str(item.fspath):
            item.add_marker(pytest.mark.requires_chromadb)
        elif "embeddings" in str(item.fspath) and "mps" in item.name.lower():
            item.add_marker(pytest.mark.requires_gpu)


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_gpu: Tests requiring GPU/MPS")
    config.addinivalue_line("markers", "requires_chromadb: Tests requiring ChromaDB connection")


def pytest_report_header(config):
    """Add custom header to pytest report."""
    import sys

    header = [
        f"Python: {sys.version.split()[0]}",
        f"Platform: {sys.platform}",
    ]

    # Add PyTorch info if available
    try:
        import torch

        header.append(f"PyTorch: {torch.__version__}")
        if torch.backends.mps.is_available():
            header.append("MPS: Available")
    except ImportError:
        pass

    # Add ChromaDB info if available
    try:
        import chromadb

        header.append(f"ChromaDB: {chromadb.__version__}")
    except ImportError:
        pass

    return header
