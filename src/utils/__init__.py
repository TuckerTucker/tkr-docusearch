"""Utility modules for DocuSearch."""

from .paths import (
    PROJECT_ROOT,
    ensure_absolute,
    get_data_dir,
    get_images_dir,
    get_logs_dir,
    get_models_dir,
    get_uploads_dir,
    resolve_absolute,
    validate_file_path,
)

__all__ = [
    "PROJECT_ROOT",
    "resolve_absolute",
    "ensure_absolute",
    "get_data_dir",
    "get_uploads_dir",
    "get_images_dir",
    "get_models_dir",
    "get_logs_dir",
    "validate_file_path",
]
