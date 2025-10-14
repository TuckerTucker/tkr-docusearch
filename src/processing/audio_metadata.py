"""
Audio metadata extraction using mutagen.

Extracts ID3 tags, audio properties, and album art from MP3/WAV files.
Designed to work alongside Docling's ASR transcription pipeline.

See AUDIO_METADATA_SCHEMA.md for complete metadata field documentation.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AudioMetadata:
    """Container for extracted audio metadata."""

    # ID3 text tags
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    year: Optional[str] = None
    genre: Optional[str] = None
    track_number: Optional[str] = None
    composer: Optional[str] = None
    comment: Optional[str] = None
    publisher: Optional[str] = None

    # Audio properties
    duration_seconds: Optional[float] = None
    bitrate_kbps: Optional[int] = None
    sample_rate_hz: Optional[int] = None
    channels: Optional[int] = None
    encoder: Optional[str] = None

    # Album art info (image data stored separately)
    has_album_art: bool = False
    album_art_mime: Optional[str] = None
    album_art_size_bytes: Optional[int] = None
    album_art_description: Optional[str] = None
    album_art_data: Optional[bytes] = None  # Raw image data (for saving)

    def to_chromadb_metadata(self) -> Dict[str, Any]:
        """
        Convert to ChromaDB metadata dict with audio_ prefix.

        Returns dict with only non-None values to keep metadata lean.
        """
        metadata = {}

        # ID3 tags with audio_ prefix
        if self.title:
            metadata["audio_title"] = self.title
        if self.artist:
            metadata["audio_artist"] = self.artist
        if self.album:
            metadata["audio_album"] = self.album
        if self.album_artist:
            metadata["audio_album_artist"] = self.album_artist
        if self.year:
            metadata["audio_year"] = self.year
        if self.genre:
            metadata["audio_genre"] = self.genre
        if self.track_number:
            metadata["audio_track_number"] = self.track_number
        if self.composer:
            metadata["audio_composer"] = self.composer
        if self.comment:
            # Truncate long comments (podcast descriptions can be huge)
            comment = self.comment[:1000] if len(self.comment) > 1000 else self.comment
            metadata["audio_comment"] = comment
        if self.publisher:
            metadata["audio_publisher"] = self.publisher

        # Audio properties
        if self.duration_seconds is not None:
            metadata["audio_duration_seconds"] = self.duration_seconds
        if self.bitrate_kbps is not None:
            metadata["audio_bitrate_kbps"] = self.bitrate_kbps
        if self.sample_rate_hz is not None:
            metadata["audio_sample_rate_hz"] = self.sample_rate_hz
        if self.channels is not None:
            metadata["audio_channels"] = self.channels
        if self.encoder:
            metadata["audio_encoder"] = self.encoder

        # Album art metadata (not the image data itself)
        metadata["has_album_art"] = self.has_album_art
        if self.album_art_mime:
            metadata["album_art_mime"] = self.album_art_mime
        if self.album_art_size_bytes is not None:
            metadata["album_art_size_bytes"] = self.album_art_size_bytes
        if self.album_art_description:
            metadata["album_art_description"] = self.album_art_description

        return metadata


def extract_audio_metadata(file_path: str) -> AudioMetadata:
    """
    Extract ID3 tags and audio properties from an audio file.

    Args:
        file_path: Path to MP3 or WAV file

    Returns:
        AudioMetadata instance with extracted data

    Raises:
        ImportError: If mutagen is not installed
        FileNotFoundError: If file doesn't exist
        Exception: For other errors (logged, not raised - returns empty metadata)
    """
    if not MUTAGEN_AVAILABLE:
        logger.error("mutagen library not installed - cannot extract audio metadata")
        raise ImportError("mutagen is required for audio metadata extraction")

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    metadata = AudioMetadata()

    try:
        # Load audio file with mutagen
        audio = MutagenFile(file_path)

        if audio is None:
            logger.warning(f"File type not recognized by mutagen: {file_path}")
            return metadata

        logger.debug(f"Processing audio file: {file_path_obj.name} (type: {type(audio).__name__})")

        # Extract audio properties
        _extract_audio_properties(audio, metadata)

        # Extract ID3 tags (if present)
        _extract_id3_tags(audio, metadata)

        # Extract album art (if present)
        _extract_album_art(audio, metadata)

        logger.info(
            f"Extracted metadata from {file_path_obj.name}: "
            f"title={metadata.title}, artist={metadata.artist}, "
            f"duration={metadata.duration_seconds:.1f}s, "
            f"album_art={metadata.has_album_art}"
        )

    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}", exc_info=True)
        # Return partially populated metadata rather than failing

    return metadata


def _extract_audio_properties(audio, metadata: AudioMetadata) -> None:
    """Extract audio properties (duration, bitrate, etc.) from mutagen audio object."""
    if not hasattr(audio, 'info'):
        return

    info = audio.info

    if hasattr(info, 'length'):
        metadata.duration_seconds = float(info.length)

    if hasattr(info, 'bitrate'):
        metadata.bitrate_kbps = int(info.bitrate // 1000)

    if hasattr(info, 'sample_rate'):
        metadata.sample_rate_hz = int(info.sample_rate)

    if hasattr(info, 'channels'):
        metadata.channels = int(info.channels)


def _extract_id3_tags(audio, metadata: AudioMetadata) -> None:
    """Extract ID3 tags from mutagen audio object."""
    if not hasattr(audio, 'tags') or audio.tags is None:
        logger.debug("No ID3 tags found in audio file")
        return

    tags = audio.tags

    # Helper to safely get text from ID3 frames
    def get_text_tag(tag_id: str) -> Optional[str]:
        if tag_id in tags:
            tag = tags[tag_id]
            if hasattr(tag, 'text') and tag.text:
                return str(tag.text[0])
        return None

    # Extract standard ID3v2 text frames
    metadata.title = get_text_tag('TIT2')           # Title
    metadata.artist = get_text_tag('TPE1')          # Artist
    metadata.album = get_text_tag('TALB')           # Album
    metadata.album_artist = get_text_tag('TPE2')    # Album Artist
    metadata.year = get_text_tag('TDRC')            # Year
    metadata.genre = get_text_tag('TCON')           # Genre
    metadata.track_number = get_text_tag('TRCK')    # Track number
    metadata.composer = get_text_tag('TCOM')        # Composer
    metadata.publisher = get_text_tag('TPUB')       # Publisher
    metadata.encoder = get_text_tag('TSSE')         # Encoder software

    # Comment frame (can have multiple, take first)
    if 'COMM::eng' in tags:
        comm = tags['COMM::eng']
        if hasattr(comm, 'text') and comm.text:
            metadata.comment = str(comm.text[0])
    elif any(k.startswith('COMM:') for k in tags.keys()):
        # Fallback to any comment frame
        comm_keys = [k for k in tags.keys() if k.startswith('COMM:')]
        if comm_keys:
            comm = tags[comm_keys[0]]
            if hasattr(comm, 'text') and comm.text:
                metadata.comment = str(comm.text[0])


def _extract_album_art(audio, metadata: AudioMetadata) -> None:
    """Extract album art from mutagen audio object."""
    if not hasattr(audio, 'tags') or audio.tags is None:
        return

    tags = audio.tags

    # Find APIC frames (attached pictures)
    apic_frames = [k for k in tags.keys() if k.startswith('APIC:')]

    if not apic_frames:
        return

    # Prefer front cover, otherwise take first
    apic_key = None
    for key in apic_frames:
        if 'Cover (front)' in key or key == 'APIC:':
            apic_key = key
            break

    if apic_key is None:
        apic_key = apic_frames[0]

    apic = tags[apic_key]

    if hasattr(apic, 'data') and apic.data:
        metadata.has_album_art = True
        metadata.album_art_data = apic.data
        metadata.album_art_size_bytes = len(apic.data)

        if hasattr(apic, 'mime'):
            metadata.album_art_mime = apic.mime

        if hasattr(apic, 'desc'):
            metadata.album_art_description = apic.desc

        logger.debug(
            f"Extracted album art: {metadata.album_art_mime}, "
            f"{metadata.album_art_size_bytes / 1024:.1f} KB"
        )


def save_album_art(
    doc_id: str,
    metadata: AudioMetadata,
    base_dir: str = "data/images",
    use_placeholder: bool = True
) -> Optional[str]:
    """
    Save album art image to filesystem, or use placeholder if no album art.

    Args:
        doc_id: Document ID (used for directory name)
        metadata: AudioMetadata instance with album art data
        base_dir: Base directory for image storage
        use_placeholder: If True, use placeholder image when no album art exists

    Returns:
        Relative path to saved image, or None if no album art and use_placeholder=False
    """
    try:
        # Create directory for this document's images
        doc_image_dir = Path(base_dir) / doc_id
        doc_image_dir.mkdir(parents=True, exist_ok=True)

        if metadata.has_album_art and metadata.album_art_data:
            # Determine file extension from MIME type
            ext = _mime_to_extension(metadata.album_art_mime)

            # Save actual album art
            image_path = doc_image_dir / f"cover{ext}"
            image_path.write_bytes(metadata.album_art_data)

            # Return relative path
            relative_path = str(image_path)
            logger.info(f"Saved album art to: {relative_path}")

            return relative_path
        elif use_placeholder:
            # No album art - copy placeholder
            import shutil

            placeholder_path = Path(base_dir) / "placeholders" / "audio-placeholder.svg"

            if not placeholder_path.exists():
                logger.warning(f"Placeholder image not found: {placeholder_path}")
                return None

            # Copy placeholder to doc directory
            dest_path = doc_image_dir / "cover.svg"
            shutil.copy2(placeholder_path, dest_path)

            relative_path = str(dest_path)
            logger.info(f"Using placeholder image for audio file: {relative_path}")

            return relative_path
        else:
            return None

    except Exception as e:
        logger.error(f"Failed to save album art for {doc_id}: {e}")
        return None


def _mime_to_extension(mime_type: Optional[str]) -> str:
    """Convert MIME type to file extension."""
    if not mime_type:
        return ".jpg"  # Default

    mime_map = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/webp": ".webp",
    }

    return mime_map.get(mime_type.lower(), ".jpg")
