/**
 * @fileoverview Accordion component for displaying document content in expandable sections
 * with markdown rendering, timestamps, and bidirectional media sync.
 *
 * Ported from src/frontend/accordion.js
 * Wave 2 - Details Agent
 */

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { useClipboard } from '../../hooks/useClipboard.js';

/**
 * Strip YAML frontmatter from markdown content
 *
 * @param {string} markdown - The markdown content potentially containing frontmatter
 * @returns {string} The markdown content with frontmatter removed
 *
 * @example
 * const markdown = `---
 * title: My Document
 * date: 2025-10-26
 * ---
 * # Content here`;
 *
 * const stripped = stripFrontmatter(markdown);
 * // Returns: "# Content here"
 */
function stripFrontmatter(markdown) {
  if (!markdown) return '';

  const lines = markdown.split('\n');

  // Check if starts with frontmatter delimiter
  if (lines[0] === '---') {
    // Find ending delimiter
    const endIndex = lines.findIndex((line, index) => index > 0 && line === '---');

    if (endIndex !== -1) {
      // Return everything after the frontmatter
      return lines.slice(endIndex + 1).join('\n').trim();
    }
  }

  return markdown;
}

/**
 * Format time duration in MM:SS or HH:MM:SS format
 *
 * @param {number|null|undefined} seconds - Time duration in seconds
 * @returns {string} Formatted time string (MM:SS or HH:MM:SS) or empty string if invalid
 *
 * @example
 * formatTime(65);     // Returns: "1:05"
 * formatTime(3665);   // Returns: "1:01:05"
 * formatTime(null);   // Returns: ""
 */
function formatTime(seconds) {
  if (seconds === null || seconds === undefined) return '';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

/**
 * Individual accordion section component
 *
 * Renders a single expandable section with header, content, and actions.
 * Supports markdown rendering, timestamp navigation, and copy-to-clipboard functionality.
 *
 * @component
 * @param {Object} props - Component props
 * @param {string} props.id - Unique identifier for the section
 * @param {string} props.title - Display title for the section header
 * @param {string} props.content - Markdown content to display when expanded
 * @param {boolean} props.isOpen - Whether the section is currently expanded
 * @param {boolean} props.isActive - Whether the section is currently active (for sync highlighting)
 * @param {Function} props.onToggle - Callback when section is toggled open/closed
 * @param {Function} [props.onCopy] - Optional callback after content is copied
 * @param {Function} [props.onTimestampClick] - Optional callback when timestamp is clicked (for audio seeking)
 * @param {Function} [props.onPageClick] - Optional callback when page link is clicked (for slideshow navigation)
 * @param {Object} [props.timestamp] - Optional timestamp object with start and end times
 * @param {number} [props.timestamp.start] - Start time in seconds
 * @param {number} [props.timestamp.end] - End time in seconds
 * @param {number} [props.pageNumber] - Optional page number for document navigation
 * @returns {React.ReactElement} The rendered accordion section
 */
function AccordionSection({
  id,
  title,
  content,
  isOpen,
  isActive,
  onToggle,
  onCopy,
  onTimestampClick,
  onPageClick,
  timestamp,
  pageNumber
}) {
  const { copy, isCopied } = useClipboard();

  const handleCopy = async (e) => {
    e.stopPropagation();
    await copy(content);
    if (onCopy) {
      onCopy();
    }
  };

  const handleHeaderClick = () => {
    onToggle();

    // Handle timestamp click (audio navigation)
    if (timestamp && onTimestampClick) {
      console.log(`[Accordion] Timestamp click: ${timestamp.start}s`);
      onTimestampClick(timestamp.start);
    }

    // Handle page click (slideshow navigation)
    if (pageNumber && onPageClick) {
      console.log(`[Accordion] Page click: page ${pageNumber}`);
      onPageClick(pageNumber);
    }
  };

  return (
    <div className={`accordion-section ${isActive ? 'active' : ''}`} data-section-id={id}>
      <div
        className={`accordion-header ${isOpen ? 'open' : ''}`}
        onClick={handleHeaderClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleHeaderClick();
          }
        }}
      >
        <div className="accordion-title">
          {title}
          {timestamp && (
            <span className="accordion-timestamp">
              ({formatTime(timestamp.start)} - {formatTime(timestamp.end)})
            </span>
          )}
        </div>
        <div className="accordion-actions">
          <span className="accordion-toggle">{isOpen ? '▼' : '▶'}</span>
        </div>
      </div>

      {isOpen && (
        <div className="accordion-content open">
          <div className="accordion-body">
            <div className="accordion-body-actions">
              <button
                className={`btn-icon ${isCopied ? 'success' : ''}`}
                onClick={handleCopy}
                aria-label="Copy to clipboard"
              >
                {isCopied ? '✓ Copied!' : '📋 Copy'}
              </button>
            </div>
            <div className="accordion-body-text">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Section data structure for Accordion component
 * @typedef {Object} AccordionSectionData
 * @property {string} id - Unique identifier for the section
 * @property {string} title - Display title for the section header
 * @property {string} content - Markdown content to display when expanded
 * @property {Object} [timestamp] - Optional timestamp for audio/video content
 * @property {number} timestamp.start - Start time in seconds
 * @property {number} timestamp.end - End time in seconds
 * @property {number} [pageNumber] - Optional page number for document navigation
 */

/**
 * Accordion Component
 *
 * A container component that displays multiple expandable sections with rich content.
 * Designed for displaying document text content, transcripts, and other structured
 * information with support for media synchronization and navigation.
 *
 * Features:
 * - Expandable/collapsible sections with smooth animations
 * - Markdown rendering with ReactMarkdown
 * - Copy-to-clipboard functionality for each section
 * - Timestamp support for audio/video synchronization
 * - Page number support for document/slideshow navigation
 * - Bidirectional sync: auto-open sections when media playback reaches them
 * - Active section highlighting for visual feedback
 * - Keyboard navigation support (Enter/Space to toggle)
 * - Automatic scroll-to-view for active sections
 *
 * @component
 * @param {Object} props - Component props
 * @param {AccordionSectionData[]} [props.sections=[]] - Array of section objects to display
 * @param {Function} [props.onTimestampClick] - Callback when timestamp is clicked (for audio/video seeking)
 * @param {Function} [props.onPageClick] - Callback when page number is clicked (for slideshow navigation)
 * @param {string} [props.activeSectionId] - Currently active section ID (for sync highlighting)
 * @returns {React.ReactElement} The rendered Accordion component
 *
 * @example
 * // Basic usage with document sections
 * import Accordion from './components/ui/Accordion';
 *
 * function DocumentViewer({ document }) {
 *   const sections = [
 *     {
 *       id: 'intro',
 *       title: 'Introduction',
 *       content: '# Welcome\n\nThis is the introduction...'
 *     },
 *     {
 *       id: 'chapter1',
 *       title: 'Chapter 1',
 *       content: '## Getting Started\n\nLet\'s begin with...'
 *     }
 *   ];
 *
 *   return <Accordion sections={sections} />;
 * }
 *
 * @example
 * // Advanced usage with audio transcript and bidirectional sync
 * import { useState } from 'react';
 * import Accordion from './components/ui/Accordion';
 * import AudioPlayer from './components/AudioPlayer';
 *
 * function TranscriptView({ audioUrl, transcript }) {
 *   const [activeSectionId, setActiveSectionId] = useState(null);
 *
 *   const sections = transcript.segments.map((segment, idx) => ({
 *     id: `segment-${idx}`,
 *     title: `Segment ${idx + 1}`,
 *     content: segment.text,
 *     timestamp: {
 *       start: segment.start_time,
 *       end: segment.end_time
 *     }
 *   }));
 *
 *   const handleTimestampClick = (seconds) => {
 *     // Seek audio player to timestamp
 *     audioPlayerRef.current.seekTo(seconds);
 *   };
 *
 *   const handleAudioTimeUpdate = (currentTime) => {
 *     // Find and activate section matching current playback time
 *     const activeSection = sections.find(
 *       s => s.timestamp.start <= currentTime && currentTime <= s.timestamp.end
 *     );
 *     if (activeSection) {
 *       setActiveSectionId(activeSection.id);
 *     }
 *   };
 *
 *   return (
 *     <div>
 *       <AudioPlayer
 *         src={audioUrl}
 *         onTimeUpdate={handleAudioTimeUpdate}
 *         ref={audioPlayerRef}
 *       />
 *       <Accordion
 *         sections={sections}
 *         activeSectionId={activeSectionId}
 *         onTimestampClick={handleTimestampClick}
 *       />
 *     </div>
 *   );
 * }
 *
 * @example
 * // Usage with slideshow/presentation navigation
 * import Accordion from './components/ui/Accordion';
 *
 * function PresentationNotes({ slides }) {
 *   const [currentSlide, setCurrentSlide] = useState(0);
 *
 *   const sections = slides.map((slide, idx) => ({
 *     id: `slide-${idx}`,
 *     title: slide.title,
 *     content: slide.notes,
 *     pageNumber: idx + 1
 *   }));
 *
 *   const handlePageClick = (pageNumber) => {
 *     // Navigate slideshow to specific page
 *     setCurrentSlide(pageNumber - 1);
 *   };
 *
 *   return (
 *     <Accordion
 *       sections={sections}
 *       activeSectionId={`slide-${currentSlide}`}
 *       onPageClick={handlePageClick}
 *     />
 *   );
 * }
 */
export default function Accordion({
  sections = [],
  onTimestampClick,
  onPageClick,
  activeSectionId
}) {
  const [openSectionId, setOpenSectionId] = useState(null);
  const lastActiveSectionRef = useRef(null);

  // Log sections on mount/update
  useEffect(() => {
    console.log(`[Accordion] Received ${sections.length} sections`);
    console.log(`[Accordion] Sections with page numbers:`, sections.filter(s => s.pageNumber).map(s => ({ id: s.id, title: s.title, pageNumber: s.pageNumber })));
    console.log(`[Accordion] onPageClick callback:`, onPageClick ? 'defined' : 'UNDEFINED');
  }, [sections, onPageClick]);

  const handleToggle = (sectionId) => {
    // User manually toggled - allow full toggle behavior
    setOpenSectionId(openSectionId === sectionId ? null : sectionId);
  };

  // Auto-open section when it becomes active (for audio/slideshow sync)
  // This mimics the original openSection() method which is separate from toggleSection()
  useEffect(() => {
    if (!activeSectionId) return;

    // Only auto-open if this is a NEW active section
    // Prevents repeated opens of the same section
    if (activeSectionId !== lastActiveSectionRef.current) {
      console.log(`[Accordion] Auto-opening section: ${activeSectionId}`);
      setOpenSectionId(activeSectionId);
      lastActiveSectionRef.current = activeSectionId;

      // Scroll section into view
      setTimeout(() => {
        const sectionElement = document.querySelector(`[data-section-id="${activeSectionId}"]`);
        if (sectionElement) {
          sectionElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 100);
    }
  }, [activeSectionId]);

  if (sections.length === 0) {
    return (
      <div className="accordion-empty">
        <p>No content available.</p>
      </div>
    );
  }

  return (
    <div className="accordion">
      {sections.map((section) => (
        <AccordionSection
          key={section.id}
          id={section.id}
          title={section.title}
          content={section.content}
          isOpen={openSectionId === section.id}
          isActive={activeSectionId === section.id}
          onToggle={() => handleToggle(section.id)}
          onTimestampClick={onTimestampClick}
          onPageClick={onPageClick}
          timestamp={section.timestamp}
          pageNumber={section.pageNumber}
        />
      ))}
    </div>
  );
}
