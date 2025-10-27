# Whisper Integration Tests

This directory contains tests for the custom MLX-Whisper integration that replaces Docling's audio transcription system.

## Test Organization

### Unit Tests
- `test_transcriber.py` - Core transcription functionality (Agent-CoreWhisper)
- `test_output_validator.py` - Output validation utilities
- `../config/test_asr_config.py` - Configuration management (Agent-ConfigSystem)

### Integration Tests
- `../../integration/test_audio_routing.py` - Audio file routing (Wave 2)
- `../../integration/test_audio_end_to_end.py` - Full pipeline (Wave 2)

### Contract Validation
All tests validate compliance with Integration Contracts:
- **IC-001**: Whisper Output Format (`test_transcriber.py::TestContractIC001`)
- **IC-003**: ASR Config Interface (`test_asr_config.py::TestContractIC003`)

## Running Tests

### Run all whisper tests:
```bash
pytest tests/processing/whisper/ -v
```

### Run specific test class:
```bash
pytest tests/processing/whisper/test_transcriber.py::TestTranscribeAudio -v
```

### Run with coverage:
```bash
pytest tests/processing/whisper/ --cov=src/processing/whisper --cov-report=term
```

### Run contract validation only:
```bash
pytest tests/processing/whisper/ -k "contract" -v
```

## Test Fixtures

### Required Fixtures
- `tests/fixtures/sample.mp3` - Sample audio file for transcription testing
- `tests/fixtures/sample.pdf` - For format validation (should reject)

### Shared Fixtures (`conftest.py`)
- `sample_audio_file` - Path to sample MP3
- `sample_audio_file_path` - Validated Path object
- `nonexistent_audio_file` - For error testing
- `unsupported_format_file` - For format validation

## Integration Contracts

### IC-001: Whisper Output Format
**File**: `.context-kit/orchestration/custom-whisper-replacement/integration-contracts/01-whisper-output-format.md`

**Tests**: `test_transcriber.py::TestContractIC001`

**Requirements**:
- Must return word-level timestamps in every segment
- Must include segment start/end times
- Must provide full transcript text
- Must include audio duration

### IC-003: ASR Config Interface
**File**: `.context-kit/orchestration/custom-whisper-replacement/integration-contracts/03-asr-config-interface.md`

**Tests**: `test_asr_config.py::TestContractIC003`

**Requirements**:
- Must provide `to_whisper_kwargs()` method
- Must enforce `word_timestamps=True`
- Must support all existing environment variables
- Must remove Docling dependencies

## Test Coverage Goals

- **Unit tests**: > 90% coverage
- **Integration tests**: All critical paths
- **Contract tests**: 100% requirement coverage

## Writing New Tests

### Test Naming Convention
```python
def test_{component}_{behavior}():
    """Test {component} {behavior description}."""
```

### Contract Validation Tests
```python
class TestContract{ID}:
    """Validate IC-{ID}: {Contract Name}."""

    def test_contract_{id}_{requirement}(self):
        """Test {specific requirement from contract}."""
```

### Example Test Structure
```python
def test_transcribe_audio_success(sample_audio_file_path):
    """Test successful audio transcription."""
    # Arrange
    file_path = str(sample_audio_file_path)

    # Act
    result = transcribe_audio(file_path)

    # Assert
    assert "text" in result
    assert len(result["segments"]) > 0
```

## Common Test Patterns

### Testing Error Handling
```python
def test_missing_file_raises_error():
    """Test FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="not found"):
        transcribe_audio("/nonexistent/file.mp3")
```

### Testing Configuration
```python
def test_config_from_env(monkeypatch):
    """Test loading config from environment."""
    monkeypatch.setenv("ASR_MODEL", "base")
    config = AsrConfig.from_env()
    assert config.model == "base"
```

### Testing Contract Compliance
```python
def test_contract_ic001_word_timestamps(sample_audio_file_path):
    """Test all segments have word-level timestamps (IC-001)."""
    result = transcribe_audio(str(sample_audio_file_path))

    for segment in result["segments"]:
        assert "words" in segment
        assert len(segment["words"]) > 0
```

## Troubleshooting

### Test Skips
If tests are skipped due to missing fixtures:
```bash
# Check if sample audio exists
ls -la tests/fixtures/sample.mp3
```

### Import Errors
If you see import errors:
```bash
# Run tests from project root
cd /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch
pytest tests/processing/whisper/
```

### MLX-Whisper Not Installed
Some tests require mlx-whisper:
```bash
pip install mlx-whisper
```

## Wave 1 Status

- [x] Agent-CoreWhisper: transcriber.py unit tests
- [x] Agent-ConfigSystem: AsrConfig unit tests
- [x] Test infrastructure created
- [x] Contract validation tests implemented
- [ ] Gate 1: All tests passing

## Next Steps (Wave 2)

1. Agent-AudioParser will add:
   - `test_audio_parser.py`
   - `test_transcript_formatter.py`
   - `test_metadata_builder.py`

2. Agent-IntegrationBridge will add:
   - `../../integration/test_audio_routing.py`

3. Agent-Testing will add:
   - Integration tests
   - End-to-end pipeline tests

## References

- [Orchestration Plan](/.context-kit/orchestration/custom-whisper-replacement/orchestration-plan.md)
- [Integration Contracts](/.context-kit/orchestration/custom-whisper-replacement/integration-contracts/)
- [Validation Strategy](/.context-kit/orchestration/custom-whisper-replacement/validation-strategy.md)
