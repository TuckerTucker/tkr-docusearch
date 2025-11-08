/**
 * Application Configuration Constants
 *
 * Centralized configuration for API endpoints, timeouts, and application settings.
 *
 * Wave 1 - Foundation Agent
 */

/**
 * API base URL
 * Override with VITE_API_URL environment variable
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * WebSocket URL for real-time updates
 * Override with VITE_WS_URL environment variable
 *
 * Uses relative protocol and hostname to work through Vite proxy in dev
 * and direct connection in production.
 */
export const WS_URL = import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

/**
 * Copyparty file server URL
 * Uses centralized configuration from @/config/urls
 * Override with VITE_COPYPARTY_URL environment variable
 *
 * @deprecated - Use serviceURLs from '@/config/urls' instead
 */
export const COPYPARTY_URL = import.meta.env.VITE_COPYPARTY_URL || 'http://localhost:8000';

/**
 * Default page size for pagination
 */
export const DEFAULT_PAGE_SIZE = 50;

/**
 * Search debounce delay in milliseconds
 */
export const SEARCH_DEBOUNCE_MS = 300;

/**
 * Maximum number of WebSocket reconnection attempts
 */
export const RECONNECT_MAX_ATTEMPTS = 10;

/**
 * API request timeout in milliseconds
 */
export const REQUEST_TIMEOUT_MS = 30000;

/**
 * Supported file types for upload
 */
export const SUPPORTED_FILE_TYPES = {
    document: ['.pdf', '.docx', '.pptx'],
    audio: ['.mp3', '.wav'],
};

/**
 * File type categories for filtering
 */
export const FILE_TYPE_CATEGORIES = {
    all: 'All Types',
    document: 'Documents',
    audio: 'Audio',
};

/**
 * Sort options for document library
 */
export const SORT_OPTIONS = {
    date_desc: { label: 'Newest First', field: 'upload_date', order: 'desc' },
    date_asc: { label: 'Oldest First', field: 'upload_date', order: 'asc' },
    name_asc: { label: 'Name A-Z', field: 'filename', order: 'asc' },
    name_desc: { label: 'Name Z-A', field: 'filename', order: 'desc' },
};

/**
 * Default sort option
 */
export const DEFAULT_SORT = 'date_desc';

/**
 * Processing status types
 */
export const PROCESSING_STATUS = {
    PENDING: 'pending',
    PROCESSING: 'processing',
    COMPLETE: 'complete',
    FAILED: 'failed',
};

/**
 * Theme options
 */
export const THEMES = {
    LIGHT: 'light',
    DARK: 'dark',
};

/**
 * Local storage keys
 */
export const STORAGE_KEYS = {
    THEME: 'docusearch-theme',
    LAST_SEARCH: 'docusearch-last-search',
    SORT_PREFERENCE: 'docusearch-sort-preference',
};
