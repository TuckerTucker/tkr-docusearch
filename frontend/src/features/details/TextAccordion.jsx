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
 * Parse VTT content into readable transcript
 * Converts WebVTT format to plain text with timestamps
 *
 * @param {string} vttText - Raw VTT file content
 * @returns {string} Formatted transcript with timestamps
 */
function parseVTT(vttText) {
  if (!vttText) return '';

  const lines = vttText.split('\n');
  const segments = [];
  let currentTimestamp = '';
  let currentText = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Skip WEBVTT header and NOTE lines
    if (line.startsWith('WEBVTT') || line.startsWith('NOTE')) {
      continue;
    }

    // Check if line is a timestamp (HH:MM:SS.mmm --> HH:MM:SS.mmm)
    if (line.includes('-->')) {
      // Extract start time only
      const startTime = line.split('-->')[0].trim();
      currentTimestamp = startTime;
      continue;
    }

    // Skip cue identifiers (numeric lines before timestamps)
    if (line && /^\d+$/.test(line)) {
      continue;
    }

    // Skip empty lines
    if (!line) {
      // If we have accumulated text, save the segment
      if (currentText && currentTimestamp) {
        segments.push(`[${currentTimestamp}] ${currentText}`);
        currentText = '';
        currentTimestamp = '';
      }
      continue;
    }

    // Accumulate caption text
    currentText += (currentText ? ' ' : '') + line;
  }

  // Don't forget the last segment
  if (currentText && currentTimestamp) {
    segments.push(`[${currentTimestamp}] ${currentText}`);
  }

  return segments.join('\n\n');
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
 * @param {number} [props.currentPage] - Current page number (for slideshow sync)
 */
export default function TextAccordion({
  document,
  markdown,
  chunks = [],
  onTimestampClick,
  onPageClick,
  activeChunk,
  currentPage
}) {
  const [sections, setSections] = useState([]);
  const [activeSectionId, setActiveSectionId] = useState(null);
  const [vttContent, setVttContent] = useState(null);

  // Update active section when active chunk changes (for audio sync)
  useEffect(() => {
    if (activeChunk) {
      setActiveSectionId(activeChunk.chunk_id);
    }
  }, [activeChunk]);

  // Update active section when current page changes (for slideshow sync)
  useEffect(() => {
    if (currentPage && sections && sections.length > 0) {
      // Find section with matching page number
      const matchingSection = sections.find(section => section.pageNumber === currentPage);
      if (matchingSection) {
        setActiveSectionId(matchingSection.id);
      }
    }
  }, [currentPage, sections]);

  // Fetch VTT content if available
  useEffect(() => {
    const metadata = document?.metadata || {};

    if (metadata.vtt_available && document.doc_id) {
      const fetchVTT = async () => {
        try {
          const response = await fetch(`/documents/${document.doc_id}/vtt`);
          if (response.ok) {
            const vttText = await response.text();
            const parsed = parseVTT(vttText);
            setVttContent(parsed);
            console.log('[TextAccordion] Loaded VTT transcript');
          } else {
            console.error('[TextAccordion] Failed to fetch VTT:', response.status);
            setVttContent('Failed to load VTT transcript.');
          }
        } catch (err) {
          console.error('[TextAccordion] Error fetching VTT:', err);
          setVttContent('Error loading VTT transcript.');
        }
      };

      fetchVTT();
    } else {
      setVttContent(null);
    }
  }, [document]);

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
      // Use fetched VTT content or show loading message
      const content = vttContent !== null
        ? vttContent
        : 'Loading VTT transcript...';

      newSections.push({
        id: 'vtt-transcript',
        title: 'VTT Transcript',
        content: content,
        timestamp: null
      });
    }

    // Section 3: Per-chunk sections
    if (chunks && chunks.length > 0) {
      // Determine if this is a visual document with pages
      const hasPages = document?.pages && document.pages.length > 0;
      const pageCount = hasPages ? document.pages.length : 0;

      chunks.forEach((chunk, index) => {
        const hasTimestamp = chunk.has_timestamps &&
          chunk.start_time !== null &&
          chunk.end_time !== null;

        // For visual documents (PDF/PPTX), infer page number from chunk index
        // Assumption: chunks are ordered by page (chunk 0 = page 1, chunk 1 = page 2, etc.)
        let inferredPageNumber = null;
        if (hasPages && chunks.length === pageCount) {
          // 1:1 mapping between chunks and pages
          inferredPageNumber = index + 1;
        }

        let title;
        let pageNumber = chunk.page_number || inferredPageNumber;

        if (hasTimestamp) {
          title = `Segment ${index + 1}`;
        } else if (pageNumber) {
          title = `Page ${pageNumber}`;
        } else {
          title = `Chunk ${index + 1}`;
        }

        newSections.push({
          id: chunk.chunk_id,
          title,
          content: chunk.text_content || '',
          timestamp: hasTimestamp ? {
            start: chunk.start_time,
            end: chunk.end_time
          } : null,
          pageNumber: pageNumber
        });
      });
    }

    setSections(newSections);
  }, [document, markdown, chunks, vttContent]);

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
