/**
 * Accordion Component
 *
 * Displays document text content in expandable sections with markdown rendering.
 * Supports timestamps, copy to clipboard, and bidirectional sync with media players.
 * Ported from src/frontend/accordion.js
 *
 * Wave 2 - Details Agent
 */

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { useClipboard } from '../../hooks/useClipboard.js';

/**
 * Strip YAML frontmatter from markdown
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
 * Format time in MM:SS or HH:MM:SS
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
 * Individual accordion section
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
      onTimestampClick(timestamp.start);
    }

    // Handle page click (slideshow navigation)
    if (pageNumber && onPageClick) {
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
 * Accordion container with multiple sections
 *
 * @param {Object} props - Component props
 * @param {Array} props.sections - Array of section objects
 * @param {Function} [props.onTimestampClick] - Callback when timestamp is clicked (for audio seeking)
 * @param {Function} [props.onPageClick] - Callback when page link is clicked (for slideshow navigation)
 * @param {string} [props.activeSectionId] - Currently active section (for sync highlighting)
 */
export default function Accordion({
  sections = [],
  onTimestampClick,
  onPageClick,
  activeSectionId
}) {
  const [openSectionId, setOpenSectionId] = useState(null);
  const lastActiveSectionRef = useRef(null);

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
