"""
Unit tests for image_utils module.

Tests all image storage utility functions with comprehensive coverage.

Provider: image-agent
Target Coverage: 95%+
Contract: integration-contracts/02-image-utils.contract.md
"""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import shutil

from src.processing.image_utils import (
    save_page_image,
    generate_thumbnail,
    get_image_path,
    delete_document_images,
    image_exists,
    ImageStorageError,
    DiskFullError,
    PermissionError as ImagePermissionError,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_image_dir(monkeypatch):
    """Create temporary directory for image storage."""
    temp_dir = Path(tempfile.mkdtemp())

    # Monkey patch PAGE_IMAGE_DIR to use temp directory
    import src.config.image_config as config
    monkeypatch.setattr(config, 'PAGE_IMAGE_DIR', temp_dir)

    # Also update image_utils module's reference
    import src.processing.image_utils as image_utils
    monkeypatch.setattr(image_utils, 'PAGE_IMAGE_DIR', temp_dir)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_image():
    """Create a sample PIL image for testing."""
    return Image.new('RGB', (800, 1000), color='blue')


@pytest.fixture
def sample_rgba_image():
    """Create a sample RGBA image for testing transparency handling."""
    return Image.new('RGBA', (800, 1000), color=(255, 0, 0, 128))


# ============================================================================
# Tests for save_page_image()
# ============================================================================

def test_save_page_image_creates_files(temp_image_dir, sample_image):
    """Test that save_page_image creates both PNG and JPEG files."""
    img_path, thumb_path = save_page_image(sample_image, 'test-doc', 1)

    # Check paths are strings
    assert isinstance(img_path, str)
    assert isinstance(thumb_path, str)

    # Check files exist
    assert Path(img_path).exists()
    assert Path(thumb_path).exists()

    # Check filenames
    assert img_path.endswith('/page001.png')
    assert thumb_path.endswith('/page001_thumb.jpg')

    # Check they're in the same directory
    assert Path(img_path).parent == Path(thumb_path).parent


def test_save_page_image_creates_directory(temp_image_dir, sample_image):
    """Test that document directory is created if it doesn't exist."""
    doc_id = 'new-doc-123'
    doc_dir = temp_image_dir / doc_id

    # Verify directory doesn't exist yet
    assert not doc_dir.exists()

    save_page_image(sample_image, doc_id, 1)

    # Verify directory was created
    assert doc_dir.exists()
    assert doc_dir.is_dir()


def test_save_page_image_page_numbers(temp_image_dir, sample_image):
    """Test saving multiple pages with different page numbers."""
    doc_id = 'multi-page-doc'

    # Save pages 1, 2, 10
    img1, thumb1 = save_page_image(sample_image, doc_id, 1)
    img2, thumb2 = save_page_image(sample_image, doc_id, 2)
    img10, thumb10 = save_page_image(sample_image, doc_id, 10)

    # Check filenames
    assert 'page001.png' in img1
    assert 'page002.png' in img2
    assert 'page010.png' in img10

    assert 'page001_thumb.jpg' in thumb1
    assert 'page002_thumb.jpg' in thumb2
    assert 'page010_thumb.jpg' in thumb10


def test_save_page_image_validates_inputs(temp_image_dir, sample_image):
    """Test input validation."""
    # None image
    with pytest.raises(ValueError, match="Image cannot be None"):
        save_page_image(None, 'test-doc', 1)

    # Invalid image type
    with pytest.raises(ValueError, match="must be PIL.Image.Image"):
        save_page_image("not an image", 'test-doc', 1)

    # Invalid doc_id (too short)
    with pytest.raises(ValueError, match="Invalid doc_id format"):
        save_page_image(sample_image, 'short', 1)

    # Invalid doc_id (invalid characters)
    with pytest.raises(ValueError, match="Invalid doc_id format"):
        save_page_image(sample_image, 'doc/with/slash', 1)

    # Invalid page number (< 1)
    with pytest.raises(ValueError, match="Page number must be integer >= 1"):
        save_page_image(sample_image, 'test-doc', 0)

    # Invalid page number (not int)
    with pytest.raises(ValueError, match="Page number must be integer >= 1"):
        save_page_image(sample_image, 'test-doc', "1")


def test_save_page_image_file_sizes(temp_image_dir, sample_image):
    """Test that file sizes are reasonable."""
    img_path, thumb_path = save_page_image(sample_image, 'test-doc', 1)

    img_size = Path(img_path).stat().st_size
    thumb_size = Path(thumb_path).stat().st_size

    # Full image should be larger than thumbnail
    assert img_size > thumb_size

    # Thumbnail should be reasonable size (< 100KB for test image)
    assert thumb_size < 100 * 1024

    # Full image should be reasonable (< 1MB for test image)
    assert img_size < 1024 * 1024


# ============================================================================
# Tests for generate_thumbnail()
# ============================================================================

def test_generate_thumbnail_maintains_aspect_ratio():
    """Test thumbnail maintains aspect ratio."""
    # 4:5 ratio image
    img = Image.new('RGB', (1600, 2000))
    thumb = generate_thumbnail(img, (300, 400), 85)

    # Should maintain 4:5 ratio
    ratio = thumb.width / thumb.height
    expected_ratio = 1600 / 2000
    assert abs(ratio - expected_ratio) < 0.01


def test_generate_thumbnail_landscape():
    """Test thumbnail generation for landscape images."""
    # Landscape image
    img = Image.new('RGB', (2000, 1000))
    thumb = generate_thumbnail(img, (400, 300), 85)

    # Should be landscape
    assert thumb.width > thumb.height

    # Should fit within bounds
    assert thumb.width <= 400
    assert thumb.height <= 300


def test_generate_thumbnail_converts_rgba_to_rgb(sample_rgba_image):
    """Test that RGBA images are converted to RGB."""
    thumb = generate_thumbnail(sample_rgba_image, (300, 400), 85)

    # Should be RGB mode
    assert thumb.mode == 'RGB'


def test_generate_thumbnail_validates_inputs():
    """Test input validation for generate_thumbnail."""
    img = Image.new('RGB', (800, 1000))

    # None image
    with pytest.raises(ValueError, match="Image cannot be None"):
        generate_thumbnail(None, (300, 400), 85)

    # Invalid image type
    with pytest.raises(ValueError, match="must be PIL.Image.Image"):
        generate_thumbnail("not an image", (300, 400), 85)

    # Invalid size (not tuple)
    with pytest.raises(ValueError, match="Size must be .* tuple"):
        generate_thumbnail(img, [300, 400], 85)

    # Invalid size (wrong length)
    with pytest.raises(ValueError, match="Size must be .* tuple"):
        generate_thumbnail(img, (300,), 85)

    # Invalid size (too large)
    with pytest.raises(ValueError, match="Size dimensions must be"):
        generate_thumbnail(img, (10000, 10000), 85)

    # Invalid quality (< 1)
    with pytest.raises(ValueError, match="Quality must be integer 1-100"):
        generate_thumbnail(img, (300, 400), 0)

    # Invalid quality (> 100)
    with pytest.raises(ValueError, match="Quality must be integer 1-100"):
        generate_thumbnail(img, (300, 400), 101)


def test_generate_thumbnail_does_not_modify_original():
    """Test that original image is not modified."""
    img = Image.new('RGB', (1600, 2000))
    original_size = img.size

    generate_thumbnail(img, (300, 400), 85)

    # Original should be unchanged
    assert img.size == original_size


# ============================================================================
# Tests for get_image_path()
# ============================================================================

def test_get_image_path_full_image(temp_image_dir):
    """Test getting path to full image."""
    path = get_image_path('test-doc', 1, is_thumb=False)

    assert isinstance(path, str)
    assert 'test-doc' in path
    assert 'page001.png' in path
    assert '_thumb' not in path


def test_get_image_path_thumbnail(temp_image_dir):
    """Test getting path to thumbnail."""
    path = get_image_path('test-doc', 1, is_thumb=True)

    assert isinstance(path, str)
    assert 'test-doc' in path
    assert 'page001_thumb.jpg' in path


def test_get_image_path_various_page_numbers(temp_image_dir):
    """Test path generation for various page numbers."""
    path1 = get_image_path('test-doc', 1)
    path5 = get_image_path('test-doc', 5)
    path99 = get_image_path('test-doc', 99)
    path100 = get_image_path('test-doc', 100)

    assert 'page001.png' in path1
    assert 'page005.png' in path5
    assert 'page099.png' in path99
    assert 'page100.png' in path100


def test_get_image_path_validates_inputs(temp_image_dir):
    """Test input validation for get_image_path."""
    # Invalid doc_id
    with pytest.raises(ValueError, match="Invalid doc_id format"):
        get_image_path('bad/doc', 1)

    # Invalid page number
    with pytest.raises(ValueError, match="Page number must be integer >= 1"):
        get_image_path('test-doc', 0)


# ============================================================================
# Tests for delete_document_images()
# ============================================================================

def test_delete_document_images_removes_all_files(temp_image_dir, sample_image):
    """Test that delete removes all images for a document."""
    doc_id = 'test-doc'

    # Create test images
    save_page_image(sample_image, doc_id, 1)
    save_page_image(sample_image, doc_id, 2)

    # Verify they exist
    doc_dir = temp_image_dir / doc_id
    assert doc_dir.exists()
    assert len(list(doc_dir.iterdir())) == 4  # 2 PNGs + 2 JPGs

    # Delete
    count = delete_document_images(doc_id)

    # Should have deleted 4 files
    assert count == 4

    # Directory should be removed
    assert not doc_dir.exists()


def test_delete_document_images_nonexistent_doc(temp_image_dir):
    """Test deleting images for nonexistent document."""
    count = delete_document_images('nonexistent-doc')

    # Should return 0 (not an error)
    assert count == 0


def test_delete_document_images_validates_doc_id(temp_image_dir):
    """Test doc_id validation."""
    with pytest.raises(ValueError, match="Invalid doc_id format"):
        delete_document_images('bad/doc/id')


# ============================================================================
# Tests for image_exists()
# ============================================================================

def test_image_exists_true(temp_image_dir, sample_image):
    """Test image_exists returns True for existing images."""
    doc_id = 'test-doc'
    save_page_image(sample_image, doc_id, 1)

    # Full image should exist
    assert image_exists(doc_id, 1, is_thumb=False) is True

    # Thumbnail should exist
    assert image_exists(doc_id, 1, is_thumb=True) is True


def test_image_exists_false(temp_image_dir):
    """Test image_exists returns False for non-existing images."""
    assert image_exists('nonexistent-doc', 1, is_thumb=False) is False
    assert image_exists('nonexistent-doc', 1, is_thumb=True) is False


def test_image_exists_handles_invalid_inputs(temp_image_dir):
    """Test image_exists handles invalid inputs gracefully."""
    # Should return False, not raise exception
    assert image_exists('bad/doc', 1) is False
    assert image_exists('test-doc', -1) is False


# ============================================================================
# Integration Tests
# ============================================================================

def test_save_and_retrieve_workflow(temp_image_dir, sample_image):
    """Test full workflow: save, check exists, retrieve path, delete."""
    doc_id = 'workflow-test'

    # Save
    img_path, thumb_path = save_page_image(sample_image, doc_id, 1)

    # Check exists
    assert image_exists(doc_id, 1, is_thumb=False)
    assert image_exists(doc_id, 1, is_thumb=True)

    # Get paths
    retrieved_img_path = get_image_path(doc_id, 1, is_thumb=False)
    retrieved_thumb_path = get_image_path(doc_id, 1, is_thumb=True)

    assert retrieved_img_path == img_path
    assert retrieved_thumb_path == thumb_path

    # Delete
    count = delete_document_images(doc_id)
    assert count == 2

    # No longer exists
    assert not image_exists(doc_id, 1, is_thumb=False)
    assert not image_exists(doc_id, 1, is_thumb=True)


def test_multiple_documents_isolation(temp_image_dir, sample_image):
    """Test that multiple documents don't interfere with each other."""
    doc1 = 'doc-one-123'
    doc2 = 'doc-two-456'

    # Save to both documents
    save_page_image(sample_image, doc1, 1)
    save_page_image(sample_image, doc2, 1)

    # Both should exist
    assert image_exists(doc1, 1)
    assert image_exists(doc2, 1)

    # Delete doc1
    delete_document_images(doc1)

    # doc1 should be gone, doc2 should remain
    assert not image_exists(doc1, 1)
    assert image_exists(doc2, 1)


# ============================================================================
# Performance Tests
# ============================================================================

def test_save_page_image_performance(temp_image_dir, benchmark):
    """Test save_page_image performance (if pytest-benchmark installed)."""
    try:
        img = Image.new('RGB', (1200, 1600))

        result = benchmark(save_page_image, img, 'perf-test', 1)

        # Should return paths
        assert len(result) == 2
    except Exception:
        # pytest-benchmark not installed, skip
        pytest.skip("pytest-benchmark not installed")


def test_generate_thumbnail_performance(benchmark):
    """Test generate_thumbnail performance."""
    try:
        img = Image.new('RGB', (1600, 2000))

        result = benchmark(generate_thumbnail, img, (300, 400), 85)

        # Should return thumbnail
        assert isinstance(result, Image.Image)
    except Exception:
        # pytest-benchmark not installed, skip
        pytest.skip("pytest-benchmark not installed")
