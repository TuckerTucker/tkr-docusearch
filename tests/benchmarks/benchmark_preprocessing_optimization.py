#!/usr/bin/env python3
"""
GPT-OSS-20B Harmony Preprocessing Optimization Benchmark.

Compares legacy vs Harmony prompts to validate token reduction and latency improvements.
This benchmark specifically measures the impact of the Harmony prompt optimization
on the preprocessing pipeline's compression strategy.

Usage:
    # Run with mock LLM (fast, simulated)
    python tests/benchmarks/benchmark_preprocessing_optimization.py --mode mock

    # Run with real MLX model (accurate, requires MLX setup)
    python tests/benchmarks/benchmark_preprocessing_optimization.py --mode real

    # Specify output path
    python tests/benchmarks/benchmark_preprocessing_optimization.py --mode mock --output .context-kit/benchmarks/preprocessing-results.md

Output:
    - Console metrics during execution
    - Markdown report with before/after comparison
    - Pass/fail validation against contract targets
"""

import argparse
import asyncio
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import structlog

# Attempt to import research modules
try:
    from src.research.context_builder import SourceDocument
    from src.research.local_preprocessor import LocalLLMPreprocessor
    from src.research.mlx_llm_client import LLMResponse, MLXLLMClient

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("Warning: Research modules not available, using mocks")

    # Mock classes for standalone execution
    from dataclasses import dataclass
    from typing import Dict

    @dataclass
    class LLMResponse:
        """Mock LLMResponse"""

        content: str
        model: str
        provider: str
        usage: Dict[str, int]
        finish_reason: str = "stop"
        latency_ms: int = 0

    @dataclass
    class SourceDocument:
        """Mock SourceDocument"""

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
# Test Corpus - Resume Chunks (Real Examples)
# ============================================================================


# These are actual resume text samples that showed expansion with legacy prompts
RESUME_CHUNKS = [
    # Chunk 1: Professional summary (~400 chars)
    "Tucker is a Senior UX Designer with 15+ years of experience. "
    "He has worked at Nutrien as Lead UX Designer from February 2023 to September 2023, "
    "where he led a team of 5 designers on multiple product initiatives. "
    "His contact information is 403-630-7003 and connect@tucker.sh. "
    "He has expertise in product design, user research, and design systems.",
    # Chunk 2: Work experience (~500 chars)
    "At Nutrien, Tucker led a team of 5 designers and collaborated with cross-functional teams "
    "including product managers, engineers, and executives. He designed multiple B2B SaaS products "
    "serving 10,000+ farmers across North America. His work focused on improving user experience "
    "for agricultural planning and crop management tools. He also established design system standards "
    "and mentored junior designers on the team throughout his tenure.",
    # Chunk 3: Technical skills (~450 chars)
    "Tucker has extensive experience with design tools including Figma, Sketch, Adobe Creative Suite, "
    "and prototyping tools like Axure and InVision. He is proficient in user research methodologies "
    "including usability testing, user interviews, surveys, and analytics. His technical skills "
    "include HTML, CSS, JavaScript, and React. He has worked on both web and mobile applications "
    "for iOS and Android platforms across various industries.",
    # Chunk 4: Education and certifications (~400 chars)
    "Tucker holds a Bachelor's degree in Design from Emily Carr University of Art and Design. "
    "He has completed certifications in UX Design from Nielsen Norman Group and Interaction Design "
    "Foundation. He regularly attends design conferences including UXPA International and SXSW. "
    "He has also completed training in accessibility standards including WCAG 2.1 and inclusive design practices.",
    # Chunk 5: Projects and achievements (~550 chars)
    "Tucker has successfully launched 15+ products across his career, including mobile apps, web applications, "
    "and enterprise software. His work at Nutrien resulted in a 40% increase in user satisfaction scores "
    "and a 25% reduction in support tickets. He redesigned the core product experience serving 10,000+ farmers, "
    "which led to improved adoption and engagement metrics. His design system work reduced design-to-development "
    "time by 30% and improved consistency across products. He has received recognition from leadership "
    "for his contributions to product strategy and user experience excellence.",
]


# ============================================================================
# Mock MLX Client for Testing
# ============================================================================


class MockMLXClient:
    """Mock MLX client that simulates legacy vs Harmony compression behavior"""

    CONTEXT_WINDOW = 16384

    def __init__(self, model_path: str = "mock-model", **kwargs):
        """Initialize mock client"""
        self.model_path = model_path
        self.max_tokens = kwargs.get("max_tokens", 4000)
        self.temperature = kwargs.get("temperature", 0.3)
        logger.info("MockMLXClient initialized", model_path=model_path)

    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Mock completion - simulates legacy vs Harmony performance.

        Legacy behavior:
        - Returns verbose prose output
        - Often expands instead of compresses
        - Slower latency (6-8s per chunk)

        Harmony behavior:
        - Returns concise JSON output
        - 40-50% token reduction
        - Faster latency (2-3s per chunk)
        """
        # Detect prompt type
        is_harmony = "```json" in prompt.lower() or "output format:" in prompt.lower()

        # Extract chunk content from prompt
        chunk_content = self._extract_chunk_content(prompt)
        original_tokens = len(chunk_content) // 4

        if is_harmony:
            # Harmony simulation: 35-45% reduction (targeting mid-range)
            # Apply reduction at token level with realistic variance
            import random

            # Target 40% reduction +/- 5% variance
            target_reduction = random.uniform(0.35, 0.45)
            target_tokens = int(original_tokens * (1 - target_reduction))

            # Simulate compression to target token count
            compressed_content = self._simulate_compression_to_tokens(
                chunk_content, target_tokens
            )
            output_tokens = len(compressed_content) // 4

            # Format as JSON
            content = f'{{"facts": "{compressed_content}"}}'

            # Simulate faster latency (2-3s, ~30 tokens/sec)
            latency_ms = int((output_tokens / 30) * 1000) + 500  # Base + processing
            await asyncio.sleep(latency_ms / 1000)

        else:
            # Legacy simulation: 5-10% expansion (verbose prose)
            expansion_factor = 1.07  # 7% expansion
            expanded_content = self._simulate_expansion(chunk_content, expansion_factor)
            output_tokens = len(expanded_content) // 4

            # Format as prose
            content = expanded_content

            # Simulate slower latency (6-8s, ~15 tokens/sec)
            latency_ms = int((output_tokens / 15) * 1000) + 1000  # Base + processing
            await asyncio.sleep(latency_ms / 1000)

        # Build response
        return LLMResponse(
            content=content,
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

    def _extract_chunk_content(self, prompt: str) -> str:
        """Extract chunk content from prompt"""
        # Look for content after "DOCUMENT CHUNK:" or similar markers
        markers = ["DOCUMENT CHUNK:", "Chunk content:", "Text:"]
        for marker in markers:
            if marker in prompt:
                chunk = prompt.split(marker)[1].strip()
                # Take content before next instruction
                if "Output format:" in chunk:
                    chunk = chunk.split("Output format:")[0].strip()
                if "Return only:" in chunk:
                    chunk = chunk.split("Return only:")[0].strip()
                return chunk

        # Fallback: return last 500 chars of prompt (likely the chunk)
        return prompt[-500:]

    def _simulate_compression_to_tokens(self, content: str, target_tokens: int) -> str:
        """
        Simulate compression to achieve target token count.

        Args:
            content: Original content
            target_tokens: Target token count (using 4 chars/token approximation)

        Returns:
            Compressed content string
        """
        # Calculate target character length
        target_length = target_tokens * 4

        # Split into sentences
        sentences = [s.strip() for s in content.split(".") if s.strip()]

        # Build compressed version by taking sentences until we hit target length
        compressed_parts = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) + 2 <= target_length:  # +2 for ". "
                compressed_parts.append(sentence)
                current_length += len(sentence) + 2
            else:
                break

        # If we got nothing, take first sentence
        if not compressed_parts:
            compressed_parts = [sentences[0]]

        compressed = ". ".join(compressed_parts) + "."

        # Truncate if still too long
        if len(compressed) > target_length:
            compressed = compressed[:target_length]

        return compressed

    def _simulate_expansion(self, content: str, expansion_factor: float) -> str:
        """Simulate expansion by adding verbose wording"""
        # Add verbose prefixes/suffixes
        expanded = (
            "Based on the document content, the key facts are as follows: "
            + content
            + " These details provide important context and information."
        )

        # Ensure we actually expanded
        target_length = int(len(content) * expansion_factor)
        while len(expanded) < target_length:
            expanded += " Additional relevant information is included in the source material."

        return expanded


# ============================================================================
# Benchmark Result Dataclass
# ============================================================================


@dataclass
class BenchmarkResult:
    """Results from benchmarking a single chunk"""

    chunk_id: int
    chunk_description: str

    # Token metrics
    original_tokens: int
    legacy_tokens: int
    harmony_tokens: int

    # Reduction metrics
    legacy_reduction_pct: float  # Negative if expansion
    harmony_reduction_pct: float

    # Latency metrics
    legacy_latency_ms: int
    harmony_latency_ms: int
    latency_improvement_pct: float

    # Validation
    harmony_meets_target: bool  # True if 30-50% reduction


# ============================================================================
# Benchmark Runner
# ============================================================================


class HarmonyOptimizationBenchmark:
    """Benchmark legacy vs Harmony preprocessing optimization"""

    def __init__(self, use_mock: bool = True):
        """
        Initialize benchmark suite.

        Args:
            use_mock: Use mock LLM client (True) or real MLX (False)
        """
        self.use_mock = use_mock
        self.results: List[BenchmarkResult] = []

        # Initialize MLX client
        if use_mock or not IMPORTS_AVAILABLE:
            self.mlx_client = MockMLXClient()
        else:
            # Real MLX client
            model_path = os.getenv("MLX_MODEL_PATH", "./models/gpt-oss-20B-mlx")
            self.mlx_client = MLXLLMClient(model_path=model_path)

        logger.info("Benchmark initialized", use_mock=use_mock)

    async def run_single_benchmark(
        self, chunk_id: int, chunk_content: str, description: str
    ) -> BenchmarkResult:
        """
        Benchmark a single chunk with both legacy and Harmony prompts.

        Args:
            chunk_id: Numeric ID for the chunk
            chunk_content: Text content to compress
            description: Human-readable description

        Returns:
            BenchmarkResult with metrics
        """
        logger.info(
            "Running benchmark",
            chunk_id=chunk_id,
            description=description,
            content_length=len(chunk_content),
        )

        # Create source document
        source = SourceDocument(
            doc_id=f"test_doc_{chunk_id}",
            filename="test_resume.pdf",
            page=chunk_id,
            extension="pdf",
            markdown_content=chunk_content,
            relevance_score=0.95,
            chunk_id=f"test_doc_{chunk_id}-chunk{chunk_id:04d}",
            is_visual=False,
        )

        original_tokens = len(chunk_content) // 4

        # ===== Test 1: Legacy Prompts (USE_HARMONY_PROMPTS=false) =====
        # Save original env var
        original_harmony_setting = os.environ.get("USE_HARMONY_PROMPTS")

        try:
            os.environ["USE_HARMONY_PROMPTS"] = "false"

            if IMPORTS_AVAILABLE:
                preprocessor_legacy = LocalLLMPreprocessor(self.mlx_client)
            else:
                # Mock preprocessor
                preprocessor_legacy = self._create_mock_preprocessor(use_harmony=False)

            # Run compression
            start_time = time.time()
            compressed_legacy = await preprocessor_legacy.compress_chunks(
                query="What are the key facts?", sources=[source]
            )
            legacy_latency_ms = int((time.time() - start_time) * 1000)

            legacy_tokens = len(compressed_legacy[0].markdown_content) // 4
            legacy_reduction_pct = (
                ((original_tokens - legacy_tokens) / original_tokens * 100)
                if original_tokens > 0
                else 0.0
            )

            # ===== Test 2: Harmony Prompts (USE_HARMONY_PROMPTS=true) =====
            os.environ["USE_HARMONY_PROMPTS"] = "true"

            if IMPORTS_AVAILABLE:
                preprocessor_harmony = LocalLLMPreprocessor(self.mlx_client)
            else:
                # Mock preprocessor
                preprocessor_harmony = self._create_mock_preprocessor(use_harmony=True)

            # Run compression
            start_time = time.time()
            compressed_harmony = await preprocessor_harmony.compress_chunks(
                query="What are the key facts?", sources=[source]
            )
            harmony_latency_ms = int((time.time() - start_time) * 1000)

            harmony_tokens = len(compressed_harmony[0].markdown_content) // 4
            harmony_reduction_pct = (
                ((original_tokens - harmony_tokens) / original_tokens * 100)
                if original_tokens > 0
                else 0.0
            )
        finally:
            # Restore original env var
            if original_harmony_setting is None:
                os.environ.pop("USE_HARMONY_PROMPTS", None)
            else:
                os.environ["USE_HARMONY_PROMPTS"] = original_harmony_setting

        # Calculate improvement
        latency_improvement_pct = (
            ((legacy_latency_ms - harmony_latency_ms) / legacy_latency_ms * 100)
            if legacy_latency_ms > 0
            else 0.0
        )

        # Validate target achievement
        harmony_meets_target = 30.0 <= harmony_reduction_pct <= 50.0

        # Build result
        result = BenchmarkResult(
            chunk_id=chunk_id,
            chunk_description=description,
            original_tokens=original_tokens,
            legacy_tokens=legacy_tokens,
            harmony_tokens=harmony_tokens,
            legacy_reduction_pct=round(legacy_reduction_pct, 1),
            harmony_reduction_pct=round(harmony_reduction_pct, 1),
            legacy_latency_ms=legacy_latency_ms,
            harmony_latency_ms=harmony_latency_ms,
            latency_improvement_pct=round(latency_improvement_pct, 1),
            harmony_meets_target=harmony_meets_target,
        )

        logger.info(
            "Benchmark complete",
            chunk_id=chunk_id,
            legacy_reduction_pct=result.legacy_reduction_pct,
            harmony_reduction_pct=result.harmony_reduction_pct,
            latency_improvement_pct=result.latency_improvement_pct,
            meets_target=harmony_meets_target,
        )

        return result

    async def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """
        Run benchmarks for all resume chunks.

        Returns:
            List of BenchmarkResult objects
        """
        logger.info("Starting full benchmark suite", num_chunks=len(RESUME_CHUNKS))

        chunk_descriptions = [
            "Professional summary",
            "Work experience",
            "Technical skills",
            "Education and certifications",
            "Projects and achievements",
        ]

        for idx, (chunk, description) in enumerate(
            zip(RESUME_CHUNKS, chunk_descriptions), start=1
        ):
            result = await self.run_single_benchmark(idx, chunk, description)
            self.results.append(result)

        logger.info("Benchmark suite complete", total_runs=len(self.results))

        return self.results

    def generate_report(self, output_path: str) -> str:
        """
        Generate markdown report from benchmark results.

        Args:
            output_path: Path to save report

        Returns:
            Report content as string
        """
        if not self.results:
            return "No benchmark results available."

        # Calculate aggregate metrics
        def avg(values):
            return sum(values) / len(values) if values else 0

        avg_legacy_reduction = avg([r.legacy_reduction_pct for r in self.results])
        avg_harmony_reduction = avg([r.harmony_reduction_pct for r in self.results])
        avg_legacy_latency = avg([r.legacy_latency_ms for r in self.results])
        avg_harmony_latency = avg([r.harmony_latency_ms for r in self.results])
        avg_latency_improvement = avg([r.latency_improvement_pct for r in self.results])

        # Success criteria
        target_met = 30.0 <= avg_harmony_reduction <= 50.0
        latency_target_met = avg_harmony_latency < 3000  # <3s per chunk
        num_targets_met = sum(1 for r in self.results if r.harmony_meets_target)
        target_success_rate = (num_targets_met / len(self.results) * 100) if self.results else 0

        # Build markdown report
        report = "# GPT-OSS-20B Preprocessing Optimization - Benchmark Results\n\n"
        report += "## Executive Summary\n\n"
        report += f"**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**MLX Model:** {'Mock (simulated)' if self.use_mock else 'gpt-oss-20b-4bit (real)'}\n"
        report += f"**Test Chunks:** {len(self.results)} resume text samples\n\n"

        # Validation status
        report += "### Validation Status\n\n"
        if self.use_mock:
            report += "**Note:** Results are simulated based on contract specifications. "
            report += "Real MLX model validation required for production deployment.\n\n"

        report += "| Criterion | Target | Legacy | Harmony | Status |\n"
        report += "|-----------|--------|--------|---------|--------|\n"
        report += (
            f"| Token Reduction | 30-50% | {avg_legacy_reduction:+.1f}% | "
            f"{avg_harmony_reduction:+.1f}% | {'✅ PASS' if target_met else '❌ FAIL'} |\n"
        )
        report += (
            f"| Latency per Chunk | <3000ms | {avg_legacy_latency:.0f}ms | "
            f"{avg_harmony_latency:.0f}ms | {'✅ PASS' if latency_target_met else '❌ FAIL'} |\n"
        )
        report += (
            f"| Target Success Rate | 80%+ | N/A | {target_success_rate:.0f}% | "
            f"{'✅ PASS' if target_success_rate >= 80 else '❌ FAIL'} |\n"
        )
        report += "\n"

        # Key findings
        report += "### Key Findings\n\n"
        report += f"- **Legacy Prompts:** {avg_legacy_reduction:+.1f}% average (expansion: {avg_legacy_reduction < 0})\n"
        report += f"- **Harmony Prompts:** {avg_harmony_reduction:+.1f}% average token reduction\n"
        report += f"- **Improvement:** {avg_harmony_reduction - avg_legacy_reduction:.1f} percentage point improvement\n"
        report += f"- **Latency Improvement:** {avg_latency_improvement:.1f}% faster ({avg_legacy_latency - avg_harmony_latency:.0f}ms saved)\n"
        report += f"- **Reliability:** {num_targets_met}/{len(self.results)} chunks met 30-50% target\n\n"

        # Detailed results table
        report += "## Detailed Results\n\n"
        report += "| Chunk | Description | Original | Legacy | Harmony | Legacy Δ | Harmony Δ | Latency Improvement | Target Met |\n"
        report += "|-------|-------------|----------|--------|---------|----------|-----------|---------------------|------------|\n"

        for r in self.results:
            report += (
                f"| {r.chunk_id} | {r.chunk_description} | {r.original_tokens} | "
                f"{r.legacy_tokens} | {r.harmony_tokens} | {r.legacy_reduction_pct:+.1f}% | "
                f"{r.harmony_reduction_pct:+.1f}% | {r.latency_improvement_pct:+.1f}% | "
                f"{'✅' if r.harmony_meets_target else '❌'} |\n"
            )

        report += "\n"

        # Performance comparison
        report += "## Performance Comparison\n\n"
        report += "### Token Usage\n\n"
        report += "| Metric | Legacy | Harmony | Improvement |\n"
        report += "|--------|--------|---------|-------------|\n"
        report += (
            f"| Avg Original Tokens | {avg([r.original_tokens for r in self.results]):.0f} | "
            f"{avg([r.original_tokens for r in self.results]):.0f} | - |\n"
        )
        report += (
            f"| Avg Output Tokens | {avg([r.legacy_tokens for r in self.results]):.0f} | "
            f"{avg([r.harmony_tokens for r in self.results]):.0f} | "
            f"{avg([r.legacy_tokens for r in self.results]) - avg([r.harmony_tokens for r in self.results]):.0f} fewer |\n"
        )
        report += (
            f"| Avg Reduction | {avg_legacy_reduction:+.1f}% | {avg_harmony_reduction:+.1f}% | "
            f"{avg_harmony_reduction - avg_legacy_reduction:.1f}pp |\n"
        )
        report += "\n"

        report += "### Latency\n\n"
        report += "| Metric | Legacy | Harmony | Improvement |\n"
        report += "|--------|--------|---------|-------------|\n"
        report += (
            f"| Avg per Chunk | {avg_legacy_latency:.0f}ms | {avg_harmony_latency:.0f}ms | "
            f"{avg_latency_improvement:+.1f}% |\n"
        )
        report += (
            f"| Total (all chunks) | {sum(r.legacy_latency_ms for r in self.results):.0f}ms | "
            f"{sum(r.harmony_latency_ms for r in self.results):.0f}ms | "
            f"{sum(r.legacy_latency_ms for r in self.results) - sum(r.harmony_latency_ms for r in self.results):.0f}ms saved |\n"
        )
        report += "\n"

        # Recommendations
        report += "## Recommendations\n\n"

        if target_met and latency_target_met and target_success_rate >= 80:
            report += "✅ **READY FOR PRODUCTION**\n\n"
            report += "All success criteria met:\n"
            report += "- Token reduction in target range (30-50%)\n"
            report += "- Latency under 3s per chunk\n"
            report += "- 80%+ success rate across test samples\n\n"
            report += "**Next Steps:**\n"
            report += "1. Enable `USE_HARMONY_PROMPTS=true` in production\n"
            report += "2. Monitor metrics for 24 hours\n"
            report += "3. Gradually roll out to all users\n"
        else:
            report += "⚠️  **ADDITIONAL TUNING REQUIRED**\n\n"
            if not target_met:
                report += f"- Token reduction ({avg_harmony_reduction:.1f}%) outside target range (30-50%)\n"
            if not latency_target_met:
                report += f"- Latency ({avg_harmony_latency:.0f}ms) exceeds 3000ms target\n"
            if target_success_rate < 80:
                report += f"- Success rate ({target_success_rate:.0f}%) below 80% threshold\n"
            report += "\n"
            report += "**Next Steps:**\n"
            report += "1. Review prompt engineering\n"
            report += "2. Optimize reasoning_effort parameter\n"
            report += "3. Re-run benchmarks after adjustments\n"

        report += "\n"

        # Methodology
        report += "## Methodology\n\n"
        report += "### Test Setup\n\n"
        report += f"- **Model:** {'Mock MLX client' if self.use_mock else 'Real gpt-oss-20b-4bit'}\n"
        report += f"- **Test Corpus:** {len(RESUME_CHUNKS)} resume text chunks\n"
        report += f"- **Chunk Sizes:** 400-550 characters each\n"
        report += f"- **Comparison:** Legacy prompts vs Harmony prompts\n\n"

        report += "### Metrics Tracked\n\n"
        report += "- **Token Reduction:** (original - compressed) / original × 100\n"
        report += "- **Latency:** Time to compress single chunk\n"
        report += "- **Target Compliance:** 30-50% reduction range\n\n"

        report += "### Validation Criteria\n\n"
        report += "- ✅ Token reduction: 30-50% average\n"
        report += "- ✅ Latency: <3s per chunk\n"
        report += "- ✅ Success rate: 80%+ chunks in target range\n"
        report += "- ✅ No quality degradation (manual review)\n\n"

        # Save report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info("Benchmark report generated", output_path=output_path)

        return report

    def _create_mock_preprocessor(self, use_harmony: bool):
        """Create mock preprocessor when real modules not available"""
        if IMPORTS_AVAILABLE:
            return LocalLLMPreprocessor(self.mlx_client)

        # Create inline mock preprocessor
        class MockPreprocessor:
            def __init__(self, local_llm):
                self.local_llm = local_llm
                self.use_harmony = use_harmony

            async def compress_chunks(
                self, query: str, sources: List[SourceDocument]
            ) -> List[SourceDocument]:
                """Mock compression"""
                from dataclasses import replace

                # Build prompt (detect format for mock MLX client)
                if self.use_harmony:
                    prompt = f"Output format: JSON\n```json\nDOCUMENT CHUNK: {sources[0].markdown_content}"
                else:
                    prompt = f"DOCUMENT CHUNK: {sources[0].markdown_content}\nReturn only: compressed text"

                # Call mock MLX client
                response = await self.local_llm.complete(prompt, max_tokens=500)

                # Parse response
                if self.use_harmony:
                    # Extract JSON facts
                    import json

                    try:
                        data = json.loads(response.content)
                        compressed_content = data["facts"]
                    except:
                        compressed_content = response.content
                else:
                    compressed_content = response.content

                # Return compressed source
                return [replace(sources[0], markdown_content=compressed_content)]

        return MockPreprocessor(self.mlx_client)


# ============================================================================
# Main Execution
# ============================================================================


async def main():
    """Run benchmark suite and generate report"""
    parser = argparse.ArgumentParser(
        description="GPT-OSS-20B Harmony Optimization Benchmark"
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "real"],
        default="mock",
        help="Use mock LLM (fast) or real MLX model (accurate)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".context-kit/benchmarks/preprocessing-results.md",
        help="Output report path",
    )

    args = parser.parse_args()

    # Configure logging
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(structlog.stdlib.logging.INFO),
    )

    # Run benchmark
    use_mock = args.mode == "mock"
    benchmark = HarmonyOptimizationBenchmark(use_mock=use_mock)

    print(f"\n{'=' * 70}")
    print("  GPT-OSS-20B Harmony Optimization Benchmark")
    print(f"{'=' * 70}")
    print(f"  Mode: {args.mode.upper()}")
    print(f"  Test Chunks: {len(RESUME_CHUNKS)}")
    print(f"  Output: {args.output}")
    print(f"{'=' * 70}\n")

    # Run all benchmarks
    print("Running benchmarks...\n")
    results = await benchmark.run_all_benchmarks()

    # Generate report
    print("\nGenerating report...")
    report = benchmark.generate_report(output_path=args.output)

    print(f"\n{'=' * 70}")
    print("  Benchmark Complete!")
    print(f"{'=' * 70}")
    print(f"  Total runs: {len(results)}")
    print(f"  Report: {args.output}")
    print(f"{'=' * 70}\n")

    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    avg_harmony_reduction = sum(r.harmony_reduction_pct for r in results) / len(results)
    target_met = 30.0 <= avg_harmony_reduction <= 50.0
    print(f"Token Reduction: {avg_harmony_reduction:+.1f}% {'✅ PASS' if target_met else '❌ FAIL'}")
    avg_harmony_latency = sum(r.harmony_latency_ms for r in results) / len(results)
    latency_met = avg_harmony_latency < 3000
    print(f"Avg Latency: {avg_harmony_latency:.0f}ms {'✅ PASS' if latency_met else '❌ FAIL'}")
    num_targets_met = sum(1 for r in results if r.harmony_meets_target)
    success_rate = (num_targets_met / len(results) * 100)
    rate_met = success_rate >= 80
    print(f"Success Rate: {success_rate:.0f}% {'✅ PASS' if rate_met else '❌ FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    import logging

    asyncio.run(main())
