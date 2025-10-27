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

      console.log(`[TextAccordion] Building sections - Pages: ${pageCount}, Chunks: ${chunks.length}`);
      console.log(`[TextAccordion] Sample chunk:`, chunks[0]);

      chunks.forEach((chunk, index) => {
        const hasTimestamp = chunk.has_timestamps &&
          chunk.start_time !== null &&
          chunk.end_time !== null;

        // Extract page number from chunk metadata
        // Check multiple possible locations for page number
        let pageNumber = null;

        // First try: Direct page_number field
        if (chunk.page_number) {
          pageNumber = chunk.page_number;
        }
        // Second try: Metadata object
        else if (chunk.metadata?.page_number) {
          pageNumber = chunk.metadata.page_number;
        }
        // Third try: For visual documents, infer from chunk index if chunks match pages 1:1
        else if (hasPages && chunks.length === pageCount) {
          pageNumber = index + 1;
        }
        // Fourth try: Extract from chunk_id if it contains page info (e.g., "page_1_chunk_0")
        else if (hasPages && chunk.chunk_id) {
          const match = chunk.chunk_id.match(/page[_-]?(\d+)/i);
          if (match) {
            pageNumber = parseInt(match[1], 10);
          }
        }

        let title;

        // Determine if this is an audio document
        const isAudio = document?.metadata?.format_type === 'audio';

        if (hasTimestamp) {
          title = `Segment ${index + 1}`;
        } else if (pageNumber && !isAudio) {
          // Only use page numbers for visual documents (PDF, PPTX, etc.)
          // Audio transcripts shouldn't show "Page 1" - they should show "Chunk 1"
          title = `Page ${pageNumber}`;
        } else {
          title = `Chunk ${index + 1}`;
        }

        const section = {
          id: chunk.chunk_id,
          title,
          content: chunk.text_content || '',
          timestamp: hasTimestamp ? {
            start: chunk.start_time,
            end: chunk.end_time
          } : null,
          pageNumber: pageNumber
        };

        if (index === 0) {
          console.log(`[TextAccordion] First section:`, section);
        }

        newSections.push(section);
      });
    }

    console.log(`[TextAccordion] Total sections created: ${newSections.length}`);
    console.log(`[TextAccordion] Sections with page numbers: ${newSections.filter(s => s.pageNumber).length}`);
    setSections(newSections);
  }, [document, markdown, chunks, vttContent]);

  // Handle timestamp click (for audio seeking)
  const handleTimestampClick = (timestamp) => {
    console.log(`[TextAccordion] handleTimestampClick called with: ${timestamp}`);
    if (onTimestampClick) {
      onTimestampClick(timestamp);
    }
  };

  // Handle page click (for slideshow navigation)
  const handlePageClick = (pageNumber) => {
    console.log(`[TextAccordion] handlePageClick called with page: ${pageNumber}`);
    if (onPageClick) {
      onPageClick(pageNumber);
    } else {
      console.warn('[TextAccordion] onPageClick prop is not defined');
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
