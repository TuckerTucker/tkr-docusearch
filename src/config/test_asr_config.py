"""
Unit tests for ASR configuration.

Tests AsrConfig dataclass validation, environment loading, and Docling conversion.
"""

import os

import pytest

from tkr_docusearch.config.processing_config import AsrConfig


class TestAsrConfigDefaults:
    """Test default configuration values."""

    def test_asr_config_defaults(self):
        """Test default configuration values."""
        config = AsrConfig()

        assert config.enabled is True
        assert config.model == "turbo"
        assert config.language == "en"
        assert config.device == "mps"
        assert config.word_timestamps is True
        assert config.temperature == 0.0
        assert config.max_time_chunk == 30.0

    def test_repr(self):
        """Test string representation."""
        config = AsrConfig()
        repr_str = repr(config)

        assert "AsrConfig" in repr_str
        assert "turbo" in repr_str
        assert "en" in repr_str
        assert "mps" in repr_str

    def test_to_dict(self):
        """Test dictionary conversion."""
        config = AsrConfig()
        config_dict = config.to_dict()

        assert config_dict["enabled"] is True
        assert config_dict["model"] == "turbo"
        assert config_dict["language"] == "en"
        assert config_dict["device"] == "mps"
        assert config_dict["word_timestamps"] is True
        assert config_dict["temperature"] == 0.0
        assert config_dict["max_time_chunk"] == 30.0


class TestAsrConfigValidation:
    """Test configuration validation."""

    def test_validation_invalid_model(self):
        """Test validation rejects invalid model names."""
        with pytest.raises(ValueError, match="Invalid model"):
            AsrConfig(model="invalid")

    def test_validation_valid_models(self):
        """Test all valid model names."""
        valid_models = ["turbo", "base", "small", "medium", "large"]

        for model in valid_models:
            config = AsrConfig(model=model)
            assert config.model == model

    def test_validation_invalid_device(self):
        """Test validation rejects invalid device types."""
        with pytest.raises(ValueError, match="Invalid device"):
            AsrConfig(device="invalid")

    def test_validation_valid_devices(self):
        """Test all valid device types."""
        valid_devices = ["mps", "cpu", "cuda"]

        for device in valid_devices:
            config = AsrConfig(device=device)
            assert config.device == device

    def test_validation_temperature_too_low(self):
        """Test validation rejects negative temperature."""
        with pytest.raises(ValueError, match="Temperature must be"):
            AsrConfig(temperature=-0.1)

    def test_validation_temperature_too_high(self):
        """Test validation rejects temperature > 1.0."""
        with pytest.raises(ValueError, match="Temperature must be"):
            AsrConfig(temperature=1.1)

    def test_validation_temperature_valid_range(self):
        """Test valid temperature range."""
        config = AsrConfig(temperature=0.0)
        assert config.temperature == 0.0

        config = AsrConfig(temperature=0.5)
        assert config.temperature == 0.5

        config = AsrConfig(temperature=1.0)
        assert config.temperature == 1.0

    def test_validation_max_time_chunk_negative(self):
        """Test validation rejects negative max_time_chunk."""
        with pytest.raises(ValueError, match="max_time_chunk must be positive"):
            AsrConfig(max_time_chunk=-1.0)

    def test_validation_max_time_chunk_zero(self):
        """Test validation rejects zero max_time_chunk."""
        with pytest.raises(ValueError, match="max_time_chunk must be positive"):
            AsrConfig(max_time_chunk=0.0)

    def test_validation_max_time_chunk_valid(self):
        """Test valid max_time_chunk values."""
        config = AsrConfig(max_time_chunk=10.0)
        assert config.max_time_chunk == 10.0

        config = AsrConfig(max_time_chunk=60.0)
        assert config.max_time_chunk == 60.0


class TestAsrConfigFromEnv:
    """Test loading configuration from environment variables."""

    def setup_method(self):
        """Clean up environment before each test."""
        self.env_vars = [
            "ASR_ENABLED",
            "ASR_MODEL",
            "ASR_LANGUAGE",
            "ASR_DEVICE",
            "ASR_WORD_TIMESTAMPS",
            "ASR_TEMPERATURE",
            "ASR_MAX_TIME_CHUNK",
        ]
        for var in self.env_vars:
            if var in os.environ:
                del os.environ[var]

    def teardown_method(self):
        """Clean up environment after each test."""
        for var in self.env_vars:
            if var in os.environ:
                del os.environ[var]

    def test_from_env_defaults(self):
        """Test from_env() with no environment variables (uses defaults)."""
        config = AsrConfig.from_env()

        assert config.enabled is True
        assert config.model == "turbo"
        assert config.language == "en"
        assert config.device == "mps"

    def test_from_env_with_all_variables(self):
        """Test from_env() with all environment variables set."""
        os.environ["ASR_ENABLED"] = "false"
        os.environ["ASR_MODEL"] = "base"
        os.environ["ASR_LANGUAGE"] = "es"
        os.environ["ASR_DEVICE"] = "cpu"
        os.environ["ASR_WORD_TIMESTAMPS"] = "false"
        os.environ["ASR_TEMPERATURE"] = "0.5"
        os.environ["ASR_MAX_TIME_CHUNK"] = "60.0"

        config = AsrConfig.from_env()

        assert config.enabled is False
        assert config.model == "base"
        assert config.language == "es"
        assert config.device == "cpu"
        assert config.word_timestamps is False
        assert config.temperature == 0.5
        assert config.max_time_chunk == 60.0

    def test_from_env_boolean_parsing(self):
        """Test boolean environment variable parsing."""
        # Test "true"
        os.environ["ASR_ENABLED"] = "true"
        config = AsrConfig.from_env()
        assert config.enabled is True

        # Test "false"
        os.environ["ASR_ENABLED"] = "false"
        config = AsrConfig.from_env()
        assert config.enabled is False

        # Test case insensitive
        os.environ["ASR_ENABLED"] = "TRUE"
        config = AsrConfig.from_env()
        assert config.enabled is True

        os.environ["ASR_ENABLED"] = "FALSE"
        config = AsrConfig.from_env()
        assert config.enabled is False

    def test_from_env_invalid_model_uses_default(self):
        """Test invalid model falls back to default."""
        os.environ["ASR_MODEL"] = "invalid"

        config = AsrConfig.from_env()
        # Should fall back to default due to validation error
        assert config.model == "turbo"

    def test_from_env_invalid_temperature_uses_default(self):
        """Test invalid temperature falls back to default."""
        os.environ["ASR_TEMPERATURE"] = "not_a_number"

        config = AsrConfig.from_env()
        # Should fall back to default 0.0
        assert config.temperature == 0.0

    def test_from_env_invalid_max_time_chunk_uses_default(self):
        """Test invalid max_time_chunk falls back to default."""
        os.environ["ASR_MAX_TIME_CHUNK"] = "not_a_number"

        config = AsrConfig.from_env()
        # Should fall back to default 30.0
        assert config.max_time_chunk == 30.0


class TestAsrConfigToDoclingModelSpec:
    """Test conversion to Docling ASR model specification."""

    def test_to_docling_model_spec_returns_correct_type(self):
        """Test conversion returns InlineAsrNativeWhisperOptions."""
        config = AsrConfig(model="turbo", language="en")

        try:
            spec = config.to_docling_model_spec()

            # Check type
            from docling.datamodel.pipeline_options_asr_model import InlineAsrNativeWhisperOptions

            assert isinstance(spec, InlineAsrNativeWhisperOptions)

            # Check repo_id contains model name
            assert "turbo" in spec.repo_id or "large-v3-turbo" in spec.repo_id

        except ImportError:
            # If Docling ASR not installed, test should raise ImportError
            with pytest.raises(ImportError, match="Docling ASR not installed"):
                config.to_docling_model_spec()

    def test_model_name_mapping(self):
        """Test model name to repo_id mapping."""
        models = ["turbo", "base", "small", "medium", "large"]

        for model in models:
            config = AsrConfig(model=model)

            try:
                spec = config.to_docling_model_spec()
                # All repo_ids should start with "openai/whisper-"
                assert spec.repo_id.startswith("openai/whisper-")
            except ImportError:
                # Skip if Docling ASR not installed
                pytest.skip("Docling ASR not installed")

    def test_language_mapping(self):
        """Test language code mapping."""
        # Regular language code
        config = AsrConfig(model="turbo", language="es")

        try:
            spec = config.to_docling_model_spec()
            assert spec.language == "es"
        except ImportError:
            pytest.skip("Docling ASR not installed")

        # Auto detection (omits language parameter, Docling defaults to "en")
        config = AsrConfig(model="turbo", language="auto")

        try:
            spec = config.to_docling_model_spec()
            # When language is omitted, Docling defaults to "en"
            assert spec.language == "en"
        except ImportError:
            pytest.skip("Docling ASR not installed")

    def test_word_timestamps_setting(self):
        """Test word_timestamps setting is passed through."""
        config = AsrConfig(word_timestamps=True)

        try:
            spec = config.to_docling_model_spec()
            assert spec.word_timestamps is True
        except ImportError:
            pytest.skip("Docling ASR not installed")

        config = AsrConfig(word_timestamps=False)

        try:
            spec = config.to_docling_model_spec()
            assert spec.word_timestamps is False
        except ImportError:
            pytest.skip("Docling ASR not installed")

    def test_temperature_setting(self):
        """Test temperature setting is passed through."""
        config = AsrConfig(temperature=0.5)

        try:
            spec = config.to_docling_model_spec()
            assert spec.temperature == 0.5
        except ImportError:
            pytest.skip("Docling ASR not installed")

    def test_max_time_chunk_setting(self):
        """Test max_time_chunk setting is passed through."""
        config = AsrConfig(max_time_chunk=60.0)

        try:
            spec = config.to_docling_model_spec()
            assert spec.max_time_chunk == 60.0
        except ImportError:
            pytest.skip("Docling ASR not installed")


class TestAsrConfigIntegration:
    """Test integration scenarios."""

    def test_create_modify_convert(self):
        """Test creating, modifying, and converting configuration."""
        # Create default config
        config = AsrConfig()
        assert config.model == "turbo"

        # Modify and create new config
        config2 = AsrConfig(model="base", language="fr", device="cpu")

        assert config2.model == "base"
        assert config2.language == "fr"
        assert config2.device == "cpu"

        # Convert to dict
        config_dict = config2.to_dict()
        assert config_dict["model"] == "base"

        # Convert to Docling spec
        try:
            spec = config2.to_docling_model_spec()
            assert "base" in spec.repo_id
        except ImportError:
            pytest.skip("Docling ASR not installed")

    def test_config_for_different_use_cases(self):
        """Test configurations for different use cases."""
        # Fast/low quality
        fast_config = AsrConfig(model="base", temperature=0.0, word_timestamps=False)
        assert fast_config.model == "base"

        # High quality
        quality_config = AsrConfig(model="large", temperature=0.0, word_timestamps=True)
        assert quality_config.model == "large"

        # Multi-language
        multilang_config = AsrConfig(language="auto")
        assert multilang_config.language == "auto"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
