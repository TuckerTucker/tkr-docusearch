# ASR Configuration Interface Contract

**Provider**: config-agent
**Consumers**: parser-agent (ASR implementation)
**File**: `src/config/processing_config.py`

## Interface Specification

### New Dataclass: AsrConfig

**Purpose**: Centralized configuration for Whisper ASR audio processing.

**Definition**:
```python
from dataclasses import dataclass
from typing import Optional, Literal

@dataclass
class AsrConfig:
    """Configuration for Automatic Speech Recognition (Whisper).

    Attributes:
        enabled: Whether ASR processing is enabled
        model: Whisper model to use (turbo, base, small, medium, large)
        language: Language code or "auto" for detection
        device: Compute device (mps, cpu, cuda)
        word_timestamps: Enable word-level timestamps
        temperature: Sampling temperature for generation
        max_time_chunk: Maximum audio chunk duration (seconds)
    """

    enabled: bool = True
    model: Literal["turbo", "base", "small", "medium", "large"] = "turbo"
    language: str = "en"  # ISO 639-1 code or "auto"
    device: Literal["mps", "cpu", "cuda"] = "mps"
    word_timestamps: bool = True
    temperature: float = 0.0  # 0.0 = deterministic
    max_time_chunk: float = 30.0

    def __post_init__(self):
        """Validate configuration."""
        if self.model not in ["turbo", "base", "small", "medium", "large"]:
            raise ValueError(f"Invalid model: {self.model}")

        if self.device not in ["mps", "cpu", "cuda"]:
            raise ValueError(f"Invalid device: {self.device}")

        if self.temperature < 0.0 or self.temperature > 1.0:
            raise ValueError(f"Temperature must be 0.0-1.0, got {self.temperature}")

        if self.max_time_chunk <= 0:
            raise ValueError(f"max_time_chunk must be positive, got {self.max_time_chunk}")

    def to_docling_model_spec(self):
        """Convert to Docling ASR model specification.

        Returns:
            InlineAsrNativeWhisperOptions instance
        """
        from docling.datamodel.pipeline_options_asr_model import (
            InlineAsrNativeWhisperOptions
        )

        # Map our model names to Docling repo_ids
        model_map = {
            "turbo": "openai/whisper-large-v3-turbo",
            "base": "openai/whisper-base",
            "small": "openai/whisper-small",
            "medium": "openai/whisper-medium",
            "large": "openai/whisper-large-v3"
        }

        return InlineAsrNativeWhisperOptions(
            repo_id=model_map[self.model],
            language=self.language if self.language != "auto" else None,
            word_timestamps=self.word_timestamps,
            temperature=self.temperature,
            max_time_chunk=self.max_time_chunk
        )

    @classmethod
    def from_env(cls) -> "AsrConfig":
        """Load configuration from environment variables.

        Environment Variables:
            ASR_ENABLED: Enable ASR (default: true)
            ASR_MODEL: Model name (default: turbo)
            ASR_LANGUAGE: Language code (default: en)
            ASR_DEVICE: Compute device (default: mps)
            ASR_WORD_TIMESTAMPS: Enable word timestamps (default: true)
            ASR_TEMPERATURE: Sampling temperature (default: 0.0)
            ASR_MAX_TIME_CHUNK: Max chunk duration (default: 30.0)

        Returns:
            AsrConfig instance
        """
        import os

        return cls(
            enabled=os.getenv("ASR_ENABLED", "true").lower() == "true",
            model=os.getenv("ASR_MODEL", "turbo"),
            language=os.getenv("ASR_LANGUAGE", "en"),
            device=os.getenv("ASR_DEVICE", "mps"),
            word_timestamps=os.getenv("ASR_WORD_TIMESTAMPS", "true").lower() == "true",
            temperature=float(os.getenv("ASR_TEMPERATURE", "0.0")),
            max_time_chunk=float(os.getenv("ASR_MAX_TIME_CHUNK", "30.0"))
        )
```

## Contract Requirements

### Configuration Validation:
- All fields must be validated in `__post_init__()`
- Invalid values must raise `ValueError` with clear message
- No silent failures or defaults on invalid input

### Docling Integration:
- `to_docling_model_spec()` MUST return valid `InlineAsrNativeWhisperOptions`
- Model name mapping MUST be correct
- Language code MUST follow Docling conventions

### Environment Variable Loading:
- `from_env()` MUST handle missing variables gracefully
- Default values MUST match dataclass defaults
- Boolean parsing MUST accept "true"/"false" (case-insensitive)
- Numeric parsing MUST handle conversion errors

## Model Specifications

### Whisper Models:

| Model  | Size | Speed | Accuracy | Repo ID |
|--------|------|-------|----------|---------|
| turbo  | 809M | Fast  | Good     | openai/whisper-large-v3-turbo |
| base   | 74M  | Fastest | Basic  | openai/whisper-base |
| small  | 244M | Fast    | Good   | openai/whisper-small |
| medium | 769M | Medium  | Better | openai/whisper-medium |
| large  | 1550M | Slow   | Best   | openai/whisper-large-v3 |

**Default: turbo** (best balance of speed/accuracy)

### Device Support:

| Device | Platform | Performance | Availability |
|--------|----------|-------------|--------------|
| mps    | M1/M2/M3 Mac | 10-20x faster | macOS 12.3+ |
| cuda   | NVIDIA GPU   | 20-50x faster | Linux/Windows with CUDA |
| cpu    | Any          | Baseline (1x) | Always available |

**Default: mps** (optimized for M1/M2/M3 Macs)

### Language Codes:

Common codes: `en` (English), `es` (Spanish), `fr` (French), `de` (German), `zh` (Chinese)
Auto-detection: `"auto"` (slower, but detects language automatically)

## Data Flow

```
Environment variables →
AsrConfig.from_env() →
AsrConfig instance →
Parser agent →
to_docling_model_spec() →
Docling ASR pipeline
```

## Error Handling Contract

### Configuration Errors:
```python
class AsrConfigError(Exception):
    """Invalid ASR configuration."""
    pass
```

Raise `AsrConfigError` for:
- Invalid model name
- Invalid device type
- Invalid temperature range
- Invalid chunk duration

### Fallback Behavior:
If ASR is disabled (`enabled=False`):
- Audio files (.mp3, .wav) should still be processed
- But use existing VTT transcript if available
- Or skip audio processing with warning

## Performance Contract

- Configuration loading: <10ms
- Validation overhead: <1ms
- No network calls during config creation
- Thread-safe: Yes (immutable dataclass)

## Testing Contract

Config agent MUST implement:
- Unit test: default configuration values
- Unit test: from_env() with all variables set
- Unit test: from_env() with missing variables (uses defaults)
- Unit test: validation rejects invalid models
- Unit test: validation rejects invalid devices
- Unit test: validation rejects invalid temperature
- Unit test: to_docling_model_spec() returns correct type
- Unit test: model name mapping is correct

## Validation Checklist

- [ ] AsrConfig dataclass defined
- [ ] All fields have correct types and defaults
- [ ] __post_init__() validates all fields
- [ ] from_env() loads from environment variables
- [ ] to_docling_model_spec() converts correctly
- [ ] Model mapping table is accurate
- [ ] Error handling for invalid configs
- [ ] Tests cover all validation scenarios
- [ ] Documentation includes model comparison
- [ ] Environment variable docs complete

## Integration Notes

**Parser Agent**: Will import AsrConfig and call from_env() or use defaults
**No dependencies**: AsrConfig can be implemented independently
**Docling import**: Only imported in to_docling_model_spec() method (lazy)
**Backward compatible**: No changes to existing config classes
