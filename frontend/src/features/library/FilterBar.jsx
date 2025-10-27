/**
 * FilterBar Component
 *
 * Filtering, sorting, and pagination controls for document library.
 * Features debounced search, file type filters, and pagination.
 *
 * Wave 2 - Library Agent
 */

import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useDocumentStore } from '../../stores/useDocumentStore.js';

/**
 * FilterBar Component
 *
 * Comprehensive filter bar with sorting, file type filtering, pagination, and upload controls.
 * Integrates with Zustand document store for filter state management.
 *
 * Features:
 * - Debounced search input (300ms delay, currently hidden)
 * - Sort by: newest/oldest first, name A-Z/Z-A
 * - File type filter: all, PDF, audio, office docs, text, images
 * - Pagination with previous/next controls
 * - Upload button (triggers manualUpload event)
 * - Research page navigation
 * - Clear filters button
 *
 * @param {Object} props - Component props
 * @param {number} [props.totalCount=0] - Total number of documents for pagination
 * @param {Function} [props.onFilterChange] - Callback when filters change
 * @param {Object} props.onFilterChange.filters - Updated filter object
 * @param {string} props.onFilterChange.filters.search - Search query
 * @param {string} props.onFilterChange.filters.sortBy - Sort option (newest_first | oldest_first | name_asc | name_desc)
 * @param {string} props.onFilterChange.filters.fileTypeGroup - File type filter (all | pdf | audio | office | text | images)
 * @param {number} props.onFilterChange.filters.limit - Items per page
 * @param {number} props.onFilterChange.filters.offset - Pagination offset
 * @returns {JSX.Element} Filter bar component
 * @example
 * // Basic usage with filter change callback
 * import FilterBar from './features/library/FilterBar';
 * import { useState } from 'react';
 *
 * function LibraryPage() {
 *   const [documents, setDocuments] = useState([]);
 *   const [totalCount, setTotalCount] = useState(0);
 *
 *   const handleFilterChange = async (filters) => {
 *     // Fetch documents with new filters
 *     const response = await fetchDocuments(filters);
 *     setDocuments(response.documents);
 *     setTotalCount(response.total);
 *   };
 *
 *   return (
 *     <div>
 *       <FilterBar
 *         totalCount={totalCount}
 *         onFilterChange={handleFilterChange}
 *       />
 *       <DocumentGrid documents={documents} />
 *     </div>
 *   );
 * }
 *
 * @example
 * // Using with Zustand store (filters automatically synced)
 * import FilterBar from './features/library/FilterBar';
 * import { useDocumentStore } from './stores/useDocumentStore';
 *
 * function LibraryPage() {
 *   const documents = useDocumentStore((state) => state.documents);
 *   const totalCount = useDocumentStore((state) => state.totalCount);
 *   const filters = useDocumentStore((state) => state.filters);
 *
 *   const handleFilterChange = async (newFilters) => {
 *     // Filters are already updated in store via FilterBar
 *     // Just fetch new data
 *     await fetchDocuments(newFilters);
 *   };
 *
 *   return (
 *     <FilterBar
 *       totalCount={totalCount}
 *       onFilterChange={handleFilterChange}
 *     />
 *   );
 * }
 */
export default function FilterBar({ totalCount = 0, onFilterChange }) {
  const filters = useDocumentStore((state) => state.filters);
  const setSearch = useDocumentStore((state) => state.setSearch);
  const setSortBy = useDocumentStore((state) => state.setSortBy);
  const setFileTypeGroup = useDocumentStore((state) => state.setFileTypeGroup);
  const setPage = useDocumentStore((state) => state.setPage);
  const resetFilters = useDocumentStore((state) => state.resetFilters);

  // Local search state for immediate UI updates (debounced)
  const [searchValue, setSearchValue] = useState(filters.search);
  const [searchTimeout, setSearchTimeout] = useState(null);

  // Handle file selection from upload button
  const handleUploadFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // Dispatch custom event for UploadModal to handle
      const event = new CustomEvent('manualUpload', { detail: { files: Array.from(files) } });
      window.dispatchEvent(event);

      // Reset input to allow uploading same files again
      e.target.value = '';
    }
  };

  // Sync local search with store
  useEffect(() => {
    setSearchValue(filters.search);
  }, [filters.search]);

  // Debounced search handler
  const handleSearchChange = useCallback(
    (value) => {
      setSearchValue(value);

      // Clear existing timeout
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }

      // Set new timeout (300ms debounce)
      const timeout = setTimeout(() => {
        setSearch(value);
        if (onFilterChange) {
          onFilterChange({ ...filters, search: value, offset: 0 });
        }
      }, 300);

      setSearchTimeout(timeout);
    },
    [setSearch, searchTimeout, onFilterChange, filters]
  );

  // Sort change handler
  const handleSortChange = (e) => {
    const sortBy = e.target.value;
    setSortBy(sortBy);
    if (onFilterChange) {
      onFilterChange({ ...filters, sortBy, offset: 0 });
    }
  };

  // File type filter change handler
  const handleFileTypeChange = (e) => {
    const fileTypeGroup = e.target.value;
    setFileTypeGroup(fileTypeGroup);
    if (onFilterChange) {
      onFilterChange({ ...filters, fileTypeGroup, offset: 0 });
    }
  };

  // Clear filters handler
  const handleClearFilters = () => {
    setSearchValue('');
    resetFilters();
    if (onFilterChange) {
      onFilterChange({
        search: '',
        sortBy: 'newest_first',
        fileTypeGroup: 'all',
        limit: 50,
        offset: 0,
      });
    }
  };

  // Pagination
  const currentPage = Math.floor(filters.offset / filters.limit) + 1;
  const totalPages = Math.ceil(totalCount / filters.limit);
  const showPagination = totalCount > filters.limit;

  const handlePreviousPage = () => {
    if (filters.offset > 0) {
      const newPage = currentPage - 1;
      setPage(newPage);
      if (onFilterChange) {
        onFilterChange({ ...filters, offset: (newPage - 1) * filters.limit });
      }
    }
  };

  const handleNextPage = () => {
    if (filters.offset + filters.limit < totalCount) {
      const newPage = currentPage + 1;
      setPage(newPage);
      if (onFilterChange) {
        onFilterChange({ ...filters, offset: (newPage - 1) * filters.limit });
      }
    }
  };

  return (
    <div className="filter-bar">
      {/* Search input - temporarily hidden per contract */}
      {/*
      <div className="filter-bar__search">
        <input
          type="search"
          id="search-input"
          className="filter-bar__search-input"
          placeholder="Search documents..."
          value={searchValue}
          onChange={(e) => handleSearchChange(e.target.value)}
          aria-label="Search documents"
        />
      </div>
      */}

      {/* Sort dropdown */}
      <div className="filter-bar__sort">
        <label htmlFor="sort-select" className="filter-bar__label">
          Sort by:
        </label>
        <select
          id="sort-select"
          className="filter-bar__select"
          value={filters.sortBy}
          onChange={handleSortChange}
          aria-label="Sort documents by"
        >
          <option value="newest_first">Newest First</option>
          <option value="oldest_first">Oldest First</option>
          <option value="name_asc">Name A-Z</option>
          <option value="name_desc">Name Z-A</option>
        </select>
      </div>

      {/* File type filter */}
      <div className="filter-bar__file-type">
        <label htmlFor="file-type-select" className="filter-bar__label">
          Filter by type:
        </label>
        <select
          id="file-type-select"
          className="filter-bar__select"
          value={filters.fileTypeGroup}
          onChange={handleFileTypeChange}
          aria-label="Filter documents by file type"
        >
          <option value="all">All</option>
          <option value="pdf">PDF</option>
          <option value="audio">Audio (MP3, WAV)</option>
          <option value="office">Office Documents (Word, Excel, PowerPoint)</option>
          <option value="text">Text Documents (Markdown, CSV, HTML, VTT)</option>
          <option value="images">Images (PNG, JPG, TIFF, BMP, WebP)</option>
        </select>
      </div>

      {/* Clear filters button */}
      <button
        id="clear-filters"
        className="filter-bar__clear"
        onClick={handleClearFilters}
      >
        Clear Filters
      </button>

      {/* Upload button */}
      {/* File upload - use label to trigger input for accessibility (WCAG 3.3.2) */}
      <label htmlFor="filter-bar-upload-input" className="filter-bar__upload">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        Upload
      </label>

      {/* Visually hidden file input - screen readers can access it */}
      <input
        id="filter-bar-upload-input"
        type="file"
        multiple
        accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.html,.xhtml,.md,.asciidoc,.csv,.mp3,.wav,.vtt,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
        className="sr-only"
        onChange={handleUploadFileChange}
      />

      {/* Research button - aligned right */}
      <Link
        to="/research"
        className="filter-bar__research"
        aria-label="Go to research page"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        Research
      </Link>

      {/* Pagination */}
      {showPagination && (
        <div className="filter-bar__pagination" id="pagination-controls">
          <button
            id="prev-page"
            className="filter-bar__page-btn"
            onClick={handlePreviousPage}
            disabled={filters.offset === 0}
            aria-label="Previous page"
          >
            Previous
          </button>
          <span id="page-info" className="filter-bar__page-info">
            Page {currentPage} of {totalPages}
          </span>
          <button
            id="next-page"
            className="filter-bar__page-btn"
            onClick={handleNextPage}
            disabled={filters.offset + filters.limit >= totalCount}
            aria-label="Next page"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
