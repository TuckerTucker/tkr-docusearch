/**
 * FilterBar Component
 *
 * Filtering, sorting, and pagination controls for document library.
 * Features debounced search, file type filters, and pagination.
 *
 * Wave 2 - Library Agent
 */

import { useState, useEffect, useCallback } from 'react';
import { useDocumentStore } from '../../stores/useDocumentStore.js';

/**
 * FilterBar Component
 *
 * @param {Object} props - Component props
 * @param {number} [props.totalCount=0] - Total number of documents
 * @param {Function} [props.onFilterChange] - Filter change callback
 * @returns {JSX.Element} Filter bar
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
