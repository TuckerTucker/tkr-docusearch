"""
Filter group configuration for document type filtering.

This module defines logical groupings of file types for the UI filter dropdown,
mapping user-friendly category names to file extension lists.
"""

from typing import Dict, List, Optional

# Filter group definitions
# Maps group name to list of file extensions (with dot prefix)
FILTER_GROUPS: Dict[str, Optional[List[str]]] = {
    "all": None,  # None indicates no filtering (show all types)
    "pdf": [".pdf"],
    "audio": [".mp3", ".wav"],
    "office": [".docx", ".pptx", ".xlsx"],
    "text": [".md", ".asciidoc", ".csv", ".vtt", ".html", ".xhtml"],
    "images": [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"],
}

# Valid group names for validation
VALID_GROUPS = set(FILTER_GROUPS.keys())


def resolve_filter_group(group: str) -> Optional[List[str]]:
    """
    Resolve a filter group name to a list of file extensions.

    Args:
        group: Filter group name (e.g., 'audio', 'pdf', 'all')

    Returns:
        List of extensions with dot prefix (e.g., ['.mp3', '.wav'])
        or None if group is 'all' or invalid (defaults to 'all')

    Example:
        >>> resolve_filter_group('audio')
        ['.mp3', '.wav']
        >>> resolve_filter_group('all')
        None
        >>> resolve_filter_group('invalid')
        None
    """
    if group not in FILTER_GROUPS:
        # Invalid group defaults to 'all' (no filtering)
        return None

    return FILTER_GROUPS[group]


def get_group_display_name(group: str) -> str:
    """
    Get user-friendly display name for a filter group.

    Args:
        group: Filter group name

    Returns:
        User-friendly display name with format hints

    Example:
        >>> get_group_display_name('audio')
        'Audio (MP3, WAV)'
    """
    display_names = {
        "all": "All",
        "pdf": "PDF",
        "audio": "Audio (MP3, WAV)",
        "office": "Office Documents (Word, Excel, PowerPoint)",
        "text": "Text Documents (Markdown, CSV, HTML, VTT)",
        "images": "Images (PNG, JPG, TIFF, BMP, WebP)",
    }

    return display_names.get(group, "Unknown")
