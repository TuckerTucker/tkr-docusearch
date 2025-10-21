/**
 * FilterBar - Filtering and sorting UI
 *
 * Provides search input, sort dropdown, file type filters,
 * and pagination controls with event emission.
 *
 * Provider: filter-agent (Wave 1)
 * Contract: integration-contracts/filter-events.contract.md
 */

/**
 * Filter Bar Component
 * Emits filterChange and pageChange custom events
 */
export class FilterBar {
  /**
   * Create filter bar
   * @param {string} containerSelector - Container selector (e.g., '#filter-bar')
   */
  constructor(containerSelector) {
    this.container = document.querySelector(containerSelector);

    if (!this.container) {
      throw new Error(`Container not found: ${containerSelector}`);
    }

    // Filter state
    this.state = {
      search: '',
      sort_by: 'newest_first',
      file_type_group: 'all',
      limit: 50,
      offset: 0
    };

    // Debounce timer for search
    this.searchTimeout = null;
    this.searchDebounce = 300; // ms

    // Pagination state
    this.totalResults = 0;
    this.currentPage = 1;

    this.init();
  }

  /**
   * Initialize filter bar
   */
  init() {
    // Read URL params
    this.loadStateFromURL();

    // Render UI
    this.render();

    // Attach event listeners
    this.attachEventListeners();
  }

  /**
   * Load state from URL query params
   */
  loadStateFromURL() {
    const params = new URLSearchParams(window.location.search);

    if (params.has('search')) {
      this.state.search = params.get('search');
    }

    if (params.has('sort_by')) {
      this.state.sort_by = params.get('sort_by');
    }

    if (params.has('file_type_group')) {
      this.state.file_type_group = params.get('file_type_group');
    }

    if (params.has('offset')) {
      this.state.offset = parseInt(params.get('offset'), 10);
    }
  }

  /**
   * Render filter bar UI
   */
  render() {
    this.container.innerHTML = `
      <div class="filter-bar">
        <!-- Search temporarily hidden until semantic search is implemented -->
        <!-- <div class="filter-bar__search">
          <input
            type="search"
            id="search-input"
            class="filter-bar__search-input"
            placeholder="Search documents..."
            value="${this.state.search}"
            aria-label="Search documents"
          >
        </div> -->

        <div class="filter-bar__sort">
          <label for="sort-select" class="filter-bar__label">Sort by:</label>
          <select id="sort-select" class="filter-bar__select" aria-label="Sort documents by">
            <option value="newest_first" ${this.state.sort_by === 'newest_first' ? 'selected' : ''}>Newest First</option>
            <option value="oldest_first" ${this.state.sort_by === 'oldest_first' ? 'selected' : ''}>Oldest First</option>
            <option value="name_asc" ${this.state.sort_by === 'name_asc' ? 'selected' : ''}>Name A-Z</option>
            <option value="name_desc" ${this.state.sort_by === 'name_desc' ? 'selected' : ''}>Name Z-A</option>
          </select>
        </div>

        <div class="filter-bar__file-type">
          <label for="file-type-select" class="filter-bar__label">Filter by type:</label>
          <select id="file-type-select" class="filter-bar__select" aria-label="Filter documents by file type">
            <option value="all" ${this.state.file_type_group === 'all' ? 'selected' : ''}>All</option>
            <option value="pdf" ${this.state.file_type_group === 'pdf' ? 'selected' : ''}>PDF</option>
            <option value="audio" ${this.state.file_type_group === 'audio' ? 'selected' : ''}>Audio (MP3, WAV)</option>
            <option value="office" ${this.state.file_type_group === 'office' ? 'selected' : ''}>Office Documents (Word, Excel, PowerPoint)</option>
            <option value="text" ${this.state.file_type_group === 'text' ? 'selected' : ''}>Text Documents (Markdown, CSV, HTML, VTT)</option>
            <option value="images" ${this.state.file_type_group === 'images' ? 'selected' : ''}>Images (PNG, JPG, TIFF, BMP, WebP)</option>
          </select>
        </div>

        <button id="clear-filters" class="filter-bar__clear">Clear Filters</button>

        <div class="filter-bar__pagination" id="pagination-controls" style="display: none;">
          <button id="prev-page" class="filter-bar__page-btn" disabled>Previous</button>
          <span id="page-info" class="filter-bar__page-info">Page 1</span>
          <button id="next-page" class="filter-bar__page-btn">Next</button>
        </div>
      </div>
    `;
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Search input (debounced) - temporarily disabled
    const searchInput = this.container.querySelector('#search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
          this.state.search = e.target.value;
          this.state.offset = 0; // Reset to first page
          this.emitFilterChange();
        }, this.searchDebounce);
      });
    }

    // Sort select
    const sortSelect = this.container.querySelector('#sort-select');
    sortSelect.addEventListener('change', (e) => {
      this.state.sort_by = e.target.value;
      this.state.offset = 0; // Reset to first page
      this.emitFilterChange();
    });

    // File type group select
    const fileTypeSelect = this.container.querySelector('#file-type-select');
    fileTypeSelect.addEventListener('change', (e) => {
      this.state.file_type_group = e.target.value;
      this.state.offset = 0; // Reset to first page
      this.emitFilterChange();
    });

    // Clear filters button
    const clearBtn = this.container.querySelector('#clear-filters');
    clearBtn.addEventListener('click', () => {
      this.clearFilters();
    });

    // Pagination buttons
    const prevBtn = this.container.querySelector('#prev-page');
    const nextBtn = this.container.querySelector('#next-page');

    prevBtn.addEventListener('click', () => {
      if (this.state.offset > 0) {
        this.state.offset = Math.max(0, this.state.offset - this.state.limit);
        this.emitPageChange();
      }
    });

    nextBtn.addEventListener('click', () => {
      if (this.state.offset + this.state.limit < this.totalResults) {
        this.state.offset += this.state.limit;
        this.emitPageChange();
      }
    });
  }

  /**
   * Clear all filters
   */
  clearFilters() {
    this.state = {
      search: '',
      sort_by: 'newest_first',
      file_type_group: 'all',
      limit: 50,
      offset: 0
    };

    // Re-render to update UI
    this.render();
    this.attachEventListeners();

    // Emit change
    this.emitFilterChange();
  }

  /**
   * Emit filterChange event
   */
  emitFilterChange() {
    const event = new CustomEvent('filterChange', {
      detail: { ...this.state },
      bubbles: true
    });

    this.container.dispatchEvent(event);
    this.updateURL();
  }

  /**
   * Emit pageChange event
   */
  emitPageChange() {
    const event = new CustomEvent('pageChange', {
      detail: {
        offset: this.state.offset,
        limit: this.state.limit
      },
      bubbles: true
    });

    this.container.dispatchEvent(event);
    this.updateURL();
    this.updatePagination();
  }

  /**
   * Update URL query params
   */
  updateURL() {
    const params = new URLSearchParams();

    if (this.state.search) {
      params.set('search', this.state.search);
    }

    if (this.state.sort_by !== 'newest_first') {
      params.set('sort_by', this.state.sort_by);
    }

    if (this.state.file_type_group !== 'all') {
      params.set('file_type_group', this.state.file_type_group);
    }

    if (this.state.offset > 0) {
      params.set('offset', this.state.offset.toString());
    }

    const queryString = params.toString();
    const newURL = queryString ? `?${queryString}` : window.location.pathname;

    window.history.pushState(null, '', newURL);
  }

  /**
   * Update pagination display
   * @param {number} total - Total results
   */
  updatePaginationDisplay(total) {
    this.totalResults = total;
    this.currentPage = Math.floor(this.state.offset / this.state.limit) + 1;
    const totalPages = Math.ceil(total / this.state.limit);

    const paginationControls = this.container.querySelector('#pagination-controls');
    const prevBtn = this.container.querySelector('#prev-page');
    const nextBtn = this.container.querySelector('#next-page');
    const pageInfo = this.container.querySelector('#page-info');

    if (total > this.state.limit) {
      paginationControls.style.display = 'flex';
      pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;

      prevBtn.disabled = this.state.offset === 0;
      nextBtn.disabled = this.state.offset + this.state.limit >= total;
    } else {
      paginationControls.style.display = 'none';
    }
  }

  /**
   * Update pagination (internal)
   */
  updatePagination() {
    this.updatePaginationDisplay(this.totalResults);
  }
}
