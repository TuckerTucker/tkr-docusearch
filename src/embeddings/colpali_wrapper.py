"""
ColPali engine wrapper for multi-vector embeddings and late interaction.

This module provides the main ColPaliEngine class for generating embeddings
and computing late interaction scores using the MaxSim algorithm.

NOTE: Wave 2 implementation uses mock model. Real ColPali integration in Wave 3+.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

try:
    from config.model_config import ModelConfig
    from embeddings.exceptions import EmbeddingGenerationError, ScoringError
    from embeddings.model_loader import estimate_memory_usage, load_model
    from embeddings.scoring import batch_maxsim_scores, validate_embedding_shape
    from embeddings.types import BatchEmbeddingOutput, EmbeddingOutput, ScoringOutput
except ImportError:
    # Fallback to relative imports
    from ..config.model_config import ModelConfig
    from .exceptions import EmbeddingGenerationError, ScoringError
    from .model_loader import estimate_memory_usage, load_model
    from .scoring import batch_maxsim_scores, validate_embedding_shape
    from .types import BatchEmbeddingOutput, EmbeddingOutput, ScoringOutput

logger = logging.getLogger(__name__)


class ColPaliEngine:
    """ColPali engine wrapper for multi-vector embeddings and late interaction."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        precision: Optional[str] = None,
        cache_dir: Optional[str] = None,
        quantization: Optional[str] = None,
        config: Optional[ModelConfig] = None,
    ):
        """
        Initialize ColPali model and processor.

        Args:
            model_name: HuggingFace model identifier
            device: Target device (mps for M1, cuda for NVIDIA, cpu for fallback)
            precision: Model precision (fp16 or int8)
            cache_dir: Directory for model caching
            quantization: Quantization mode (None, "int8")
            config: Pre-configured ModelConfig (overrides other args)

        Raises:
            ModelLoadError: If model loading fails
            DeviceError: If requested device unavailable
        """
        # Create or use provided config
        if config is None:
            self.config = ModelConfig(
                name=model_name or "vidore/colqwen2-v0.1",
                device=device or "mps",
                precision=precision or "fp16",
                cache_dir=cache_dir or "/models",
            )
            # Apply quantization if specified
            if quantization == "int8":
                self.config.precision = "int8"
        else:
            self.config = config

        logger.info(f"Initializing ColPaliEngine with config: {self.config}")

        # Load model and processor
        self.model, self.processor = load_model(self.config)

        # Track memory usage
        self._memory_allocated = estimate_memory_usage(self.model, self.config.device)

        logger.info(f"ColPaliEngine initialized successfully")
        logger.info(f"Memory allocated: {self._memory_allocated:.1f}MB")

    def embed_images(
        self, images: List[Image.Image], batch_size: Optional[int] = None
    ) -> BatchEmbeddingOutput:
        """
        Generate multi-vector embeddings for image batch.

        Args:
            images: List of PIL Images (document pages)
            batch_size: Number of images to process at once (uses config default if None)

        Returns:
            BatchEmbeddingOutput with:
            - embeddings: List of (seq_length, 768) arrays
            - cls_tokens: (batch_size, 768) representative vectors
            - seq_lengths: Token counts (typically 80-120 per page)
            - input_type: "visual"
            - batch_processing_time_ms: Total batch time

        Raises:
            ValueError: If images list is empty
            EmbeddingGenerationError: If embedding generation fails

        Performance:
            FP16: ~6s per image on M1
            INT8: ~3s per image on M1
        """
        if not images:
            raise ValueError("Images list cannot be empty")

        if batch_size is None:
            batch_size = self.config.batch_size_visual

        logger.info(f"Embedding {len(images)} images with batch_size={batch_size}")
        start_time = time.time()

        try:
            # Process in batches
            all_embeddings = []
            all_seq_lengths = []

            for i in range(0, len(images), batch_size):
                batch = images[i : i + batch_size]
                logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch)} images")

                # Generate embeddings (mock in Wave 2)
                embeddings, seq_lengths = self.model.embed_batch(batch, "visual")

                all_embeddings.extend(embeddings)
                all_seq_lengths.extend(seq_lengths)

            # Extract CLS tokens (first token of each embedding)
            cls_tokens = np.array([emb[0] for emb in all_embeddings])

            # Calculate processing time
            elapsed_ms = (time.time() - start_time) * 1000

            logger.info(f"Image embedding complete: {len(images)} images in {elapsed_ms:.1f}ms")
            logger.info(f"Average seq_length: {np.mean(all_seq_lengths):.1f} tokens")

            return BatchEmbeddingOutput(
                embeddings=all_embeddings,
                cls_tokens=cls_tokens,
                seq_lengths=all_seq_lengths,
                input_type="visual",
                batch_processing_time_ms=elapsed_ms,
            )

        except Exception as e:
            logger.error(f"Image embedding failed: {e}")
            raise EmbeddingGenerationError(f"Failed to embed images: {e}") from e

    def embed_texts(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> BatchEmbeddingOutput:
        """
        Generate multi-vector embeddings for text batch.

        Args:
            texts: List of text chunks (avg 250 words)
            batch_size: Number of texts to process at once (uses config default if None)

        Returns:
            BatchEmbeddingOutput with:
            - embeddings: List of (seq_length, 768) arrays
            - cls_tokens: (batch_size, 768) representative vectors
            - seq_lengths: Token counts (typically 50-80 per chunk)
            - input_type: "text"
            - batch_processing_time_ms: Total batch time

        Raises:
            ValueError: If texts list is empty
            EmbeddingGenerationError: If embedding generation fails

        Performance:
            FP16: ~6s per chunk on M1
            INT8: ~3s per chunk on M1
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        # Validate non-empty texts
        if any(not text.strip() for text in texts):
            raise ValueError("Text chunks cannot be empty strings")

        if batch_size is None:
            batch_size = self.config.batch_size_text

        logger.info(f"Embedding {len(texts)} texts with batch_size={batch_size}")
        start_time = time.time()

        try:
            # Process in batches
            all_embeddings = []
            all_seq_lengths = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch)} texts")

                # Generate embeddings (mock in Wave 2)
                embeddings, seq_lengths = self.model.embed_batch(batch, "text")

                all_embeddings.extend(embeddings)
                all_seq_lengths.extend(seq_lengths)

            # Extract CLS tokens (first token of each embedding)
            cls_tokens = np.array([emb[0] for emb in all_embeddings])

            # Calculate processing time
            elapsed_ms = (time.time() - start_time) * 1000

            logger.info(f"Text embedding complete: {len(texts)} texts in {elapsed_ms:.1f}ms")
            logger.info(f"Average seq_length: {np.mean(all_seq_lengths):.1f} tokens")

            return BatchEmbeddingOutput(
                embeddings=all_embeddings,
                cls_tokens=cls_tokens,
                seq_lengths=all_seq_lengths,
                input_type="text",
                batch_processing_time_ms=elapsed_ms,
            )

        except Exception as e:
            logger.error(f"Text embedding failed: {e}")
            raise EmbeddingGenerationError(f"Failed to embed texts: {e}") from e

    def embed_query(self, query: str) -> EmbeddingOutput:
        """
        Generate multi-vector embedding for search query.

        Args:
            query: Natural language search query

        Returns:
            EmbeddingOutput with:
            - embeddings: (seq_length, 768) multi-vector
            - cls_token: (768,) representative vector
            - seq_length: Query token count (typically 10-30)
            - input_type: "text"
            - processing_time_ms: Generation time

        Raises:
            ValueError: If query is empty
            EmbeddingGenerationError: If embedding generation fails

        Performance:
            <100ms for typical queries on M1
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")

        logger.info(f"Embedding query: '{query[:50]}...'")
        start_time = time.time()

        try:
            # Embed as single-item batch
            batch_output = self.embed_texts([query], batch_size=1)

            elapsed_ms = (time.time() - start_time) * 1000

            return EmbeddingOutput(
                embeddings=batch_output["embeddings"][0],
                cls_token=batch_output["cls_tokens"][0],
                seq_length=batch_output["seq_lengths"][0],
                input_type="text",
                processing_time_ms=elapsed_ms,
            )

        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise EmbeddingGenerationError(f"Failed to embed query: {e}") from e

    def score_multi_vector(
        self,
        query_embeddings: np.ndarray,
        document_embeddings: List[np.ndarray],
        use_gpu: bool = True,
    ) -> ScoringOutput:
        """
        Late interaction scoring using MaxSim algorithm.

        Computes maximum similarity between each query token and all document
        tokens, then sums across query tokens.

        Args:
            query_embeddings: Query multi-vector, shape (query_tokens, 768)
            document_embeddings: List of document multi-vectors, each (doc_tokens, 768)
            use_gpu: Use GPU for scoring (faster)

        Returns:
            ScoringOutput with:
            - scores: List of MaxSim scores (0-1 range, higher = better match)
            - scoring_time_ms: Time to score all documents
            - num_candidates: len(document_embeddings)

        Algorithm:
            For each document:
                score = sum over query_tokens of max(cosine_sim(q_token, d_token))

        Raises:
            ValueError: If embedding shapes incompatible
            ScoringError: If scoring computation fails

        Performance:
            ~1ms per document on M1 GPU
            100 documents: ~100ms total
        """
        logger.info(f"Scoring {len(document_embeddings)} documents")
        start_time = time.time()

        try:
            # Validate query embeddings
            validate_embedding_shape(query_embeddings, "query_embeddings")

            # Validate document embeddings
            for i, doc_emb in enumerate(document_embeddings):
                validate_embedding_shape(doc_emb, f"document_embeddings[{i}]")

            # Compute MaxSim scores
            scores = batch_maxsim_scores(query_embeddings, document_embeddings, use_gpu=use_gpu)

            elapsed_ms = (time.time() - start_time) * 1000

            logger.info(f"Scoring complete: {len(scores)} documents in {elapsed_ms:.1f}ms")
            logger.info(f"Score range: [{min(scores):.3f}, {max(scores):.3f}]")

            return ScoringOutput(
                scores=scores, scoring_time_ms=elapsed_ms, num_candidates=len(document_embeddings)
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            raise ScoringError(f"Failed to score documents: {e}") from e

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model configuration and status.

        Returns:
            {
                "model_name": str,
                "device": str,
                "dtype": str,
                "quantization": Optional[str],
                "memory_allocated_mb": float,
                "is_loaded": bool,
                "cache_dir": str,
                "batch_size_visual": int,
                "batch_size_text": int
            }
        """
        return {
            "model_name": self.config.name,
            "device": self.config.device,
            "dtype": self.config.precision,
            "quantization": "int8" if self.config.is_quantized else None,
            "memory_allocated_mb": self._memory_allocated,
            "is_loaded": hasattr(self, "model") and self.model is not None,
            "cache_dir": self.config.cache_dir,
            "batch_size_visual": self.config.batch_size_visual,
            "batch_size_text": self.config.batch_size_text,
        }

    def clear_cache(self):
        """
        Clear GPU memory cache (useful between large batches).

        For MPS (M1):
            torch.mps.empty_cache()
        For CUDA:
            torch.cuda.empty_cache()
        """
        try:
            import torch

            if self.config.device == "mps" and torch.backends.mps.is_available():
                torch.mps.empty_cache()
                logger.info("MPS cache cleared")
            elif self.config.device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("CUDA cache cleared")
            else:
                logger.debug("No GPU cache to clear (using CPU)")

        except ImportError:
            logger.warning("PyTorch not available, cannot clear cache")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
