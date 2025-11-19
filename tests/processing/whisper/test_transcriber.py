"""
Unit tests for custom whisper transcriber.

Tests Integration Contract IC-001 (Whisper Output Format).
"""

from pathlib import Path

import pytest

from tkr_docusearch.processing.whisper.output_validator import validate_whisper_output
from tkr_docusearch.processing.whisper.transcriber import (
    MODEL_MAPPING,
    AudioFormatError,
    AudioProcessingError,
    WhisperTranscriptionError,
    transcribe_audio,
)


class TestTranscribeAudio:
    """Test transcribe_audio() function."""

    def test_transcribe_audio_success(self, sample_audio_file_path):
        """Test successful audio transcription."""
        result = transcribe_audio(str(sample_audio_file_path))

        # Structure validation
        assert "text" in result
        assert "segments" in result
        assert "duration" in result
        assert "language" in result

        # Content validation
        assert len(result["text"]) > 0
        assert len(result["segments"]) > 0
        assert result["duration"] > 0

    def test_transcribe_audio_with_word_timestamps(self, sample_audio_file_path):
        """Test word-level timestamps are included."""
        result = transcribe_audio(str(sample_audio_file_path), word_timestamps=True)

        # All segments must have words
        for segment in result["segments"]:
            assert "words" in segment
            assert len(segment["words"]) > 0

            # All words must have timing
            for word in segment["words"]:
                assert "word" in word
                assert "start" in word
                assert "end" in word
                assert word["start"] < word["end"]

    def test_transcribe_audio_missing_file(self, nonexistent_audio_file):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            transcribe_audio(nonexistent_audio_file)

    def test_transcribe_audio_unsupported_format(self):
        """Test error handling for unsupported format."""
        # Check if PDF fixture exists
        pdf_path = Path("tests/fixtures/sample.pdf")
        if not pdf_path.exists():
            pytest.skip("PDF fixture not available")

        with pytest.raises(AudioFormatError):
            transcribe_audio(str(pdf_path))

    def test_transcribe_audio_invalid_model(self, sample_audio_file_path):
        """Test error handling for invalid model name."""
        with pytest.raises(ValueError, match="Invalid model"):
            transcribe_audio(str(sample_audio_file_path), model="invalid_model")

    def test_transcribe_audio_with_language(self, sample_audio_file_path):
        """Test transcription with explicit language."""
        result = transcribe_audio(str(sample_audio_file_path), language="en")

        assert result["language"] == "en"

    def test_transcribe_audio_returns_duration(self, sample_audio_file_path):
        """Test duration is included in output."""
        result = transcribe_audio(str(sample_audio_file_path))

        assert "duration" in result
        assert isinstance(result["duration"], (int, float))
        assert result["duration"] > 0


class TestOutputValidation:
    """Test whisper output validation."""

    def test_whisper_output_validation(self, sample_audio_file_path):
        """Test output format validation passes for real transcription."""
        result = transcribe_audio(str(sample_audio_file_path))

        # Contract IC-001 validation
        is_valid, errors = validate_whisper_output(result)
        assert is_valid, f"Validation errors: {errors}"

    def test_timestamp_monotonicity(self, sample_audio_file_path):
        """Test timestamps are monotonically increasing."""
        result = transcribe_audio(str(sample_audio_file_path))

        prev_end = 0.0
        for segment in result["segments"]:
            # Allow small overlap (0.1s tolerance)
            assert (
                segment["start"] >= prev_end - 0.1
            ), f"Segment starts before previous ends: {segment['start']} < {prev_end}"
            prev_end = segment["end"]

    def test_validate_invalid_output_missing_fields(self):
        """Test validation detects missing fields."""
        invalid_result = {
            "text": "test",
            # Missing segments, language, duration
        }

        is_valid, errors = validate_whisper_output(invalid_result)

        assert not is_valid
        assert len(errors) > 0
        assert any("segments" in err for err in errors)

    def test_validate_invalid_output_empty_segments(self):
        """Test validation detects empty segments."""
        invalid_result = {
            "text": "test",
            "segments": [],  # Empty
            "language": "en",
            "duration": 10.0,
        }

        is_valid, errors = validate_whisper_output(invalid_result)

        assert not is_valid
        assert any("empty" in err.lower() for err in errors)

    def test_validate_invalid_output_missing_words(self):
        """Test validation detects missing word timestamps."""
        invalid_result = {
            "text": "test",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 1.0,
                    "text": "test",
                    "words": [],  # Empty words - violates IC-001
                }
            ],
            "language": "en",
            "duration": 1.0,
        }

        is_valid, errors = validate_whisper_output(invalid_result)

        assert not is_valid
        assert any("words" in err.lower() for err in errors)


class TestContractIC001:
    """
    Validate compliance with IC-001: Whisper Output Format.

    This test class ensures the transcribe_audio() function meets
    all requirements specified in Integration Contract IC-001.
    """

    def test_contract_ic001_compliance(self, sample_audio_file_path):
        """Validate compliance with IC-001: Whisper Output Format."""
        result = transcribe_audio(str(sample_audio_file_path))

        # Required top-level fields
        assert "text" in result
        assert "segments" in result
        assert "language" in result
        assert "duration" in result

        # Text field validation
        assert isinstance(result["text"], str)
        assert len(result["text"]) > 0

        # Segments validation
        assert isinstance(result["segments"], list)
        assert len(result["segments"]) > 0

        for segment in result["segments"]:
            # Required segment fields
            assert "id" in segment
            assert "start" in segment
            assert "end" in segment
            assert "text" in segment
            assert "words" in segment

            # Timing validation
            assert isinstance(segment["start"], (int, float))
            assert isinstance(segment["end"], (int, float))
            assert segment["start"] < segment["end"]

            # Words validation (CRITICAL for IC-001)
            assert isinstance(segment["words"], list)
            assert len(segment["words"]) > 0, "IC-001 requires word-level timestamps"

            for word in segment["words"]:
                # Required word fields
                assert "word" in word
                assert "start" in word
                assert "end" in word
                assert "probability" in word

                # Word timing validation
                assert isinstance(word["start"], (int, float))
                assert isinstance(word["end"], (int, float))
                assert word["start"] < word["end"]

                # Probability validation
                assert isinstance(word["probability"], (int, float))
                assert 0.0 <= word["probability"] <= 1.0

        # Language field validation
        assert isinstance(result["language"], str)

        # Duration validation
        assert isinstance(result["duration"], (int, float))
        assert result["duration"] > 0

    def test_contract_ic001_duration_accuracy(self, sample_audio_file_path):
        """Test duration matches actual audio file length (±0.1s tolerance)."""
        result = transcribe_audio(str(sample_audio_file_path))

        try:
            import librosa

            actual_duration = librosa.get_duration(path=str(sample_audio_file_path))
            assert (
                abs(result["duration"] - actual_duration) < 0.1
            ), f"Duration mismatch: {result['duration']} vs {actual_duration}"
        except ImportError:
            pytest.skip("librosa not available for duration verification")

    def test_contract_ic001_function_signature(self):
        """Test function signature matches IC-001 specification."""
        import inspect

        sig = inspect.signature(transcribe_audio)

        # Check parameters
        params = sig.parameters
        assert "file_path" in params
        assert "model" in params
        assert "language" in params
        assert "word_timestamps" in params
        assert "temperature" in params

        # Check defaults
        assert params["model"].default == "turbo"
        assert params["language"].default is None
        assert params["word_timestamps"].default is True
        assert params["temperature"].default == 0.0


class TestModelMapping:
    """Test model name to HuggingFace repo mapping."""

    def test_model_mapping_exists(self):
        """Test model mapping dictionary exists."""
        assert MODEL_MAPPING is not None
        assert isinstance(MODEL_MAPPING, dict)

    def test_model_mapping_completeness(self):
        """Test all required models are mapped."""
        required_models = ["turbo", "base", "small", "medium", "large"]

        for model in required_models:
            assert model in MODEL_MAPPING
            assert MODEL_MAPPING[model].startswith("mlx-community/")

    def test_invalid_model_raises_error(self, sample_audio_file_path):
        """Test invalid model name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid model"):
            transcribe_audio(str(sample_audio_file_path), model="nonexistent")


class TestErrorHandling:
    """Test error handling compliance with IC-004."""

    def test_file_not_found_error(self):
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="not found"):
            transcribe_audio("/nonexistent/file.mp3")

    def test_audio_format_error(self):
        """Test AudioFormatError for unsupported format."""
        pdf_path = Path("tests/fixtures/sample.pdf")
        if not pdf_path.exists():
            pytest.skip("PDF fixture not available")

        with pytest.raises(AudioFormatError, match="Unsupported"):
            transcribe_audio(str(pdf_path))

    def test_audio_format_error_for_txt_file(self, tmp_path):
        """Test AudioFormatError for text file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")

        with pytest.raises(AudioFormatError):
            transcribe_audio(str(txt_file))

    def test_exception_hierarchy(self):
        """Test exception hierarchy follows IC-004."""
        # WhisperTranscriptionError is subclass of AudioProcessingError
        assert issubclass(WhisperTranscriptionError, AudioProcessingError)

        # AudioFormatError is subclass of AudioProcessingError
        assert issubclass(AudioFormatError, AudioProcessingError)

        # AudioProcessingError is subclass of Exception
        assert issubclass(AudioProcessingError, Exception)
