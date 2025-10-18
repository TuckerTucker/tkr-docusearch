/**
 * TextAccordion Component
 *
 * Wrapper around Accordion that formats document chunks and markdown
 * into accordion sections with bidirectional sync support.
 *
 * Wave 2 - Details Agent
 */

import { useState, useEffect } from 'react';
import Accordion from '../../components/ui/Accordion.jsx';

/**
 * Strip YAML frontmatter from markdown
 */
function stripFrontmatter(markdown) {
  if (!markdown) return '';

  const lines = markdown.split('\n');

  if (lines[0] === '---') {
    const endIndex = lines.findIndex((line, index) => index > 0 && line === '---');

    if (endIndex !== -1) {
      return lines.slice(endIndex + 1).join('\n').trim();
    }
  }

  return markdown;
}

/**
 * Text accordion with chunk and markdown sections
 *
 * @param {Object} props - Component props
 * @param {Object} props.document - Document with metadata
 * @param {string} [props.markdown] - Full markdown content
 * @param {Array} [props.chunks=[]] - Text chunks with optional timestamps
 * @param {Function} [props.onTimestampClick] - Audio seek callback
 * @param {Function} [props.onPageClick] - Slideshow navigation callback
 * @param {Object} [props.activeChunk] - Currently active chunk (for audio sync)
 */
export default function TextAccordion({
  document,
  markdown,
  chunks = [],
  onTimestampClick,
  onPageClick,
  activeChunk
}) {
  const [sections, setSections] = useState([]);
  const [activeSectionId, setActiveSectionId] = useState(null);

  // Update active section when active chunk changes
  useEffect(() => {
    if (activeChunk) {
      setActiveSectionId(activeChunk.chunk_id);
    }
  }, [activeChunk]);

  // Build sections from markdown and chunks
  useEffect(() => {
    const newSections = [];

    // Section 1: Full markdown (if available)
    if (markdown) {
      newSections.push({
        id: 'markdown-full',
        title: 'Full Document',
        content: stripFrontmatter(markdown),
        timestamp: null
      });
    }

    // Section 2: VTT transcript (if available)
    const metadata = document?.metadata || {};
    if (metadata.vtt_available && document.doc_id) {
      // Note: VTT content is handled separately, we just show a placeholder
      newSections.push({
        id: 'vtt-transcript',
        title: 'VTT Transcript',
        content: 'VTT transcript available for download.',
        timestamp: null
      });
    }

    // Section 3: Per-chunk sections
    if (chunks && chunks.length > 0) {
      chunks.forEach((chunk, index) => {
        const hasTimestamp = chunk.has_timestamps &&
          chunk.start_time !== null &&
          chunk.end_time !== null;

        let title;
        if (hasTimestamp) {
          title = `Segment ${index + 1}`;
        } else {
          const pageNum = chunk.page_number || null;
          title = pageNum ? `Chunk ${index + 1} (Page ${pageNum})` : `Chunk ${index + 1}`;
        }

        newSections.push({
          id: chunk.chunk_id,
          title,
          content: chunk.text_content || '',
          timestamp: hasTimestamp ? {
            start: chunk.start_time,
            end: chunk.end_time
          } : null,
          pageNumber: chunk.page_number || null
        });
      });
    }

    setSections(newSections);
  }, [document, markdown, chunks]);

  // Handle timestamp click (for audio seeking)
  const handleTimestampClick = (timestamp) => {
    if (onTimestampClick) {
      onTimestampClick(timestamp);
    }
  };

  // Handle page click (for slideshow navigation)
  const handlePageClick = (pageNumber) => {
    if (onPageClick) {
      onPageClick(pageNumber);
    }
  };

  if (sections.length === 0) {
    return (
      <div className="text-accordion-empty">
        <p>No text content available for this document.</p>
      </div>
    );
  }

  return (
    <div className="text-accordion">
      <Accordion
        sections={sections}
        onTimestampClick={handleTimestampClick}
        onPageClick={handlePageClick}
        activeSectionId={activeSectionId}
      />
    </div>
  );
}
