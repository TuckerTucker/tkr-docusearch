/**
 * Download Utilities
 *
 * Helper functions for downloading files (markdown, VTT, generic).
 *
 * Wave 1 - Foundation Agent
 */

/**
 * Download markdown file for a document
 * @param {string} docId - Document identifier
 * @param {HTMLElement} buttonElement - Button that triggered the download (for feedback)
 */
export async function downloadMarkdown(docId, buttonElement) {
    try {
        const url = `/documents/${docId}/markdown`;

        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = ''; // Filename from server
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Visual feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✓ Downloaded!';
            buttonElement.classList.add('success');

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
                buttonElement.classList.remove('success');
            }, 2000);
        }

        console.log('Markdown download initiated');
    } catch (err) {
        console.error('Failed to download markdown:', err);

        // Error feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✗ Failed';

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
            }, 2000);
        }
    }
}

/**
 * Download VTT file for an audio document
 * @param {string} docId - Document identifier
 * @param {HTMLElement} buttonElement - Button that triggered the download (for feedback)
 */
export async function downloadVTT(docId, buttonElement) {
    try {
        const url = `/documents/${docId}/vtt`;

        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = ''; // Filename from server
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Visual feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✓ Downloaded!';
            buttonElement.classList.add('success');

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
                buttonElement.classList.remove('success');
            }, 2000);
        }

        console.log('VTT download initiated');
    } catch (err) {
        console.error('Failed to download VTT:', err);

        // Error feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✗ Failed';

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
            }, 2000);
        }
    }
}

/**
 * Download text as a file
 * @param {string} text - Text content to download
 * @param {string} filename - Filename for download
 * @param {string} mimeType - MIME type (default: text/plain)
 */
export function downloadTextAsFile(text, filename, mimeType = 'text/plain') {
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up object URL
    URL.revokeObjectURL(url);

    console.log(`Downloaded: ${filename}`);
}

/**
 * Generic file download function
 * @param {string} url - URL to download from
 * @param {string} filename - Optional filename for download
 */
export function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    if (filename) {
        link.download = filename;
    }
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Download research report as markdown file
 * @param {string} query - Research query
 * @param {string} answer - AI-generated answer with citations
 * @param {Array<Object>} references - Array of source references
 * @param {Object} metadata - Research metadata (timing, model info)
 */
export function downloadResearchMarkdown(query, answer, references, metadata) {
    const timestamp = new Date().toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    // Convert relative thumbnail path to absolute filesystem path
    const toAbsolutePath = (thumbnailPath) => {
        if (!thumbnailPath) return 'N/A';
        // Remove leading slash if present
        const relativePath = thumbnailPath.startsWith('/') ? thumbnailPath.slice(1) : thumbnailPath;
        return `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/images/${relativePath}`;
    };

    // Calculate costs
    const inputCost = metadata?.llm_usage_details?.prompt_tokens
        ? (metadata.llm_usage_details.prompt_tokens / 1_000_000) * 10.0
        : 0;
    const outputCost = metadata?.llm_usage_details?.completion_tokens
        ? (metadata.llm_usage_details.completion_tokens / 1_000_000) * 30.0
        : 0;
    const totalCost = inputCost + outputCost;

    // Build markdown content
    let markdown = `# Research Report: ${query}\n\n`;
    markdown += `**Generated:** ${timestamp}\n`;
    markdown += `**Model:** ${metadata?.model_used || 'Unknown'}\n`;
    markdown += `**Total Time:** ${metadata?.processing_time_ms || 'N/A'}ms\n`;
    markdown += `**LLM Time:** ${metadata?.llm_latency_ms || 'N/A'}ms\n`;
    markdown += `**Cost:** $${totalCost.toFixed(4)}\n\n`;

    markdown += `---\n\n`;
    markdown += `## Answer\n\n`;
    markdown += `${answer}\n\n`;

    // Add Inference Flow Debug section
    if (metadata) {
        markdown += `---\n\n`;
        markdown += `## Inference Flow Debug\n\n`;

        // Overview / Request Flow
        markdown += `### Request Flow\n\n`;
        markdown += `#### 1. Search & Context Building\n`;
        markdown += `- Retrieved ${metadata.total_sources || 0} sources in ${metadata.search_latency_ms || 0}ms\n`;
        markdown += `- Context: ${metadata.context_tokens || 0} tokens${metadata.context_truncated ? ' (truncated)' : ''}\n\n`;

        if (metadata.preprocessing_enabled) {
            markdown += `#### 2. Local LLM Preprocessing\n`;
            markdown += `- Strategy: ${metadata.preprocessing_strategy} (${metadata.preprocessing_latency_ms}ms)\n`;
            markdown += `- Token reduction: ${metadata.token_reduction_percent?.toFixed(1)}%\n\n`;
        }

        markdown += `#### ${metadata.preprocessing_enabled ? '3' : '2'}. Foundation LLM Request\n`;
        markdown += `- Model: ${metadata.model_used} (temp: ${metadata.llm_request_params?.temperature || 'N/A'})\n`;
        markdown += `- Input: ${metadata.llm_usage_details?.prompt_tokens || 0} tokens`;
        if (metadata.vision_enabled) {
            markdown += ` + ${metadata.images_sent} images (~${metadata.image_tokens} tokens)`;
        }
        markdown += `\n- Latency: ${metadata.llm_latency_ms}ms\n\n`;

        markdown += `#### ${metadata.preprocessing_enabled ? '4' : '3'}. Response & Citation Parsing\n`;
        markdown += `- Output: ${metadata.llm_usage_details?.completion_tokens || 0} tokens\n`;
        markdown += `- Total tokens: ${metadata.llm_usage_details?.total_tokens || 0}\n`;
        markdown += `- Cost: $${totalCost.toFixed(4)}\n\n`;

        // System Prompt
        markdown += `### System Prompt\n\n`;
        markdown += `\`\`\`\n${metadata.system_prompt || 'Not available'}\n\`\`\`\n\n`;

        // User Prompt
        markdown += `### User Prompt\n\n`;
        markdown += `Full prompt including formatted context and user query.\n\n`;
        markdown += `\`\`\`\n${metadata.user_prompt || 'Not available'}\n\`\`\`\n\n`;
        markdown += `- Length: ${metadata.user_prompt?.length.toLocaleString() || 0} chars\n`;
        markdown += `- Tokens: ~${metadata.context_tokens || 0}\n\n`;

        // Context Only
        markdown += `### Formatted Context Only\n\n`;
        if (metadata.preprocessing_enabled) {
            markdown += `Final compressed context sent to foundation model (after MLX preprocessing).\n\n`;
        } else {
            markdown += `Retrieved document chunks formatted for the LLM (without query).\n\n`;
        }
        markdown += `\`\`\`\n${metadata.formatted_context || 'Not available'}\n\`\`\`\n\n`;
        markdown += `- Sources: ${metadata.total_sources || 0}\n`;
        markdown += `- Tokens: ${metadata.context_tokens || 0}\n`;
        if (metadata.context_truncated) {
            markdown += `- ⚠️ Context was truncated\n`;
        }
        if (metadata.preprocessing_enabled) {
            markdown += `- ✓ Compressed by ${metadata.preprocessing_model}\n`;
        }
        markdown += `\n`;

        // MLX Preprocessing (if enabled)
        if (metadata.preprocessing_enabled) {
            markdown += `### MLX Preprocessing\n\n`;
            markdown += `- **Model:** ${metadata.preprocessing_model}\n`;
            markdown += `- **Strategy:** ${metadata.preprocessing_strategy}\n`;
            markdown += `- **Latency:** ${metadata.preprocessing_latency_ms}ms\n`;
            markdown += `- **Token Reduction:** -${metadata.token_reduction_percent?.toFixed(1)}%\n\n`;

            // Before/After
            markdown += `#### Context Transformation\n\n`;
            markdown += `**Before MLX Preprocessing** (${metadata.preprocessing_original_context?.length || 0} chars):\n`;
            markdown += `\`\`\`\n${metadata.preprocessing_original_context || 'Not available'}\n\`\`\`\n\n`;
            markdown += `**After MLX Preprocessing** (${metadata.preprocessing_compressed_context?.length || 0} chars):\n`;
            markdown += `\`\`\`\n${metadata.preprocessing_compressed_context || 'Not available'}\n\`\`\`\n\n`;
            markdown += `- Original: ${metadata.preprocessing_original_context?.length.toLocaleString() || 0} chars\n`;
            markdown += `- Compressed: ${metadata.preprocessing_compressed_context?.length.toLocaleString() || 0} chars\n`;
            markdown += `- Reduction: ${metadata.token_reduction_percent?.toFixed(1)}% fewer tokens\n`;
            markdown += `- Processing Time: ${metadata.preprocessing_latency_ms}ms\n\n`;
        }

        // Images (if vision enabled)
        if (metadata.image_urls_sent && metadata.image_urls_sent.length > 0) {
            markdown += `### Images (${metadata.images_sent})\n\n`;
            markdown += `Visual sources sent for multimodal analysis (~${metadata.image_tokens} tokens)\n\n`;
            metadata.image_urls_sent.forEach((url, idx) => {
                markdown += `${idx + 1}. ${url}\n`;
            });
            markdown += `\n`;
        }

        // Raw Response
        markdown += `### Raw LLM Response\n\n`;
        markdown += `Unprocessed response from the foundation model before citation parsing.\n\n`;
        markdown += `\`\`\`\n${metadata.llm_raw_response || 'Not available'}\n\`\`\`\n\n`;
        markdown += `- Length: ${metadata.llm_raw_response?.length.toLocaleString() || 0} chars\n`;
        markdown += `- Tokens: ${metadata.llm_usage_details?.completion_tokens || 0}\n\n`;

        // Parameters
        markdown += `### Parameters\n\n`;
        markdown += `| Parameter | Value |\n`;
        markdown += `|-----------|-------|\n`;
        markdown += `| Model | ${metadata.model_used} |\n`;
        markdown += `| Temperature | ${metadata.llm_request_params?.temperature || 'N/A'} |\n`;
        markdown += `| Max Tokens | ${metadata.llm_request_params?.max_tokens || 'N/A'} |\n`;
        markdown += `| Search Mode | ${metadata.search_mode || 'N/A'} |\n`;
        markdown += `| Vision Enabled | ${metadata.vision_enabled ? 'Yes' : 'No'} |\n`;
        if (metadata.vision_enabled) {
            markdown += `| Images Sent | ${metadata.images_sent} |\n`;
            markdown += `| Image Tokens (est.) | ${metadata.image_tokens} |\n`;
        }
        markdown += `| Preprocessing | ${metadata.preprocessing_enabled ? `${metadata.preprocessing_strategy} (${metadata.preprocessing_latency_ms}ms)` : 'Disabled'} |\n\n`;

        markdown += `**Timing Breakdown:**\n\n`;
        markdown += `| Stage | Time |\n`;
        markdown += `|-------|------|\n`;
        markdown += `| Search & Context | ${metadata.search_latency_ms}ms |\n`;
        if (metadata.preprocessing_enabled) {
            markdown += `| Local Preprocessing | ${metadata.preprocessing_latency_ms}ms |\n`;
        }
        markdown += `| LLM Inference | ${metadata.llm_latency_ms}ms |\n`;
        markdown += `| **Total** | **${metadata.processing_time_ms}ms** |\n\n`;
    }

    // Sources
    if (references && references.length > 0) {
        markdown += `---\n\n`;
        markdown += `## Sources\n\n`;

        references.forEach((ref) => {
            markdown += `### [${ref.id}] ${ref.filename} (Page ${ref.page || 1})\n\n`;
            markdown += `**Document ID:** ${ref.doc_id || 'N/A'}\n`;
            markdown += `**Extension:** ${ref.extension || 'pdf'}\n`;
            markdown += `**Date Added:** ${ref.date_added ? new Date(ref.date_added).toLocaleDateString() : 'N/A'}\n`;
            markdown += `**Thumbnail Path:** ${toAbsolutePath(ref.thumbnail_path)}\n\n`;
        });
    }

    markdown += `---\n\n`;
    markdown += `*Report generated by tkr-docusearch Research Bot*\n`;

    // Generate filename from query
    const sanitizedQuery = query
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 50);
    const filename = `research-${sanitizedQuery}-${Date.now()}.md`;

    downloadTextAsFile(markdown, filename, 'text/markdown');
    console.log(`Research report downloaded: ${filename}`);
}
