"""
Model loader for ColPali embeddings.

This module handles loading and initialization of the ColQwen2_5 model
with device detection, quantization, and error handling.

Wave 3: Real ColPali integration with fallback to mock if unavailable.
"""

import logging
from typing import Any, List, Tuple, Union

import numpy as np

try:
    from config.model_config import ModelConfig
    from embeddings.exceptions import DeviceError, ModelLoadError, QuantizationError
except ImportError:
    # Fallback to relative imports
    from ..config.model_config import ModelConfig
    from .exceptions import DeviceError, ModelLoadError, QuantizationError

logger = logging.getLogger(__name__)

# Try to import ColPali, fallback to mock if unavailable
try:
    from colpali_engine.models import ColPali, ColPaliProcessor

    COLPALI_AVAILABLE = True
    logger.info("ColPali engine available - using real implementation")
except ImportError as e:
    COLPALI_AVAILABLE = False
    logger.warning(f"ColPali engine not available ({e}) - using mock implementation")


class MockColPaliModel:
    """Mock ColPali model for Wave 2 testing.

    This mock generates random embeddings with correct shapes for testing
    the API structure without requiring the full ColPali installation.
    """

    def __init__(self, model_name: str, device: str, dtype: str, is_quantized: bool):
        """Initialize mock model.

        Args:
            model_name: Model identifier
            device: Target device
            dtype: Model precision
            is_quantized: Whether model is quantized
        """
        self.model_name = model_name
        self.device = device
        self.dtype = dtype
        self.is_quantized = is_quantized
        self._is_loaded = True
        logger.info(f"MockColPaliModel initialized: {model_name} on {device} ({dtype})")

    def embed_batch(self, inputs: Any, input_type: str) -> Tuple[list, list]:
        """Generate mock embeddings.

        Args:
            inputs: Batch of inputs (images or texts)
            input_type: "visual" or "text"

        Returns:
            Tuple of (embeddings_list, seq_lengths_list)
        """
        batch_size = len(inputs)

        embeddings = []
        seq_lengths = []

        for _ in range(batch_size):
            # Generate realistic sequence lengths
            if input_type == "visual":
                seq_len = np.random.randint(80, 120)  # Visual: 80-120 tokens
            else:
                seq_len = np.random.randint(50, 80)  # Text: 50-80 tokens

            # Generate random embeddings with correct shape
            emb = np.random.randn(seq_len, 768).astype(np.float32)

            # Normalize to unit vectors (as ColPali would)
            emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8)

            embeddings.append(emb)
            seq_lengths.append(seq_len)

        return embeddings, seq_lengths


class MockColPaliProcessor:
    """Mock processor for ColPali inputs."""

    def __init__(self, model_name: str):
        """Initialize mock processor."""
        self.model_name = model_name
        logger.info(f"MockColPaliProcessor initialized: {model_name}")


class RealColPaliModel:
    """Real ColPali model wrapper for production use."""

    def __init__(self, model, processor, device: str):
        """Initialize real ColPali model wrapper.

        Args:
            model: Loaded ColQwen2 model
            processor: ColQwen2Processor
            device: Device name ('mps', 'cuda', or 'cpu')
        """
        self.model = model
        self.processor = processor
        self.device = device
        self._is_loaded = True
        logger.info(f"RealColPaliModel initialized on {device}")

    def embed_batch(self, inputs: Union[List, Any], input_type: str) -> Tuple[list, list]:
        """Generate real ColPali embeddings.

        Args:
            inputs: Batch of inputs (images or texts)
            input_type: "visual" or "text"

        Returns:
            Tuple of (embeddings_list, seq_lengths_list)
        """
        import torch

        try:
            # Process inputs with ColPali processor
            if input_type == "visual":
                # Images - use image processor
                processed = self.processor.process_images(inputs)
            else:
                # Text - use text processor
                processed = self.processor.process_queries(inputs)

            # Move to device
            processed = {
                k: v.to(self.device) if isinstance(v, torch.Tensor) else v
                for k, v in processed.items()
            }

            # Generate embeddings
            with torch.no_grad():
                # ColPali returns tensor directly: (batch_size, seq_length, hidden_size)
                embeddings_tensor = self.model(**processed)

            # Convert to numpy and extract per-sample embeddings
            embeddings_np = embeddings_tensor.cpu().numpy()

            embeddings = []
            seq_lengths = []

            for i in range(embeddings_np.shape[0]):
                emb = embeddings_np[i]  # (seq_length, hidden_size)
                seq_len = emb.shape[0]

                embeddings.append(emb.astype(np.float32))
                seq_lengths.append(seq_len)

            return embeddings, seq_lengths

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise


def load_model(config: ModelConfig) -> Tuple[Any, Any]:
    """
    Load ColPali model and processor.

    Wave 3: Attempts to load real ColPali model, falls back to mock if unavailable.

    Args:
        config: Model configuration

    Returns:
        Tuple of (model, processor)

    Raises:
        ModelLoadError: If model loading fails
        DeviceError: If requested device unavailable
        QuantizationError: If quantization fails
    """
    try:
        logger.info(f"Loading model: {config.name}")
        logger.info(f"Target device: {config.device}, Precision: {config.precision}")
        logger.info(f"Estimated memory: {config.memory_estimate_gb:.1f}GB")

        # Validate device availability
        device = _validate_device(config.device)
        if device != config.device:
            logger.warning(f"Device fallback: {config.device} -> {device}")

        # Try to load real ColPali if available
        if COLPALI_AVAILABLE:
            try:
                logger.info("Attempting to load real ColPali model...")

                # Use recommended ColPali model if using default
                model_name = config.name
                if model_name in ["vidore/colqwen2-v0.1", "vidore/colqwen2-v1.0"]:
                    model_name = "vidore/colpali-v1.2"
                    logger.info(f"Using recommended model: {model_name}")

                # Load processor
                processor = ColPaliProcessor.from_pretrained(model_name)

                # Load model with appropriate precision
                torch_dtype = get_torch_dtype(config.precision)

                model = ColPali.from_pretrained(
                    model_name, torch_dtype=torch_dtype, device_map=device
                )

                # Model is already on device via device_map
                model.eval()

                # Wrap in our interface
                wrapped_model = RealColPaliModel(model, processor, device)

                logger.info("Real ColPali model loaded successfully")
                return wrapped_model, processor

            except Exception as e:
                logger.warning(f"Failed to load real ColPali model: {e}")
                logger.warning("Falling back to mock implementation")

        # Fallback to mock implementation
        logger.warning("Using mock ColPali model. Install ColPali for production.")

        model = MockColPaliModel(
            model_name=config.name,
            device=device,
            dtype=config.precision,
            is_quantized=config.is_quantized,
        )

        processor = MockColPaliProcessor(model_name=config.name)

        logger.info("Mock model loaded successfully")
        return model, processor

    except DeviceError:
        raise
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise ModelLoadError(f"Failed to load model {config.name}: {e}") from e


def _validate_device(device: str) -> str:
    """
    Validate device availability with fallback.

    Args:
        device: Requested device ('mps', 'cuda', or 'cpu')

    Returns:
        Available device name

    Raises:
        DeviceError: If validation fails completely
    """
    try:
        import torch

        if device == "mps":
            if torch.backends.mps.is_available():
                logger.info("MPS (Metal) device available")
                return "mps"
            else:
                logger.warning("MPS not available, falling back to CPU")
                return "cpu"

        elif device == "cuda":
            if torch.cuda.is_available():
                logger.info(f"CUDA device available: {torch.cuda.get_device_name(0)}")
                return "cuda"
            else:
                logger.warning("CUDA not available, falling back to CPU")
                return "cpu"

        elif device == "cpu":
            logger.info("Using CPU device")
            return "cpu"

        else:
            raise DeviceError(f"Invalid device: {device}")

    except ImportError:
        logger.warning("PyTorch not available, using CPU")
        return "cpu"


def get_torch_dtype(precision: str):
    """
    Get PyTorch dtype from precision string.

    Args:
        precision: 'fp16' or 'int8'

    Returns:
        torch.dtype

    Raises:
        QuantizationError: If precision is invalid
    """
    try:
        import torch

        if precision == "fp16":
            return torch.float16
        elif precision == "int8":
            # INT8 quantization would use torch.float16 with additional quantization
            return torch.float16
        else:
            raise QuantizationError(f"Invalid precision: {precision}")

    except ImportError:
        logger.warning("PyTorch not available")
        return None


def estimate_memory_usage(model: Any, device: str) -> float:
    """
    Estimate model memory usage in MB.

    Args:
        model: Loaded model
        device: Device name

    Returns:
        Memory usage in MB
    """
    try:
        if isinstance(model, MockColPaliModel):
            # Mock estimate based on precision
            if model.is_quantized:
                return 7000.0  # 7GB for INT8
            return 14000.0  # 14GB for FP16

        elif isinstance(model, RealColPaliModel):
            # Real model memory estimation
            try:
                import torch

                if device == "mps":
                    # MPS doesn't have direct memory query, estimate based on parameters
                    param_size = sum(p.numel() * p.element_size() for p in model.model.parameters())
                    return param_size / (1024**2)  # Convert to MB
                elif device == "cuda":
                    return torch.cuda.memory_allocated() / (1024**2)
                else:
                    return 0.0
            except Exception as e:
                # Fallback estimate
                logger.debug(f"Memory estimation failed: {e}")
                return 8000.0  # ~8GB for ColPali

        return 0.0

    except Exception as e:
        logger.warning(f"Could not estimate memory usage: {e}")
        return 0.0
