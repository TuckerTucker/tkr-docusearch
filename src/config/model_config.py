"""
Model configuration for ColPali embeddings.

This module defines configuration for the ColQwen2_5 model including
device selection, precision, and batch sizes.
"""

from dataclasses import dataclass
from typing import Literal
import os


@dataclass
class ModelConfig:
    """ColPali model configuration.

    Attributes:
        name: Model identifier on HuggingFace
        precision: Model precision (fp16 or int8)
        device: Compute device (mps, cuda, or cpu)
        batch_size_visual: Number of images to process per batch
        batch_size_text: Number of text chunks to process per batch
        cache_dir: Directory for model caching
        auto_fallback: Automatically fallback to CPU if device unavailable
    """

    # Model selection
    name: str = os.getenv('MODEL_NAME', 'vidore/colqwen2-v0.1')
    precision: Literal['fp16', 'int8'] = os.getenv('MODEL_PRECISION', 'fp16')  # type: ignore

    # Device selection
    device: Literal['mps', 'cuda', 'cpu'] = os.getenv('DEVICE', 'mps')  # type: ignore

    # Batch sizes
    batch_size_visual: int = int(os.getenv('BATCH_SIZE_VISUAL', '4'))
    batch_size_text: int = int(os.getenv('BATCH_SIZE_TEXT', '8'))

    # Cache directory
    cache_dir: str = os.getenv('MODELS_CACHE', '/models')

    # Auto-detect device if specified device unavailable
    auto_fallback: bool = True

    def __post_init__(self):
        """Validate configuration and detect available device."""
        if self.precision not in ['fp16', 'int8']:
            raise ValueError(f"Invalid precision: {self.precision}. Must be 'fp16' or 'int8'")
        if self.device not in ['mps', 'cuda', 'cpu']:
            raise ValueError(f"Invalid device: {self.device}. Must be 'mps', 'cuda', or 'cpu'")

        # Check device availability and fallback
        if self.auto_fallback:
            self.device = self._detect_device()

    def _detect_device(self) -> str:
        """Detect available device with fallback.

        Returns:
            Available device name ('mps', 'cuda', or 'cpu')
        """
        try:
            import torch

            # Check requested device
            if self.device == 'mps' and torch.backends.mps.is_available():
                return 'mps'
            elif self.device == 'cuda' and torch.cuda.is_available():
                return 'cuda'
            else:
                if self.device != 'cpu':
                    print(f"Warning: Requested device '{self.device}' not available, falling back to CPU")
                return 'cpu'
        except ImportError:
            print("Warning: PyTorch not available, using CPU device")
            return 'cpu'

    @property
    def memory_estimate_gb(self) -> float:
        """Estimate memory usage based on model and precision.

        Returns:
            Estimated memory in GB
        """
        base_model_size = 14.0  # ColNomic 7B ~14GB FP16
        if self.precision == 'int8':
            return base_model_size / 2  # ~7GB INT8
        return base_model_size

    @property
    def is_quantized(self) -> bool:
        """Check if model uses quantization.

        Returns:
            True if INT8 quantization enabled
        """
        return self.precision == 'int8'

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return {
            'name': self.name,
            'precision': self.precision,
            'device': self.device,
            'batch_size_visual': self.batch_size_visual,
            'batch_size_text': self.batch_size_text,
            'cache_dir': self.cache_dir,
            'memory_estimate_gb': self.memory_estimate_gb,
            'is_quantized': self.is_quantized,
        }

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"ModelConfig(name='{self.name}', "
            f"precision='{self.precision}', "
            f"device='{self.device}', "
            f"batch_visual={self.batch_size_visual}, "
            f"batch_text={self.batch_size_text}, "
            f"memory={self.memory_estimate_gb:.1f}GB)"
        )
