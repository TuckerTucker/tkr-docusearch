"""
Koji database configuration.

This module defines configuration for the Koji hybrid database
(SQL + vector + graph).
"""

import os
from dataclasses import dataclass


@dataclass
class KojiConfig:
    """Koji database configuration.

    Attributes:
        db_path: Path to the Koji database file.
        server_port: Port for Koji server (reserved for multi-process access).
        sync_on_write: Whether to flush to disk after mutations.
        compact_interval: Number of writes before triggering compaction.
    """

    db_path: str = os.getenv("KOJI_DB_PATH", "./data/koji.db")
    server_port: int = int(os.getenv("KOJI_SERVER_PORT", "8003"))
    sync_on_write: bool = os.getenv("KOJI_SYNC_ON_WRITE", "true").lower() == "true"
    compact_interval: int = int(os.getenv("KOJI_COMPACT_INTERVAL", "100"))

    @classmethod
    def from_env(cls) -> "KojiConfig":
        """Load configuration from environment variables.

        Returns:
            KojiConfig instance with values from environment.
        """
        return cls(
            db_path=os.getenv("KOJI_DB_PATH", "./data/koji.db"),
            server_port=int(os.getenv("KOJI_SERVER_PORT", "8003")),
            sync_on_write=os.getenv("KOJI_SYNC_ON_WRITE", "true").lower() == "true",
            compact_interval=int(os.getenv("KOJI_COMPACT_INTERVAL", "100")),
        )

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary.
        """
        return {
            "db_path": self.db_path,
            "server_port": self.server_port,
            "sync_on_write": self.sync_on_write,
            "compact_interval": self.compact_interval,
        }

    def __repr__(self) -> str:
        """Return string representation of configuration."""
        return (
            f"KojiConfig("
            f"db_path='{self.db_path}', "
            f"sync_on_write={self.sync_on_write}, "
            f"compact={self.compact_interval})"
        )


@dataclass
class ShikomiConfig:
    """Shikomi embedding service configuration.

    Attributes:
        model: ColNomic model name for embeddings.
        grpc_target: Shikomi gRPC server address (host:port).
        device: Compute device (auto, mps, cuda, cpu).
        quantization: Model quantization level (fp32, fp16, int8, int4).
        use_mock: Use mock embeddings for testing without GPU.
    """

    model: str = os.getenv(
        "SHIKOMI_MODEL", "nomic-ai/colnomic-embed-multimodal-7b"
    )
    grpc_target: str = os.getenv("SHIKOMI_GRPC_TARGET", "localhost:50051")
    device: str = os.getenv("SHIKOMI_DEVICE", "auto")
    quantization: str = os.getenv("SHIKOMI_QUANTIZATION", "fp16")
    use_mock: bool = os.getenv("SHIKOMI_USE_MOCK", "false").lower() == "true"

    @classmethod
    def from_env(cls) -> "ShikomiConfig":
        """Load configuration from environment variables.

        Returns:
            ShikomiConfig instance with values from environment.
        """
        return cls(
            model=os.getenv(
                "SHIKOMI_MODEL", "nomic-ai/colnomic-embed-multimodal-7b"
            ),
            grpc_target=os.getenv("SHIKOMI_GRPC_TARGET", "localhost:50051"),
            device=os.getenv("SHIKOMI_DEVICE", "auto"),
            quantization=os.getenv("SHIKOMI_QUANTIZATION", "fp16"),
            use_mock=os.getenv("SHIKOMI_USE_MOCK", "false").lower() == "true",
        )

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary.
        """
        return {
            "model": self.model,
            "grpc_target": self.grpc_target,
            "device": self.device,
            "quantization": self.quantization,
            "use_mock": self.use_mock,
        }

    def __repr__(self) -> str:
        """Return string representation of configuration."""
        return (
            f"ShikomiConfig("
            f"model='{self.model}', "
            f"device='{self.device}', "
            f"quantization='{self.quantization}')"
        )
