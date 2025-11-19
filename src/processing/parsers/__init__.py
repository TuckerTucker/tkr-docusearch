"""
Document parsing strategies.

This module contains strategy pattern implementations for different
document types, reducing complexity in DoclingParser.
"""

from .audio_metadata_extractor import AudioMetadataExtractor
from .doc_converter import DocConverter
from .format_options_builder import FormatOptionsBuilder
from .slide_renderer import SlideRenderer
from .symlink_helper import SymlinkHelper

__all__ = [
    "FormatOptionsBuilder",
    "SlideRenderer",
    "AudioMetadataExtractor",
    "SymlinkHelper",
    "DocConverter",
]
