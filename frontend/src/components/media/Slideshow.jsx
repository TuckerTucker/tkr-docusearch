/**
 * Slideshow Component
 *
 * Displays document pages with manual navigation and keyboard support.
 * Ported from src/frontend/slideshow.js
 *
 * Wave 2 - Details Agent
 */

import { useState, useEffect } from 'react';
import { useKeyboardNav } from '../../hooks/useKeyboardNav.js';

/**
 * Slideshow for PDF/DOCX/PPTX page images
 *
 * @param {Object} props - Component props
 * @param {Object} props.document - Document with pageImages array
 * @param {number} [props.initialPage=1] - Initial page number
 * @param {Function} [props.onPageChange] - Callback when page changes
 */
export default function Slideshow({ document, initialPage = 1, onPageChange }) {
  const pages = document?.pages || [];
  const totalPages = pages.length;

  const [currentPage, setCurrentPage] = useState(initialPage);
  const [pageInput, setPageInput] = useState(String(initialPage));

  // Update internal state when document changes
  useEffect(() => {
    setCurrentPage(initialPage);
    setPageInput(String(initialPage));
  }, [document?.doc_id, initialPage]);

  // Notify parent of page changes
  useEffect(() => {
    if (onPageChange) {
      onPageChange(currentPage);
    }
  }, [currentPage, onPageChange]);

  const goToPage = (pageNumber) => {
    // Type validation
    if (typeof pageNumber !== 'number' || isNaN(pageNumber)) {
      console.error(`[Slideshow] Invalid page number type: ${pageNumber}`);
      return;
    }

    // Range validation
    if (pageNumber < 1 || pageNumber > totalPages) {
      console.warn(`[Slideshow] Page ${pageNumber} out of range [1-${totalPages}]`);
      return;
    }

    setCurrentPage(pageNumber);
    setPageInput(String(pageNumber));
  };

  const previousPage = () => {
    if (currentPage > 1) {
      goToPage(currentPage - 1);
    }
  };

  const nextPage = () => {
    if (currentPage < totalPages) {
      goToPage(currentPage + 1);
    }
  };

  const handlePageInputChange = (e) => {
    setPageInput(e.target.value);
  };

  const handlePageInputSubmit = (e) => {
    e.preventDefault();
    const pageNumber = parseInt(pageInput, 10);

    if (isNaN(pageNumber)) {
      // Reset to current page if invalid
      setPageInput(String(currentPage));
      return;
    }

    goToPage(pageNumber);
  };

  // Keyboard navigation
  useKeyboardNav({
    onArrowLeft: previousPage,
    onArrowRight: nextPage,
    enabled: totalPages > 0,
  });

  // No pages available
  if (totalPages === 0) {
    return (
      <div className="slideshow-empty">
        <p>No pages available for this document.</p>
      </div>
    );
  }

  // Find current page data
  const currentPageData = pages.find(p => p.page_number === currentPage);
  const imageSrc = currentPageData?.image_path || currentPageData?.thumb_path;

  return (
    <div className="slideshow">
      <div className="slideshow-controls">
        <button
          className="slideshow-button"
          onClick={previousPage}
          disabled={currentPage === 1}
          aria-label="Previous page"
        >
          ← Previous
        </button>

        <form onSubmit={handlePageInputSubmit} className="slideshow-page-input">
          <label htmlFor="page-number" className="sr-only">
            Page number
          </label>
          <input
            id="page-number"
            type="number"
            min="1"
            max={totalPages}
            value={pageInput}
            onChange={handlePageInputChange}
            className="page-input"
            aria-label="Current page"
          />
          <span className="page-total" aria-label="Total pages">
            / {totalPages}
          </span>
        </form>

        <button
          className="slideshow-button"
          onClick={nextPage}
          disabled={currentPage === totalPages}
          aria-label="Next page"
        >
          Next →
        </button>
      </div>

      <div className="slideshow-image-container">
        {imageSrc ? (
          <img
            src={imageSrc}
            alt={`Page ${currentPage}`}
            className="slideshow-image"
          />
        ) : (
          <div className="slideshow-no-image">
            <p>No image available for page {currentPage}</p>
          </div>
        )}
      </div>

      <div className="slideshow-keyboard-hint" aria-live="polite">
        Use arrow keys (← →) to navigate
      </div>
    </div>
  );
}
