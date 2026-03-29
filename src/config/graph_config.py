"""
Graph enrichment configuration.

This module defines configuration for the document graph ontology
enrichment service — thresholds, schedule, and boost weights.
"""

import os
from dataclasses import dataclass


@dataclass
class GraphEnrichmentConfig:
    """Graph enrichment configuration.

    Attributes:
        similarity_threshold: Minimum MaxSim score for ``similar_to`` edges.
        similarity_top_k: Max neighbors per document for similarity.
        same_topic_jaccard_threshold: Minimum Jaccard for ``same_topic`` edges.
        max_community_full_connect: Communities larger than this use
            nearest-neighbor connections instead of all-pairs.
        enrichment_interval_seconds: Seconds between periodic enrichment runs.
        auto_enrich_on_startup: Whether to run enrichment at startup.
    """

    similarity_threshold: float = float(
        os.getenv("GRAPH_SIMILARITY_THRESHOLD", "0.7")
    )
    similarity_top_k: int = int(
        os.getenv("GRAPH_SIMILARITY_TOP_K", "5")
    )
    same_topic_jaccard_threshold: float = float(
        os.getenv("GRAPH_TOPIC_JACCARD_THRESHOLD", "0.5")
    )
    max_community_full_connect: int = int(
        os.getenv("GRAPH_MAX_COMMUNITY_FULL_CONNECT", "20")
    )
    enrichment_interval_seconds: int = int(
        os.getenv("GRAPH_ENRICHMENT_INTERVAL", "3600")
    )
    auto_enrich_on_startup: bool = (
        os.getenv("GRAPH_AUTO_ENRICH", "false").lower() == "true"
    )

    @classmethod
    def from_env(cls) -> "GraphEnrichmentConfig":
        """Load configuration from environment variables.

        Returns:
            GraphEnrichmentConfig instance with values from environment.
        """
        return cls()

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary.
        """
        return {
            "similarity_threshold": self.similarity_threshold,
            "similarity_top_k": self.similarity_top_k,
            "same_topic_jaccard_threshold": self.same_topic_jaccard_threshold,
            "max_community_full_connect": self.max_community_full_connect,
            "enrichment_interval_seconds": self.enrichment_interval_seconds,
            "auto_enrich_on_startup": self.auto_enrich_on_startup,
        }
