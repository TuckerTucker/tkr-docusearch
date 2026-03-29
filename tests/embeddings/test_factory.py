"""Tests for embedding engine factory."""

import pytest
from unittest.mock import patch, MagicMock

from src.config.koji_config import ShikomiConfig
from src.embeddings.factory import create_embedding_engine


class TestCreateEmbeddingEngine:
    """Tests for the create_embedding_engine factory function."""

    def test_in_process_mode(self):
        """Config with mode='in_process' returns InProcessEmbeddingEngine."""
        config = ShikomiConfig(
            mode="in_process",
            device="cpu",
            quantization="fp16",
        )

        mock_engine = MagicMock()
        mock_cls = MagicMock(return_value=mock_engine)

        with patch.dict(
            "sys.modules",
            {"src.embeddings.in_process_engine": MagicMock(
                InProcessEmbeddingEngine=mock_cls
            )},
        ):
            # Re-import to pick up the patched module
            from importlib import reload
            import src.embeddings.factory as factory_mod
            reload(factory_mod)

            result = factory_mod.create_embedding_engine(config)

            mock_cls.assert_called_once_with(
                device="cpu",
                quantization="fp16",
            )
            mock_engine.connect.assert_called_once()
            assert result is mock_engine

    def test_grpc_mode(self):
        """Config with mode='grpc' returns ShikomiClient."""
        config = ShikomiConfig(
            mode="grpc",
            grpc_target="localhost:50051",
        )

        mock_engine = MagicMock()
        mock_cls = MagicMock(return_value=mock_engine)

        with patch.dict(
            "sys.modules",
            {"src.embeddings.shikomi_client": MagicMock(
                ShikomiClient=mock_cls
            )},
        ):
            from importlib import reload
            import src.embeddings.factory as factory_mod
            reload(factory_mod)

            result = factory_mod.create_embedding_engine(config)

            mock_cls.assert_called_once_with(config=config)
            mock_engine.connect.assert_called_once()
            assert result is mock_engine

    def test_unknown_mode_raises(self):
        """Config with unrecognized mode raises ValueError."""
        config = ShikomiConfig(mode="invalid")

        with pytest.raises(ValueError, match="Unknown SHIKOMI_MODE 'invalid'"):
            create_embedding_engine(config)

    def test_unknown_mode_includes_valid_options(self):
        """Error message mentions valid modes."""
        config = ShikomiConfig(mode="banana")

        with pytest.raises(ValueError, match="'grpc' or 'in_process'"):
            create_embedding_engine(config)
