"""Pytest configuration and shared fixtures for tkr-docusearch test suite."""

import os
import sys
import types
from pathlib import Path

# ---------------------------------------------------------------------------
# Stub unavailable modules so transitive imports don't fail.
# These must be installed before any tkr_docusearch imports.
# ---------------------------------------------------------------------------

# mcp SDK is not installed in test environment
if "mcp" not in sys.modules:
    _mcp_stub = types.ModuleType("mcp")
    sys.modules["mcp"] = _mcp_stub
    for _sub in (
        "mcp.server",
        "mcp.server.stdio",
        "mcp.server.fastmcp",
        "mcp.types",
    ):
        _s = types.ModuleType(_sub)
        if _sub == "mcp.server":
            def _decorator(self):
                """Return a decorator that registers a handler."""
                def wrapper(fn):
                    return fn
                return wrapper
            _s.Server = type("Server", (), {  # type: ignore[attr-defined]
                "__init__": lambda self, *a, **kw: None,
                "list_tools": _decorator,
                "call_tool": _decorator,
                "run": lambda self, *a, **kw: None,
                "create_initialization_options": lambda self: {},
            })
        elif _sub == "mcp.server.fastmcp":
            _s.FastMCP = type("FastMCP", (), {"__init__": lambda self, *a, **kw: None})  # type: ignore[attr-defined]
        elif _sub == "mcp.server.stdio":
            _s.stdio_server = lambda *a, **kw: None  # type: ignore[attr-defined]
        elif _sub == "mcp.types":
            _s.TextContent = type("TextContent", (), {  # type: ignore[attr-defined]
                "__init__": lambda self, **kw: self.__dict__.update(kw),
            })
            _s.ImageContent = type("ImageContent", (), {  # type: ignore[attr-defined]
                "__init__": lambda self, **kw: self.__dict__.update(kw),
            })
            _s.Tool = type("Tool", (), {  # type: ignore[attr-defined]
                "__init__": lambda self, **kw: self.__dict__.update(kw),
            })
        sys.modules[_sub] = _s


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
# Koji Fixtures
# ============================================================================


@pytest.fixture
def koji_config(tmp_path):
    """Create a KojiConfig pointing to a temporary database."""
    from src.config.koji_config import KojiConfig

    return KojiConfig(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def koji_client(koji_config):
    """Create and open a KojiClient with a temporary database."""
    from src.storage.koji_client import KojiClient

    client = KojiClient(koji_config)
    client.open()
    yield client
    client.close()


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
        elif "test_koji" in str(item.fspath):
            item.add_marker(pytest.mark.requires_koji)
        elif "embeddings" in str(item.fspath) and "mps" in item.name.lower():
            item.add_marker(pytest.mark.requires_gpu)


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_gpu: Tests requiring GPU/MPS")
    config.addinivalue_line("markers", "requires_koji: Tests requiring Koji database")


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

    # Add Koji info if available
    try:
        import koji

        header.append(f"Koji: available")
    except ImportError:
        pass

    return header


# ============================================================================
# Wave 2 Audio Processing Fixtures (Embedding Engine & Storage)
# ============================================================================


@pytest.fixture
def embedding_engine_instance():
    """Create a mock embedding engine for testing.

    Returns a mock that provides the interface expected by DocumentProcessor.
    """
    from unittest.mock import Mock

    engine = Mock()

    # Mock embed_images method
    def mock_embed_images(images, **kwargs):
        """Mock image embedding."""
        return {
            "embeddings": [np.random.randn(128).astype(np.float32) for _ in images],
            "cls_token": np.random.randn(128).astype(np.float32),
            "num_images": len(images),
        }

    # Mock embed_text method
    def mock_embed_text(texts, **kwargs):
        """Mock text embedding."""
        return {
            "embeddings": [np.random.randn(128).astype(np.float32) for _ in texts],
            "num_chunks": len(texts),
        }

    # Mock embed_query method
    def mock_embed_query(query, **kwargs):
        """Mock query embedding."""
        return {
            "embeddings": np.random.randn(128).astype(np.float32),
            "cls_token": np.random.randn(128).astype(np.float32),
        }

    engine.embed_images = mock_embed_images
    engine.embed_text = mock_embed_text
    engine.embed_query = mock_embed_query

    return engine


@pytest.fixture
def storage_client_instance(tmp_path):
    """Create a mock storage client for testing.

    Returns a mock that provides the Koji KojiClient interface expected by
    DocumentProcessor: create_document, insert_pages, insert_chunks, etc.
    """
    from src.core.testing.mocks import MockKojiClient

    client = MockKojiClient()
    client.open()

    return client
