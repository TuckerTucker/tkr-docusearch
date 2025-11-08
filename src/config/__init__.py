"""
Configuration module for DocuSearch MVP.

This module provides configuration classes for all system components:
- ModelConfig: ColPali model configuration
- StorageConfig: ChromaDB storage configuration
- ProcessingConfig: Document processing configuration
- ServiceURLs: Centralized service URL configuration (via get_service_urls)
"""

from .model_config import ModelConfig
from .processing_config import ProcessingConfig
from .storage_config import StorageConfig
from .urls import ServiceURLs, get_service_urls, reset_service_urls

__all__ = [
    "ModelConfig",
    "StorageConfig",
    "ProcessingConfig",
    "ServiceURLs",
    "get_service_urls",
    "reset_service_urls",
]
