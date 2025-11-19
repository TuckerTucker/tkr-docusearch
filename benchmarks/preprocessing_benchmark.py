#!/usr/bin/env python3
"""
Preprocessing Strategy Benchmark Suite

Compares compression, filtering, and synthesis strategies against baseline
(no preprocessing) across diverse queries with comprehensive metrics.

Usage:
    python benchmarks/preprocessing_benchmark.py --mode mock
    python benchmarks/preprocessing_benchmark.py --mode real  # Requires MLX model

Output:
    - Console metrics during execution
    - benchmark-report.md with tables and analysis
"""

import argparse
import asyncio
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import structlog

# Mock imports for when MLX is not available
try:
    from tkr_docusearch.research.context_builder import SourceDocument
    from tkr_docusearch.research.local_preprocessor import LocalLLMPreprocessor
    from tkr_docusearch.research.mlx_llm_client import LLMResponse, MLXLLMClient

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("Warning: Research modules not available, will use mocks")

    # Define mock classes at module level if imports fail
    from dataclasses import dataclass
    from typing import Dict

    @dataclass
    class LLMResponse:
        """Mock LLMResponse for standalone execution"""

        content: str
        model: str
        provider: str
        usage: Dict[str, int]
        finish_reason: str = "stop"
        latency_ms: int = 0

    @dataclass
    class SourceDocument:
        """Mock SourceDocument for standalone execution"""

        doc_id: str
        filename: str
        page: int
        extension: str
        thumbnail_path: Optional[str] = None
        image_path: Optional[str] = None
        timestamp: str = ""
        section_path: Optional[str] = None
        parent_heading: Optional[str] = None
        markdown_content: str = ""
        relevance_score: float = 0.0
        chunk_id: Optional[str] = None
        is_visual: bool = False


logger = structlog.get_logger(__name__)


# ============================================================================
# Test Corpus - 15 diverse queries
# ============================================================================


@dataclass
class TestQuery:
    """Test query with metadata"""

    id: int
    type: str  # Query category
    query: str  # Question text


TEST_QUERIES = [
    # Factual (basic fact recall)
    TestQuery(1, "factual", "What caused the 2008 financial crisis?"),
    TestQuery(2, "factual", "Who invented the telephone?"),
    # Comparison (requires analyzing multiple sources)
    TestQuery(
        3, "comparison", "How do solar and wind energy compare in terms of cost and efficiency?"
    ),
    TestQuery(4, "comparison", "What are the differences between Python and JavaScript?"),
    # Process (step-by-step procedures)
    TestQuery(5, "process", "What are the steps in the document review process?"),
    TestQuery(6, "process", "How does photosynthesis work?"),
    # Multi-part (multiple sub-questions)
    TestQuery(7, "multi-part", "What were the effects of the pandemic on housing and employment?"),
    TestQuery(8, "multi-part", "What are the causes and solutions for climate change?"),
    # Exploratory (open-ended analysis)
    TestQuery(9, "exploratory", "What are the key findings in the climate report?"),
    TestQuery(10, "exploratory", "What are the main themes in the research paper?"),
    # Technical (domain-specific knowledge)
    TestQuery(11, "technical", "How does the OAuth2 authentication system work?"),
    TestQuery(12, "technical", "What is the architecture of a neural network?"),
    # Timeline (temporal relationships)
    TestQuery(13, "timeline", "What events happened between 2010 and 2015?"),
    # Contradictory (requires reconciling conflicts)
    TestQuery(14, "contradictory", "What do different sources say about vaccine efficacy?"),
    # Gap-testing (identify missing information)
    TestQuery(15, "gap", "What information is missing about the project timeline?"),
]


# ============================================================================
# Mock LLM Client (for testing without real model)
# ============================================================================


class MockMLXClient:
    """Mock MLX client for testing without real model"""

    CONTEXT_WINDOW = 16384

    def __init__(self, model_path: str = "mock-model", **kwargs):
        """Initialize mock client"""
        self.model_path = model_path
        self.max_tokens = kwargs.get("max_tokens", 4000)
        self.temperature = kwargs.get("temperature", 0.3)
        logger.info("MockMLXClient initialized", model_path=model_path)

    async def complete(self, prompt: str, **kwargs) -> "LLMResponse":
        """
        Mock completion - simulates compression/scoring/synthesis

        Returns realistic token reduction based on strategy detected in prompt
        """
        # Detect strategy from prompt
        prompt_lower = prompt.lower()

        if "compressed facts" in prompt_lower or "extract the key" in prompt_lower:
            # Compression: 40-50% token reduction
            reduction_factor = 0.45
            mock_content = self._mock_compress(prompt, reduction_factor)
            output_tokens = len(mock_content) // 4

        elif "score:" in prompt_lower or "rate this chunk" in prompt_lower:
            # Relevance scoring: just return a score
            import random

            mock_content = str(round(random.uniform(5.0, 9.5), 1))
            output_tokens = 1

        elif "synthesized knowledge" in prompt_lower or "organize key information" in prompt_lower:
            # Synthesis: major reduction (90%+) with citation preservation
            mock_content = self._mock_synthesize(prompt)
            output_tokens = len(mock_content) // 4

        else:
            # Unknown strategy, return original
            mock_content = "Mock LLM response."
            output_tokens = 4

        # Simulate latency (5-10 tokens/sec)
        latency_ms = int((output_tokens / 7.5) * 1000)
        await asyncio.sleep(latency_ms / 1000)

        # Build response matching MLXLLMClient contract
        return LLMResponse(
            content=mock_content,
            model="mock-gpt-oss-20b",
            provider="mock-mlx",
            usage={
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": output_tokens,
                "total_tokens": (len(prompt) // 4) + output_tokens,
            },
            finish_reason="stop",
            latency_ms=latency_ms,
        )

    def _mock_compress(self, prompt: str, reduction_factor: float) -> str:
        """Mock compression: extract chunk content and reduce it"""
        # Extract chunk content from prompt
        chunk_start = prompt.find("DOCUMENT CHUNK:")
        if chunk_start > 0:
            chunk = prompt[chunk_start + 15 :].strip()
            # Simulate compression by taking first N% of content
            target_len = int(len(chunk) * reduction_factor)
            compressed = chunk[:target_len]
            return compressed
        return "Compressed content (mock)"

    def _mock_synthesize(self, prompt: str) -> str:
        """Mock synthesis: create themed summary with citations"""
        # Extract number of chunks from prompt
        chunk_markers = prompt.count("[")

        synthesis = "## Key Findings:\n"
        synthesis += f"- Finding 1: Information from sources (Sources: [1], [2])\n"
        synthesis += f"- Finding 2: Related data (Source: [3])\n"

        if chunk_markers > 5:
            synthesis += "\n## Additional Themes:\n"
            synthesis += "- Theme A: Analysis shows... (Sources: [4], [5])\n"

        return synthesis


# ============================================================================
# Mock SourceDocument Factory
# ============================================================================


def create_mock_sources(
    num_sources: int = 10, avg_tokens_per_source: int = 400
) -> List["SourceDocument"]:
    """
    Create mock source documents for benchmarking

    Args:
        num_sources: Number of sources to create
        avg_tokens_per_source: Average tokens per source (~1600 chars)

    Returns:
        List of SourceDocument objects with mock content
    """
    sources = []

    for i in range(num_sources):
        # Generate mock content (lorem ipsum style)
        content_length = avg_tokens_per_source * 4  # 4 chars per token
        content = f"Document {i+1} content. " * (content_length // 25)

        # Vary by source type
        if i % 3 == 0:
            # Visual source (no text compression)
            is_visual = True
            content = f"[Image: Chart showing data visualization on page {i+1}]"
        else:
            is_visual = False

        source = SourceDocument(
            doc_id=f"mock-doc-{i+1:03d}",
            filename=f"document_{i+1}.pdf",
            page=i + 1,
            extension="pdf",
            thumbnail_path=(
                f"/images/mock-doc-{i+1:03d}/page{i+1:03d}_thumb.jpg" if is_visual else None
            ),
            image_path=f"/images/mock-doc-{i+1:03d}/page{i+1:03d}.jpg",
            timestamp="2025-01-15T10:00:00Z",
            markdown_content=content[:content_length],
            relevance_score=0.85 - (i * 0.05),  # Decreasing relevance
            chunk_id=None if is_visual else f"mock-doc-{i+1:03d}-chunk{i+1:04d}",
            is_visual=is_visual,
        )
        sources.append(source)

    return sources


# ============================================================================
# Benchmark Runner
# ============================================================================


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""

    query_id: int
    query_type: str
    query_text: str
    strategy: str

    # Token metrics
    tokens_before: int  # Tokens in original sources
    tokens_after: int  # Tokens after preprocessing
    reduction_pct: float  # Percentage reduction

    # Latency metrics
    preprocessing_latency_ms: int

    # Cost metrics (GPT-4 pricing: $10/1M input tokens)
    cost_before_usd: float  # Cost without preprocessing
    cost_after_usd: float  # Cost with preprocessing
    cost_savings_pct: float  # Percentage savings

    # Quality metrics (manual review required)
    citations_preserved: Optional[int] = None
    citations_total: Optional[int] = None
    citation_accuracy_pct: Optional[float] = None


class PreprocessingBenchmark:
    """Benchmark suite for preprocessing strategies"""

    def __init__(self, use_mock: bool = True, num_sources: int = 10):
        """
        Initialize benchmark suite

        Args:
            use_mock: Use mock LLM client (True) or real MLX (False)
            num_sources: Number of sources per query
        """
        self.use_mock = use_mock
        self.num_sources = num_sources
        self.results: List[BenchmarkResult] = []

        # Initialize preprocessor
        if use_mock or not IMPORTS_AVAILABLE:
            mlx_client = MockMLXClient()
            # Create mock preprocessor
            self.preprocessor = self._create_mock_preprocessor(mlx_client)
        else:
            # Real MLX client
            model_path = os.getenv("MLX_MODEL_PATH", "./models/gpt-oss-20B-mlx")
            mlx_client = MLXLLMClient(model_path=model_path)
            self.preprocessor = LocalLLMPreprocessor(mlx_client=mlx_client)

        logger.info(
            "Benchmark initialized",
            use_mock=use_mock,
            num_sources=num_sources,
        )

    def _create_mock_preprocessor(self, mlx_client):
        """Create mock preprocessor when real modules not available"""
        if IMPORTS_AVAILABLE:
            return LocalLLMPreprocessor(mlx_client=mlx_client)

        # Create inline mock preprocessor
        class MockPreprocessor:
            def __init__(self, local_llm):
                self.local_llm = local_llm

            async def compress_chunks(
                self, query: str, sources: List[SourceDocument]
            ) -> List[SourceDocument]:
                """Mock compression"""
                compressed = []
                for source in sources:
                    if source.is_visual or len(source.markdown_content) < 400:
                        compressed.append(source)
                    else:
                        # Simulate 45% compression
                        compressed_content = source.markdown_content[
                            : int(len(source.markdown_content) * 0.55)
                        ]
                        from dataclasses import replace

                        compressed.append(replace(source, markdown_content=compressed_content))
                return compressed

            async def filter_by_relevance(
                self, query: str, sources: List[SourceDocument], threshold: float = 7.0
            ) -> List[SourceDocument]:
                """Mock filtering - keep ~60% of sources"""
                import random

                filtered = []
                for source in sources:
                    score = random.uniform(5.0, 9.5)
                    if score >= threshold:
                        filtered.append(source)
                return filtered

            async def synthesize_knowledge(self, query: str, sources: List[SourceDocument]) -> str:
                """Mock synthesis"""
                synthesis = "## Key Findings:\n"
                synthesis += f"- Finding 1: Information from sources (Sources: [1], [2])\n"
                synthesis += f"- Finding 2: Related data (Source: [3])\n"
                if len(sources) > 5:
                    synthesis += "\n## Additional Themes:\n"
                    synthesis += "- Theme A: Analysis shows... (Sources: [4], [5])\n"
                return synthesis

        return MockPreprocessor(mlx_client)

    async def run_single_benchmark(self, query: TestQuery, strategy: str) -> BenchmarkResult:
        """
        Run benchmark for single query + strategy combination

        Args:
            query: TestQuery object
            strategy: "baseline" | "compress" | "filter" | "synthesize"

        Returns:
            BenchmarkResult with metrics
        """
        logger.info(
            "Running benchmark",
            query_id=query.id,
            query_type=query.type,
            strategy=strategy,
        )

        # Create mock sources
        sources = create_mock_sources(num_sources=self.num_sources)

        # Calculate baseline tokens
        tokens_before = sum(len(s.markdown_content) // 4 for s in sources)

        # Run preprocessing strategy
        start_time = time.time()

        if strategy == "baseline":
            # No preprocessing
            processed_sources = sources
            tokens_after = tokens_before
            preprocessing_latency_ms = 0

        elif strategy == "compress":
            # Compression strategy
            processed_sources = await self.preprocessor.compress_chunks(
                query=query.query, sources=sources
            )
            tokens_after = sum(len(s.markdown_content) // 4 for s in processed_sources)
            preprocessing_latency_ms = int((time.time() - start_time) * 1000)

        elif strategy == "filter":
            # Filtering strategy (threshold=7.0)
            processed_sources = await self.preprocessor.filter_by_relevance(
                query=query.query, sources=sources, threshold=7.0
            )
            tokens_after = sum(len(s.markdown_content) // 4 for s in processed_sources)
            preprocessing_latency_ms = int((time.time() - start_time) * 1000)

        elif strategy == "synthesize":
            # Synthesis strategy
            synthesized_text = await self.preprocessor.synthesize_knowledge(
                query=query.query, sources=sources
            )
            tokens_after = len(synthesized_text) // 4
            preprocessing_latency_ms = int((time.time() - start_time) * 1000)

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Calculate reduction
        reduction_pct = (
            ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
        )

        # Calculate cost savings (GPT-4 pricing: $10/1M input tokens)
        GPT4_INPUT_COST_PER_1M = 10.0
        cost_before_usd = (tokens_before / 1_000_000) * GPT4_INPUT_COST_PER_1M
        cost_after_usd = (tokens_after / 1_000_000) * GPT4_INPUT_COST_PER_1M
        cost_savings_pct = (
            ((cost_before_usd - cost_after_usd) / cost_before_usd * 100)
            if cost_before_usd > 0
            else 0.0
        )

        result = BenchmarkResult(
            query_id=query.id,
            query_type=query.type,
            query_text=query.query,
            strategy=strategy,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            reduction_pct=round(reduction_pct, 1),
            preprocessing_latency_ms=preprocessing_latency_ms,
            cost_before_usd=round(cost_before_usd, 6),
            cost_after_usd=round(cost_after_usd, 6),
            cost_savings_pct=round(cost_savings_pct, 1),
        )

        logger.info(
            "Benchmark complete",
            query_id=query.id,
            strategy=strategy,
            reduction_pct=result.reduction_pct,
            cost_savings_pct=result.cost_savings_pct,
            latency_ms=preprocessing_latency_ms,
        )

        return result

    async def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """
        Run all benchmarks (15 queries × 4 strategies = 60 runs)

        Returns:
            List of all BenchmarkResult objects
        """
        logger.info("Starting full benchmark suite", num_queries=len(TEST_QUERIES))

        strategies = ["baseline", "compress", "filter", "synthesize"]

        for query in TEST_QUERIES:
            for strategy in strategies:
                result = await self.run_single_benchmark(query, strategy)
                self.results.append(result)

        logger.info("Benchmark suite complete", total_runs=len(self.results))

        return self.results

    def generate_report(self, output_path: str = "benchmark-report.md") -> str:
        """
        Generate markdown report from benchmark results

        Args:
            output_path: Path to save report

        Returns:
            Report content as string
        """
        if not self.results:
            return "No benchmark results available."

        # Organize results by strategy
        strategy_results = {
            "baseline": [],
            "compress": [],
            "filter": [],
            "synthesize": [],
        }

        for result in self.results:
            strategy_results[result.strategy].append(result)

        # Calculate aggregate metrics
        def avg(values):
            return sum(values) / len(values) if values else 0

        aggregate = {}
        for strategy, results in strategy_results.items():
            aggregate[strategy] = {
                "avg_tokens_before": int(avg([r.tokens_before for r in results])),
                "avg_tokens_after": int(avg([r.tokens_after for r in results])),
                "avg_reduction_pct": round(avg([r.reduction_pct for r in results]), 1),
                "avg_preprocessing_latency_ms": int(
                    avg([r.preprocessing_latency_ms for r in results])
                ),
                "avg_cost_savings_pct": round(avg([r.cost_savings_pct for r in results]), 1),
                "num_runs": len(results),
            }

        # Build markdown report
        report = "# Preprocessing Strategy Benchmark Report\n\n"
        report += f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Mode:** {'Mock LLM' if self.use_mock else 'Real MLX Model'}\n"
        report += f"**Test Queries:** {len(TEST_QUERIES)}\n"
        report += f"**Sources per Query:** {self.num_sources}\n"
        report += f"**Total Benchmark Runs:** {len(self.results)}\n\n"

        # Executive Summary
        report += "## Executive Summary\n\n"

        baseline_tokens = aggregate["baseline"]["avg_tokens_before"]
        compress_reduction = aggregate["compress"]["avg_reduction_pct"]
        filter_reduction = aggregate["filter"]["avg_reduction_pct"]
        synthesize_reduction = aggregate["synthesize"]["avg_reduction_pct"]

        report += f"- **Baseline tokens:** {baseline_tokens:,} avg per query\n"
        report += f"- **Compression:** {compress_reduction}% token reduction\n"
        report += f"- **Filtering:** {filter_reduction}% token reduction\n"
        report += f"- **Synthesis:** {synthesize_reduction}% token reduction\n\n"

        # Target validation
        report += "### Target Validation\n\n"
        report += f"- ✅ Token reduction ≥30%: **{compress_reduction >= 30}** (Compression: {compress_reduction}%)\n"
        report += f"- ✅ Cost savings ≥40%: **{aggregate['compress']['avg_cost_savings_pct'] >= 40}** (Compression: {aggregate['compress']['avg_cost_savings_pct']}%)\n"
        report += f"- ⚠️  Citation accuracy ≥95%: **Manual review required**\n\n"

        # Strategy Comparison Table
        report += "## Strategy Comparison\n\n"
        report += "| Strategy | Avg Tokens Before | Avg Tokens After | Reduction % | Preprocessing Latency (ms) | Cost Savings % |\n"
        report += "|----------|-------------------|------------------|-------------|---------------------------|----------------|\n"

        for strategy in ["baseline", "compress", "filter", "synthesize"]:
            agg = aggregate[strategy]
            report += f"| {strategy.capitalize():12} | {agg['avg_tokens_before']:17,} | {agg['avg_tokens_after']:16,} | {agg['avg_reduction_pct']:11}% | {agg['avg_preprocessing_latency_ms']:25,} | {agg['avg_cost_savings_pct']:14}% |\n"

        report += "\n"

        # Query Type Breakdown
        report += "## Performance by Query Type\n\n"
        report += (
            "| Query Type | Compress Reduction % | Filter Reduction % | Synthesize Reduction % |\n"
        )
        report += (
            "|------------|---------------------|-------------------|------------------------|\n"
        )

        query_types = sorted(set(r.query_type for r in self.results))
        for qtype in query_types:
            compress_results = [
                r for r in self.results if r.query_type == qtype and r.strategy == "compress"
            ]
            filter_results = [
                r for r in self.results if r.query_type == qtype and r.strategy == "filter"
            ]
            synthesize_results = [
                r for r in self.results if r.query_type == qtype and r.strategy == "synthesize"
            ]

            compress_avg = round(avg([r.reduction_pct for r in compress_results]), 1)
            filter_avg = round(avg([r.reduction_pct for r in filter_results]), 1)
            synthesize_avg = round(avg([r.reduction_pct for r in synthesize_results]), 1)

            report += (
                f"| {qtype:12} | {compress_avg:19}% | {filter_avg:17}% | {synthesize_avg:22}% |\n"
            )

        report += "\n"

        # Detailed Results
        report += "## Detailed Results\n\n"
        report += "<details>\n<summary>Click to expand full results table</summary>\n\n"
        report += "| Query ID | Type | Strategy | Tokens Before | Tokens After | Reduction % | Latency (ms) | Cost Savings % |\n"
        report += "|----------|------|----------|---------------|--------------|-------------|--------------|----------------|\n"

        for result in self.results:
            report += f"| {result.query_id:8} | {result.query_type:12} | {result.strategy:10} | {result.tokens_before:13,} | {result.tokens_after:12,} | {result.reduction_pct:11}% | {result.preprocessing_latency_ms:12,} | {result.cost_savings_pct:14}% |\n"

        report += "\n</details>\n\n"

        # Recommendations
        report += "## Recommendations\n\n"

        if compress_reduction >= 30:
            report += "✅ **Compression strategy meets target** (≥30% reduction)\n"
        else:
            report += "⚠️  **Compression strategy below target** - Consider optimizing compression prompt\n"

        if aggregate["compress"]["avg_cost_savings_pct"] >= 40:
            report += "✅ **Cost savings meet target** (≥40% savings)\n"
        else:
            report += "⚠️  **Cost savings below target** - Review token reduction strategies\n"

        report += "\n### Citation Accuracy Validation\n"
        report += "Manual review required for citation preservation:\n"
        report += "1. Select 5 random synthesis results\n"
        report += "2. Count citations in synthesized output\n"
        report += "3. Verify citations match original sources\n"
        report += "4. Calculate accuracy percentage\n\n"

        # Save report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info("Benchmark report generated", output_path=output_path)

        return report


# ============================================================================
# Main Execution
# ============================================================================


async def main():
    """Run benchmark suite and generate report"""
    parser = argparse.ArgumentParser(description="Preprocessing Strategy Benchmark Suite")
    parser.add_argument(
        "--mode",
        choices=["mock", "real"],
        default="mock",
        help="Use mock LLM (fast) or real MLX model (accurate)",
    )
    parser.add_argument(
        "--sources",
        type=int,
        default=10,
        help="Number of sources per query (default: 10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark-report.md",
        help="Output report path (default: benchmark-report.md)",
    )

    args = parser.parse_args()

    # Configure logging
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )

    # Run benchmark
    use_mock = args.mode == "mock"
    benchmark = PreprocessingBenchmark(use_mock=use_mock, num_sources=args.sources)

    print(f"\n{'='*70}")
    print(f"  Preprocessing Strategy Benchmark Suite")
    print(f"{'='*70}")
    print(f"  Mode: {args.mode.upper()}")
    print(f"  Sources: {args.sources}")
    print(f"  Queries: {len(TEST_QUERIES)}")
    print(f"{'='*70}\n")

    # Run all benchmarks
    results = await benchmark.run_all_benchmarks()

    # Generate report
    print("\nGenerating report...")
    report = benchmark.generate_report(output_path=args.output)

    print(f"\n{'='*70}")
    print(f"  Benchmark Complete!")
    print(f"{'='*70}")
    print(f"  Total runs: {len(results)}")
    print(f"  Report: {args.output}")
    print(f"{'='*70}\n")

    # Print summary
    print(report.split("## Strategy Comparison")[1].split("##")[0])


if __name__ == "__main__":
    import logging

    asyncio.run(main())
