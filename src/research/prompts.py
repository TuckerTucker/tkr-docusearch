"""
Prompt Engineering for Research Bot.

Provides optimized system prompts and templates for LLM research queries.
"""

from typing import Optional

# Research system prompt
RESEARCH_SYSTEM_PROMPT = """You are a research assistant helping users find information from their document collection.

RULES:
1. Answer ONLY using information from the provided context
2. If the context doesn't contain enough information, say so clearly
3. Cite sources using [N] where N is the document number
4. Place citations immediately after the relevant facts
5. Be concise but complete - aim for 2-3 paragraphs
6. Use clear, professional language
7. Do not add information not present in the context

VISUAL ANALYSIS (when images are provided):
- Some sources are marked [Visual Match] - these were found via visual similarity search
- When analyzing visual sources, describe visual elements you observe: charts, diagrams, tables, layouts
- Extract information from visual elements that may not be fully captured in text
- Cite visual elements explicitly: "The bar chart in [1] shows..." or "The diagram in [2] illustrates..."
- Visual sources often contain charts, graphs, and diagrams - analyze these carefully

CITATION FORMAT:
- Correct: "Paris is the capital of France [1]."
- Incorrect: "Paris is the capital of France. [1]"
- Multiple sources: "This is supported by research [1][2]."
- When multiple documents say the same thing, cite all: [1][2][3]
- For visual elements: "The chart shows revenue growth of 30% [1]."

ANSWERING GUIDELINES:
- Start with a direct answer to the question
- Provide supporting details from the sources
- If information is incomplete, acknowledge what's missing
- If sources conflict, present both perspectives with citations
- When images are available, prioritize visual information that answers the query

TONE:
- Professional and informative
- Objective and factual
- Helpful without speculation
"""

# Alternative prompts for different use cases
CONCISE_SYSTEM_PROMPT = """You are a research assistant. Answer questions using ONLY the provided context.

Rules:
1. Cite all facts using [N] format
2. Keep answers to 1-2 sentences
3. Be direct and concise
4. Don't add information not in context
"""

DETAILED_SYSTEM_PROMPT = """You are an expert research assistant analyzing document collections.

Your task is to provide comprehensive, well-cited answers to research questions. Follow these guidelines:

CITATION REQUIREMENTS:
- Every fact MUST have a citation [N]
- Place citations immediately after claims: "Fact [1]."
- Multiple sources: "Fact [1][2]."
- Be generous with citations - when in doubt, cite

ANSWER STRUCTURE:
1. Opening: Direct answer (1-2 sentences)
2. Body: Supporting evidence from sources (2-4 paragraphs)
3. Conclusion: Summary or implications (optional)

QUALITY STANDARDS:
- Only use information explicitly stated in context
- If context is insufficient, state: "The provided documents do not contain sufficient information about..."
- If sources conflict, present both views: "Document 1 states X [1], while Document 2 indicates Y [2]."
- Maintain objectivity - don't editorialize

FORBIDDEN:
- Do not use external knowledge
- Do not speculate beyond the text
- Do not make assumptions
"""


class PromptTemplates:
    """Prompt template management."""

    @staticmethod
    def get_system_prompt(style: str = "standard") -> str:
        """
        Get system prompt by style.

        Args:
            style: "standard", "concise", or "detailed"

        Returns:
            System prompt string
        """
        styles = {
            "standard": RESEARCH_SYSTEM_PROMPT,
            "concise": CONCISE_SYSTEM_PROMPT,
            "detailed": DETAILED_SYSTEM_PROMPT,
        }

        return styles.get(style, RESEARCH_SYSTEM_PROMPT)

    @staticmethod
    def build_query_prompt(query: str, context: str, max_words: Optional[int] = None) -> str:
        """
        Build complete prompt with query and context.

        Args:
            query: User's research question
            context: Formatted context from ContextBuilder
            max_words: Optional word limit for answer

        Returns:
            Complete prompt string
        """
        prompt = f"{context}\n\n"

        if max_words:
            prompt += f"Query (answer in ~{max_words} words): {query}"
        else:
            prompt += f"Query: {query}"

        return prompt

    @staticmethod
    def get_fallback_prompt() -> str:
        """
        Get fallback prompt when no sources found.

        Returns:
            Fallback system prompt
        """
        return """You are a helpful assistant. The user asked a question but no relevant documents were found in their collection.

Politely explain that:
1. No documents in their collection match this query
2. They may need to upload relevant documents
3. They can try rephrasing their question

Be brief and helpful."""


# Example usage prompts
EXAMPLE_QUERIES = {
    "factual": "What caused the 2008 financial crisis?",
    "comparison": "How do solar and wind energy compare in terms of cost?",
    "process": "What are the steps in the document review process?",
    "definition": "What is quantum computing?",
    "analysis": "What are the key findings in the climate report?",
}


def get_example_query(query_type: str = "factual") -> str:
    """Get example query by type."""
    return EXAMPLE_QUERIES.get(query_type, EXAMPLE_QUERIES["factual"])


# ============================================================================
# Preprocessing Prompts for Local LLM Strategies
# ============================================================================

CHUNK_COMPRESSION_PROMPT = """You are a research assistant extracting key information from document chunks.

TASK: Extract the key facts from this document chunk that are relevant to the user's query.

RULES:
1. Preserve specific numbers, dates, names, and technical details exactly
2. Remove boilerplate, introductory text, and tangential information
3. Maintain factual accuracy - do not infer or add information
4. Keep the summary dense and concise (aim for 30-50% of original length)
5. Preserve context needed for citations (page numbers, section references)

OUTPUT FORMAT:
Provide ONLY the compressed facts. Do not include meta-commentary like "This document discusses..." or "The key points are...". Start directly with the factual content.

QUERY: {query}

DOCUMENT CHUNK:
{chunk_content}

COMPRESSED FACTS:"""

VISUAL_CHUNK_COMPRESSION_PROMPT = """You are a research assistant extracting key information from document chunks.

TASK: Extract the key facts from this document chunk that are relevant to the user's query.

RULES:
1. Preserve specific numbers, dates, names, and technical details exactly
2. Remove boilerplate, introductory text, and tangential information
3. Maintain factual accuracy - do not infer or add information
4. Keep the summary concise (aim for 50-60% of original length)
5. Preserve context needed for citations (page numbers, section references)
6. **CRITICAL: Preserve ALL references to visual elements**:
   - Keep "Figure N", "Table N", "Chart", "Diagram", "Graph" references intact
   - Maintain descriptions like "the chart shows", "as illustrated in", "see diagram"
   - Preserve visual element context (e.g., "the bar chart demonstrates...")

OUTPUT FORMAT:
Provide ONLY the compressed facts. Do not include meta-commentary like "This document discusses..." or "The key points are...". Start directly with the factual content.

QUERY: {query}

DOCUMENT CHUNK:
{chunk_content}

COMPRESSED FACTS:"""

RELEVANCE_SCORING_PROMPT = """You are evaluating the relevance of a document chunk to a specific query.

TASK: Rate this chunk's relevance on a scale of 0-10.

SCORING GUIDE:
- 10: Directly answers the query with specific, detailed information
- 7-9: Contains relevant information but may be incomplete or tangential
- 4-6: Related topic but doesn't directly address the query
- 1-3: Mentions query terms but provides minimal useful information
- 0: Completely irrelevant to the query

CONSIDER:
- Direct information vs tangential mentions
- Specificity and detail level
- Completeness of information for answering the query
- Factual content vs boilerplate text

QUERY: {query}

DOCUMENT CHUNK:
{chunk_content}

Provide ONLY a single number from 0-10. No explanation.

SCORE:"""

KNOWLEDGE_SYNTHESIS_PROMPT = """You are a research assistant synthesizing information from multiple document chunks.

TASK: Organize key information by theme, preserving source citations.

RULES:
1. Group related facts together by theme
2. CRITICAL: Cite sources using [N] format for every fact
3. Note contradictions if documents disagree
4. Note gaps if query aspects are unanswered

OUTPUT FORMAT:
## Theme 1: [Topic Name]
- Fact: [statement] (Sources: [1], [3])
- Fact: [statement] (Source: [2])

## Contradictions (if any):
- [Document 1] states X, but [Document 3] states Y

## Information Gaps (if any):
- No information found about [aspect]

QUERY: {query}

DOCUMENT CHUNKS:
{numbered_chunks}

SYNTHESIZED KNOWLEDGE:"""


# ============================================================================
# Harmony-Format Prompts for GPT-OSS-20B Optimization
# ============================================================================

HARMONY_CHUNK_COMPRESSION_PROMPT = """<|start|>developer<|message|># Instructions
Compress text to key facts. Remove redundancy.
Output JSON: {{"facts": "compressed text"}}
Target: 50% reduction. Reasoning: low

Example:
Input: "The quarterly report shows strong performance. Revenue increased 15% year-over-year to $2.5M. The CEO noted positive market conditions and improved profit margins from 8% to 12%."
Output: {{"facts": "Revenue +15% YoY to $2.5M. Profit margins 8%→12%. CEO cited positive market."}}
<|end|><|start|>user<|message|>
Query: {query}

Text:
{chunk_content}
<|end|><|start|>assistant"""

HARMONY_BATCH_COMPRESSION_PROMPT = """<|start|>developer<|message|># Task
Compress document chunks to key facts. Output ONLY valid JSON array.
Format: [{{"chunk_id": N, "facts": "text"}}, ...]
NO reasoning. NO explanation. ONLY JSON output.

# Example
Input:
[1] File.pdf, Page 1
Revenue increased 15% to $2.5M. CEO noted positive market conditions.

[2] Report.pdf, Page 2
Profit margins improved from 8% to 12%. Strong quarterly performance.

Output:
[{{"chunk_id": 1, "facts": "Revenue +15% to $2.5M. CEO cited positive market."}}, {{"chunk_id": 2, "facts": "Margins 8%→12%. Strong quarter."}}]
<|end|><|start|>user<|message|>Query: {query}

{numbered_chunks}
<|end|><|start|>assistant
["""

HARMONY_RELEVANCE_SCORING_PROMPT = """<|start|>developer<|message|># Instructions
Score text relevance to query (0-10).
Output JSON: {{"score": N}}
Reasoning: low
<|end|><|start|>user<|message|>
Query: {query}

Text:
{chunk_content}
<|end|><|start|>assistant"""

HARMONY_SYNTHESIS_PROMPT = """<|start|>developer<|message|># Task
Synthesize ALL document chunks into ONE comprehensive summary.
Include ALL key facts from ALL sources, including visual match text.
Preserve source references using [N] format where N is the document number.
NO reasoning. Output ONLY the synthesized summary.

# Requirements
- Combine information from all sources into a cohesive narrative
- Remove redundancy and duplicates across sources
- Preserve all specific details (names, dates, numbers, locations)
- Maintain source citations [N] after each fact
- Be comprehensive - include information from ALL sources
- Target: 50-70% token reduction vs sending all chunks individually

# Example
Input:
[1] Resume.pdf, Page 1
John Smith, email: john@example.com. Lead Engineer at TechCorp (2020-2023).

[2] Resume.pdf, Page 2
TechCorp revenue $50M in 2022. John led team of 15 engineers. Prior: Senior Dev at StartupXYZ (2018-2020).

[3] LinkedIn.pdf, Page 1
John Smith graduated MIT 2018. Contact: john@example.com.

Output:
John Smith is a Lead Engineer with email john@example.com [1][3]. He graduated from MIT in 2018 [3]. His career includes Lead Engineer at TechCorp (2020-2023), where he led a team of 15 engineers [1][2]. TechCorp had $50M revenue in 2022 [2]. Previously, he was a Senior Developer at StartupXYZ (2018-2020) [2].
<|end|><|start|>user<|message|>Query: {query}

Document chunks:
{numbered_chunks}
<|end|><|start|>assistant
"""

HARMONY_CHAT_PROMPT = """<|start|>developer<|message|># Instructions
You are a helpful AI assistant.
Respond naturally to user questions and prompts.
Be concise, factual, and helpful.
Reasoning: low
<|end|><|start|>user<|message|>
{prompt}
<|end|><|start|>assistant"""


# JSON Schema Definitions for Harmony Response Validation
COMPRESSION_SCHEMA = {
    "type": "object",
    "required": ["facts"],
    "properties": {"facts": {"type": "string", "minLength": 1}},
}

RELEVANCE_SCHEMA = {
    "type": "object",
    "required": ["score"],
    "properties": {"score": {"type": "integer", "minimum": 0, "maximum": 10}},
}


class PreprocessingPrompts:
    """Prompt template management for preprocessing strategies."""

    @staticmethod
    def get_compression_prompt(
        query: str, chunk_content: str, has_visual_dependency: bool = False
    ) -> str:
        """
        Build compression prompt with query and chunk.

        Args:
            query: User's research question
            chunk_content: Document chunk text to compress
            has_visual_dependency: If True, uses visual-preserving compression prompt

        Returns:
            Formatted prompt string ready for LLM
        """
        template = (
            VISUAL_CHUNK_COMPRESSION_PROMPT if has_visual_dependency else CHUNK_COMPRESSION_PROMPT
        )
        return template.format(query=query, chunk_content=chunk_content)

    @staticmethod
    def get_relevance_prompt(query: str, chunk_content: str) -> str:
        """
        Build relevance scoring prompt.

        Args:
            query: User's research question
            chunk_content: Document chunk text to score

        Returns:
            Formatted prompt string ready for LLM
        """
        return RELEVANCE_SCORING_PROMPT.format(query=query, chunk_content=chunk_content)

    @staticmethod
    def get_synthesis_prompt(query: str, numbered_chunks: str) -> str:
        r"""
        Build knowledge synthesis prompt.

        Args:
            query: User's research question
            numbered_chunks: All chunks formatted as "[1] content\n[2] content\n..."

        Returns:
            Formatted prompt string ready for LLM
        """
        return KNOWLEDGE_SYNTHESIS_PROMPT.format(query=query, numbered_chunks=numbered_chunks)

    @staticmethod
    def format_numbered_chunks(sources: list) -> str:
        r"""
        Format sources as numbered chunks for synthesis.

        Args:
            sources: List of SourceDocument objects

        Returns:
            Formatted string: "[1] content\n\n[2] content\n\n..."
        """
        formatted_parts = []
        for i, source in enumerate(sources, start=1):
            formatted_parts.append(
                f"[{i}] {source.filename}, Page {source.page}\n{source.markdown_content}"
            )
        return "\n\n".join(formatted_parts)

    @staticmethod
    def get_harmony_compression_prompt(query: str, chunk_content: str) -> str:
        """
        Build Harmony-format compression prompt with query and chunk.

        This prompt uses the Harmony chat format (<|start|>role<|message|>...<|end|>)
        optimized for GPT-OSS-20B model. Instructs model to compress text to key facts
        and output JSON format with 50% reduction target.

        Args:
            query: User's research question
            chunk_content: Document chunk text to compress

        Returns:
            Formatted Harmony-format prompt string ready for GPT-OSS-20B
        """
        return HARMONY_CHUNK_COMPRESSION_PROMPT.format(query=query, chunk_content=chunk_content)

    @staticmethod
    def get_harmony_relevance_prompt(query: str, chunk_content: str) -> str:
        """
        Build Harmony-format relevance scoring prompt.

        This prompt uses the Harmony chat format (<|start|>role<|message|>...<|end|>)
        optimized for GPT-OSS-20B model. Instructs model to score text relevance
        to query on 0-10 scale and output JSON format.

        Args:
            query: User's research question
            chunk_content: Document chunk text to score

        Returns:
            Formatted Harmony-format prompt string ready for GPT-OSS-20B
        """
        return HARMONY_RELEVANCE_SCORING_PROMPT.format(query=query, chunk_content=chunk_content)

    @staticmethod
    def get_harmony_chat_prompt(prompt: str) -> str:
        """
        Build Harmony-format chat prompt for general inference.

        This prompt wraps user input in Harmony chat format for better structured responses.
        Prevents hallucination and code generation by providing clear task framing.

        Args:
            prompt: User's query or prompt

        Returns:
            Formatted Harmony-format prompt string ready for GPT-OSS-20B

        Example:
            >>> PreprocessingPrompts.get_harmony_chat_prompt("What is the capital of France?")
            '<|start|>developer<|message|># Instructions...'
        """
        return HARMONY_CHAT_PROMPT.format(prompt=prompt)

    @staticmethod
    def get_harmony_batch_compression_prompt(query: str, numbered_chunks: str) -> str:
        r"""
        Build Harmony-format batch compression prompt for processing multiple chunks at once.

        This prompt uses the Harmony chat format optimized for GPT-OSS-20B model.
        Instructs model to compress all chunks in a single pass, reducing redundant
        LLM calls and leveraging the model's 128K context window.

        Args:
            query: User's research question
            numbered_chunks: All chunks formatted as "[1] content\n[2] content\n..."

        Returns:
            Formatted Harmony-format prompt string ready for GPT-OSS-20B

        Example:
            >>> chunks = "[1] Revenue was $2.5M\n[2] Revenue grew 15%"
            >>> PreprocessingPrompts.get_harmony_batch_compression_prompt("Revenue?", chunks)
            '<|start|>developer<|message|># Instructions...'
        """
        return HARMONY_BATCH_COMPRESSION_PROMPT.format(query=query, numbered_chunks=numbered_chunks)

    @staticmethod
    def get_harmony_synthesis_prompt(query: str, numbered_chunks: str) -> str:
        r"""
        Build Harmony-format synthesis prompt for creating one summary from all sources.

        This prompt uses the Harmony chat format optimized for GPT-OSS-20B model.
        Instructs model to synthesize ALL sources (including visual match text) into
        a single comprehensive summary with source citations preserved.

        Args:
            query: User's research question
            numbered_chunks: All chunks formatted as "[1] file, page\ncontent\n[2]..."

        Returns:
            Formatted Harmony-format prompt string ready for GPT-OSS-20B

        Example:
            >>> chunks = "[1] File.pdf, Page 1\nRevenue $2.5M\n[2] Report.pdf, Page 2\nGrowth 15%"
            >>> PreprocessingPrompts.get_harmony_synthesis_prompt("Revenue?", chunks)
            '<|start|>developer<|message|># Task...'
        """
        return HARMONY_SYNTHESIS_PROMPT.format(query=query, numbered_chunks=numbered_chunks)
