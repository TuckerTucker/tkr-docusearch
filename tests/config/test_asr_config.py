"""
Unit tests for AsrConfig custom whisper configuration.

Tests Integration Contract IC-003 (ASR Config Interface).
"""

import pytest

from src.config.processing_config import AsrConfig


class TestAsrConfigBasics:
    """Test basic AsrConfig functionality."""

    def test_asr_config_default_values(self):
        """Test default configuration values."""
        config = AsrConfig()

        assert config.enabled is True
        assert config.model == "turbo"
        assert config.language == "en"
        assert config.device == "mps"
        assert config.word_timestamps is True
        assert config.temperature == 0.0

    def test_asr_config_custom_values(self):
        """Test configuration with custom values."""
        config = AsrConfig(model="base", language="es", device="cpu", temperature=0.5)

        assert config.model == "base"
        assert config.language == "es"
        assert config.device == "cpu"
        assert config.temperature == 0.5

    def test_asr_config_to_dict(self):
        """Test conversion to dictionary."""
        config = AsrConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "enabled" in config_dict
        assert "model" in config_dict
        assert "word_timestamps" in config_dict


class TestAsrConfigFromEnv:
    """Test loading configuration from environment."""

    def test_from_env_default(self, monkeypatch):
        """Test loading default config from environment."""
        # Clear relevant env vars
        for var in ["ASR_MODEL", "ASR_LANGUAGE", "ASR_DEVICE"]:
            monkeypatch.delenv(var, raising=False)

        config = AsrConfig.from_env()

        assert config.model == "turbo"
        assert config.language == "en"
        assert config.device == "mps"

    def test_from_env_custom_values(self, monkeypatch):
        """Test loading custom values from environment."""
        monkeypatch.setenv("ASR_MODEL", "base")
        monkeypatch.setenv("ASR_LANGUAGE", "es")
        monkeypatch.setenv("ASR_DEVICE", "cpu")
        monkeypatch.setenv("ASR_TEMPERATURE", "0.5")

        config = AsrConfig.from_env()

        assert config.model == "base"
        assert config.language == "es"
        assert config.device == "cpu"
        assert config.temperature == 0.5

    def test_from_env_word_timestamps(self, monkeypatch):
        """Test word_timestamps environment variable."""
        monkeypatch.setenv("ASR_WORD_TIMESTAMPS", "true")
        config = AsrConfig.from_env()
        assert config.word_timestamps is True

        # word_timestamps=false should raise error in validate()
        monkeypatch.setenv("ASR_WORD_TIMESTAMPS", "false")
        with pytest.raises(ValueError, match="word_timestamps"):
            AsrConfig.from_env()

    def test_from_env_caption_settings(self, monkeypatch):
        """Test caption splitting settings from environment."""
        monkeypatch.setenv("ASR_MAX_CAPTION_DURATION", "8.0")
        monkeypatch.setenv("ASR_MAX_CAPTION_CHARS", "150")

        config = AsrConfig.from_env()

        assert config.max_caption_duration == 8.0
        assert config.max_caption_chars == 150


class TestToWhisperKwargs:
    """Test to_whisper_kwargs() method (IC-003)."""

    def test_to_whisper_kwargs_structure(self):
        """Test whisper kwargs have correct structure."""
        config = AsrConfig(model="turbo", language="en")
        kwargs = config.to_whisper_kwargs()

        # Required fields per IC-003
        assert "path_or_hf_repo" in kwargs
        assert "word_timestamps" in kwargs
        assert "temperature" in kwargs
        assert "fp16" in kwargs
        assert "language" in kwargs

    def test_to_whisper_kwargs_values(self):
        """Test whisper kwargs have correct values."""
        config = AsrConfig(model="base", language="es", word_timestamps=True, temperature=0.5)
        kwargs = config.to_whisper_kwargs()

        assert kwargs["word_timestamps"] is True
        assert kwargs["temperature"] == 0.5
        assert kwargs["fp16"] is False
        assert kwargs["language"] == "es"

    def test_to_whisper_kwargs_model_mapping(self):
        """Test model names map to HuggingFace repos."""
        models_and_repos = [
            ("turbo", "mlx-community/whisper-large-v3-turbo"),
            ("base", "mlx-community/whisper-base-mlx"),
            ("small", "mlx-community/whisper-small-mlx"),
            ("medium", "mlx-community/whisper-medium-mlx"),
            ("large", "mlx-community/whisper-large-v3-mlx"),
        ]

        for model, expected_repo in models_and_repos:
            config = AsrConfig(model=model)
            kwargs = config.to_whisper_kwargs()
            assert kwargs["path_or_hf_repo"] == expected_repo

    def test_to_whisper_kwargs_language_auto(self):
        """Test language='auto' becomes None for auto-detection."""
        config = AsrConfig(language="auto")
        kwargs = config.to_whisper_kwargs()

        assert kwargs["language"] is None

    def test_to_whisper_kwargs_language_none(self):
        """Test language=None becomes None."""
        config = AsrConfig(language=None)
        kwargs = config.to_whisper_kwargs()

        assert kwargs["language"] is None

    def test_to_whisper_kwargs_invalid_model(self):
        """Test invalid model raises error."""
        config = AsrConfig(model="turbo")
        config.model = "invalid"  # Bypass validation

        with pytest.raises(ValueError, match="Invalid model"):
            config.to_whisper_kwargs()


class TestValidateMethod:
    """Test validate() method (IC-003)."""

    def test_validate_success(self):
        """Test validation passes for valid config."""
        config = AsrConfig()
        config.validate()  # Should not raise

    def test_validate_enforces_word_timestamps_true(self):
        """Test validation enforces word_timestamps=True."""
        config = AsrConfig()
        config.word_timestamps = False

        with pytest.raises(ValueError, match="word_timestamps must be True"):
            config.validate()

    def test_validate_model_names(self):
        """Test validation of model names."""
        valid_models = ["turbo", "base", "small", "medium", "large"]

        # Valid models should pass
        for model in valid_models:
            config = AsrConfig(model=model)
            config.validate()  # Should not raise

        # Invalid model should fail
        config = AsrConfig()
        config.model = "invalid"

        with pytest.raises(ValueError, match="Invalid model"):
            config.validate()

    def test_validate_device_names(self):
        """Test validation of device names."""
        valid_devices = ["mps", "cpu", "cuda"]

        # Valid devices should pass
        for device in valid_devices:
            config = AsrConfig(device=device)
            config.validate()  # Should not raise

        # Invalid device should fail
        config = AsrConfig()
        config.device = "invalid"

        with pytest.raises(ValueError, match="Invalid device"):
            config.validate()

    def test_validate_temperature_range(self):
        """Test temperature validation."""
        # Valid temperatures
        for temp in [0.0, 0.5, 1.0]:
            config = AsrConfig(temperature=temp)
            config.validate()  # Should not raise

        # Invalid temperatures
        for temp in [-0.1, 1.1, 2.0]:
            config = AsrConfig()
            config.temperature = temp

            with pytest.raises(ValueError, match="Temperature"):
                config.validate()

    def test_validate_caption_durations(self):
        """Test caption duration validation."""
        # Valid durations
        config = AsrConfig(min_caption_duration=1.0, max_caption_duration=6.0)
        config.validate()  # Should not raise

        # min > max should fail
        config = AsrConfig()
        config.min_caption_duration = 10.0
        config.max_caption_duration = 5.0

        with pytest.raises(ValueError, match="min_caption_duration"):
            config.validate()

        # Negative durations should fail
        config = AsrConfig()
        config.min_caption_duration = -1.0

        with pytest.raises(ValueError, match="positive"):
            config.validate()


class TestContractIC003:
    """
    Validate compliance with IC-003: ASR Config Interface.

    This test class ensures AsrConfig meets all requirements specified
    in Integration Contract IC-003.
    """

    def test_contract_ic003_required_methods(self):
        """Test all required methods exist."""
        config = AsrConfig()

        # Required methods per IC-003
        assert hasattr(config, "to_whisper_kwargs")
        assert callable(config.to_whisper_kwargs)

        assert hasattr(config, "validate")
        assert callable(config.validate)

        assert hasattr(config, "to_dict")
        assert callable(config.to_dict)

        assert hasattr(AsrConfig, "from_env")
        assert callable(AsrConfig.from_env)

    def test_contract_ic003_to_whisper_kwargs_return_type(self):
        """Test to_whisper_kwargs() returns dict."""
        config = AsrConfig()
        kwargs = config.to_whisper_kwargs()

        assert isinstance(kwargs, dict)

    def test_contract_ic003_to_whisper_kwargs_required_fields(self):
        """Test to_whisper_kwargs() includes all required fields."""
        config = AsrConfig()
        kwargs = config.to_whisper_kwargs()

        required_fields = [
            "path_or_hf_repo",
            "word_timestamps",
            "temperature",
            "fp16",
            "language",
        ]

        for field in required_fields:
            assert field in kwargs, f"Missing required field: {field}"

    def test_contract_ic003_validate_enforces_word_timestamps(self):
        """Test validate() enforces word_timestamps=True (critical IC-003 requirement)."""
        config = AsrConfig()
        config.word_timestamps = False

        with pytest.raises(ValueError, match="word_timestamps"):
            config.validate()

    def test_contract_ic003_backward_compatibility(self, monkeypatch):
        """Test backward compatibility with existing env vars."""
        env_vars = {
            "ASR_ENABLED": "true",
            "ASR_MODEL": "base",
            "ASR_LANGUAGE": "en",
            "ASR_DEVICE": "cpu",
            "ASR_WORD_TIMESTAMPS": "true",
            "ASR_TEMPERATURE": "0.0",
            "ASR_MAX_CAPTION_DURATION": "6.0",
            "ASR_MAX_CAPTION_CHARS": "100",
        }

        for var, value in env_vars.items():
            monkeypatch.setenv(var, value)

        # Should load without error
        config = AsrConfig.from_env()

        # Values should match
        assert config.enabled is True
        assert config.model == "base"
        assert config.language == "en"
        assert config.device == "cpu"

    def test_contract_ic003_no_docling_dependencies(self):
        """Test config does not depend on Docling imports."""
        config = AsrConfig()

        # Should not require Docling to instantiate
        assert config is not None

        # Should not have Docling-specific methods
        assert not hasattr(config, "to_docling_model_spec")

    def test_contract_ic003_integration_with_transcriber(self):
        """Test config integrates with custom whisper transcriber."""
        config = AsrConfig(model="turbo", language="en")
        kwargs = config.to_whisper_kwargs()

        # These kwargs should be directly usable by mlx_whisper.transcribe()
        # (We can't actually call mlx_whisper here without audio file)
        assert kwargs["word_timestamps"] is True
        assert kwargs["path_or_hf_repo"].startswith("mlx-community/")


class TestErrorHandling:
    """Test error handling and validation."""

    def test_invalid_model_raises_valueerror(self):
        """Test invalid model name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid model"):
            AsrConfig(model="nonexistent")

    def test_invalid_device_raises_valueerror(self):
        """Test invalid device raises ValueError."""
        with pytest.raises(ValueError, match="Invalid device"):
            AsrConfig(device="invalid")

    def test_invalid_temperature_raises_valueerror(self):
        """Test invalid temperature raises ValueError."""
        with pytest.raises(ValueError, match="Temperature"):
            AsrConfig(temperature=2.0)

    def test_word_timestamps_false_raises_valueerror(self):
        """Test word_timestamps=False raises ValueError."""
        with pytest.raises(ValueError, match="word_timestamps"):
            AsrConfig(word_timestamps=False)

    def test_from_env_invalid_values_uses_defaults(self, monkeypatch):
        """Test from_env() uses defaults for invalid values."""
        monkeypatch.setenv("ASR_MODEL", "invalid_model")

        # Should fall back to defaults and not crash
        config = AsrConfig.from_env()

        # Should use default model
        assert config.model == "turbo"
