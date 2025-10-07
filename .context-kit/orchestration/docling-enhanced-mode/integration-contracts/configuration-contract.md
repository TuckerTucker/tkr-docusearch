# Configuration Contract

**Contract ID**: CONFIG-001
**Version**: 1.0
**Status**: Specification
**Owner**: config-agent
**Consumers**: structure-agent, chunking-agent, integration-agent

## Purpose

Define configuration interface for Docling Enhanced Mode features, including feature flags, pipeline options, and runtime settings.

## Configuration Schema

### EnhancedModeConfig Dataclass

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class ChunkingStrategy(Enum):
    """Chunking strategy selection."""
    LEGACY = "legacy"      # Word-based sliding window
    HYBRID = "hybrid"      # Document-aware hybrid chunker

@dataclass
class EnhancedModeConfig:
    """Configuration for Docling enhanced mode features."""

    # Feature flags (all default to True)
    enable_table_structure: bool = True
    enable_picture_classification: bool = True
    enable_code_enrichment: bool = False  # Optional, slow
    enable_formula_enrichment: bool = False  # Optional, slow

    # Chunking configuration
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.HYBRID
    max_chunk_tokens: int = 512
    min_chunk_tokens: int = 100
    merge_peer_chunks: bool = True

    # Pipeline options
    table_structure_mode: str = "accurate"  # "fast" or "accurate"
    images_scale: float = 2.0
    generate_page_images: bool = True
    generate_picture_images: bool = True

    # Performance limits
    max_structure_size_kb: int = 100  # Max size of structure metadata

    @classmethod
    def from_env(cls) -> "EnhancedModeConfig":
        """Load configuration from environment variables."""
        import os

        return cls(
            enable_table_structure=os.getenv("ENABLE_TABLE_STRUCTURE", "true").lower() == "true",
            enable_picture_classification=os.getenv("ENABLE_PICTURE_CLASSIFICATION", "true").lower() == "true",
            enable_code_enrichment=os.getenv("ENABLE_CODE_ENRICHMENT", "false").lower() == "true",
            enable_formula_enrichment=os.getenv("ENABLE_FORMULA_ENRICHMENT", "false").lower() == "true",
            chunking_strategy=ChunkingStrategy(os.getenv("CHUNKING_STRATEGY", "hybrid")),
            max_chunk_tokens=int(os.getenv("MAX_CHUNK_TOKENS", "512")),
            min_chunk_tokens=int(os.getenv("MIN_CHUNK_TOKENS", "100")),
            merge_peer_chunks=os.getenv("MERGE_PEER_CHUNKS", "true").lower() == "true",
            table_structure_mode=os.getenv("TABLE_STRUCTURE_MODE", "accurate"),
            images_scale=float(os.getenv("IMAGES_SCALE", "2.0")),
        )
```

## Environment Variables

### Feature Flags

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_TABLE_STRUCTURE` | boolean | `true` | Enable table structure recognition |
| `ENABLE_PICTURE_CLASSIFICATION` | boolean | `true` | Enable image type classification |
| `ENABLE_CODE_ENRICHMENT` | boolean | `false` | Enable code block language detection |
| `ENABLE_FORMULA_ENRICHMENT` | boolean | `false` | Enable formula LaTeX extraction |

### Chunking Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CHUNKING_STRATEGY` | enum | `hybrid` | Chunking strategy: `legacy` or `hybrid` |
| `MAX_CHUNK_TOKENS` | int | `512` | Maximum tokens per chunk |
| `MIN_CHUNK_TOKENS` | int | `100` | Minimum tokens per chunk |
| `MERGE_PEER_CHUNKS` | boolean | `true` | Merge adjacent small chunks |

### Pipeline Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TABLE_STRUCTURE_MODE` | enum | `accurate` | TableFormer mode: `fast` or `accurate` |
| `IMAGES_SCALE` | float | `2.0` | Image generation scale factor |

## File Locations

### Primary
- `src/config/processing_config.py` - Configuration classes and loaders

### Environment Templates
- `.env.template` - Root environment template
- `docker/.env.template` - Docker environment template

## Usage Examples

### Loading Configuration

```python
from src.config.processing_config import EnhancedModeConfig

# Load from environment
config = EnhancedModeConfig.from_env()

# Access settings
if config.enable_table_structure:
    print(f"Table structure enabled with mode: {config.table_structure_mode}")

# Check chunking strategy
if config.chunking_strategy == ChunkingStrategy.HYBRID:
    print(f"Using hybrid chunking with max {config.max_chunk_tokens} tokens")
```

### Creating PdfPipelineOptions

```python
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

def create_pipeline_options(config: EnhancedModeConfig) -> PdfPipelineOptions:
    """Create Docling pipeline options from config."""
    options = PdfPipelineOptions()

    # Structure features
    options.do_table_structure = config.enable_table_structure
    options.do_picture_classification = config.enable_picture_classification
    options.do_code_enrichment = config.enable_code_enrichment
    options.do_formula_enrichment = config.enable_formula_enrichment

    # Table structure mode
    if config.enable_table_structure:
        options.table_structure_options.mode = (
            TableFormerMode.ACCURATE if config.table_structure_mode == "accurate"
            else TableFormerMode.FAST
        )

    # Image options
    options.generate_page_images = config.generate_page_images
    options.generate_picture_images = config.generate_picture_images
    options.images_scale = config.images_scale

    return options
```

## Validation Requirements

### Config Validation

```python
def validate_config(config: EnhancedModeConfig) -> None:
    """Validate configuration values."""
    # Token limits
    assert 10 <= config.min_chunk_tokens <= 1000, "min_chunk_tokens out of range"
    assert 100 <= config.max_chunk_tokens <= 4096, "max_chunk_tokens out of range"
    assert config.min_chunk_tokens < config.max_chunk_tokens, "min must be < max"

    # Image scale
    assert 0.5 <= config.images_scale <= 4.0, "images_scale out of range"

    # Table mode
    assert config.table_structure_mode in ["fast", "accurate"], "Invalid table mode"
```

## Consumer Responsibilities

### structure-agent
- Read `enable_table_structure`, `enable_picture_classification`, `enable_code_enrichment`, `enable_formula_enrichment`
- Create PdfPipelineOptions based on config
- Respect `max_structure_size_kb` limit

### chunking-agent
- Read `chunking_strategy`, `max_chunk_tokens`, `min_chunk_tokens`, `merge_peer_chunks`
- Initialize HybridChunker with correct parameters
- Fall back to legacy if hybrid fails

### integration-agent
- Load config at startup
- Pass config to all processing components
- Log effective configuration
- Validate config before processing

## Performance Implications

### Feature Combinations & Expected Overhead

| Features Enabled | Processing Overhead | Storage Overhead |
|------------------|--------------------|--------------------|
| Structure only | +5-10% | +10-15% |
| Structure + Classification | +10-15% | +15-20% |
| Structure + Chunking | +8-12% | +10-15% |
| All (recommended) | +12-18% | +20-25% |
| All + Code + Formula | +30-40% | +25-30% |

### Recommended Configurations

**Fast Mode** (minimal overhead):
```bash
ENABLE_TABLE_STRUCTURE=false
ENABLE_PICTURE_CLASSIFICATION=false
CHUNKING_STRATEGY=legacy
```

**Balanced Mode** (recommended default):
```bash
ENABLE_TABLE_STRUCTURE=true
ENABLE_PICTURE_CLASSIFICATION=true
CHUNKING_STRATEGY=hybrid
TABLE_STRUCTURE_MODE=accurate
```

**Quality Mode** (maximum quality):
```bash
ENABLE_TABLE_STRUCTURE=true
ENABLE_PICTURE_CLASSIFICATION=true
ENABLE_CODE_ENRICHMENT=true
ENABLE_FORMULA_ENRICHMENT=true
CHUNKING_STRATEGY=hybrid
TABLE_STRUCTURE_MODE=accurate
```

## Testing Contract

### Unit Tests Required
- ✅ Config loads from environment variables
- ✅ Config validation catches invalid values
- ✅ Default values are correct
- ✅ PdfPipelineOptions created correctly
- ✅ ChunkingStrategy enum works

### Integration Tests Required
- ✅ Config changes affect processing behavior
- ✅ Feature flags enable/disable correctly
- ✅ Invalid config causes graceful failure

## Version History

- **1.0** (2025-10-07): Initial specification
