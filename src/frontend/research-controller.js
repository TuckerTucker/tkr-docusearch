/**
 * Research Controller
 *
 * Main controller for research page - handles API integration,
 * state management, and coordinates answer/reference components.
 */

import { renderAnswer } from './answer-display.js';
import { renderReferenceCards } from './reference-card.js';

// State
let currentView = 'detailed';
let currentResponse = null;

// API endpoint
const API_BASE = window.location.origin.includes('localhost:8000')
    ? 'http://localhost:8003'  // Standalone research API
    : window.location.origin;  // Integrated API

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initializeResearchPage();
});

/**
 * Initialize research page
 */
function initializeResearchPage() {
    console.log('Initializing research page');

    // Attach event listeners
    const form = document.getElementById('research-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    const detailedBtn = document.getElementById('detailed-view-btn');
    const simpleBtn = document.getElementById('simple-view-btn');

    if (detailedBtn) {
        detailedBtn.addEventListener('click', () => switchView('detailed'));
    }
    if (simpleBtn) {
        simpleBtn.addEventListener('click', () => switchView('simple'));
    }

    const retryBtn = document.getElementById('retry-button');
    if (retryBtn) {
        retryBtn.addEventListener('click', handleRetry);
    }

    // Initialize theme toggle (reuse from existing code)
    initializeThemeToggle();

    console.log('Research page initialized');
}

/**
 * Initialize theme toggle
 */
function initializeThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.classList.toggle('dark-theme', savedTheme === 'dark');

    themeToggle.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

/**
 * Handle form submission
 * @param {Event} event - Submit event
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const queryInput = document.getElementById('query-input');
    const query = queryInput.value.trim();

    if (!query) {
        showError('Please enter a question.');
        return;
    }

    console.log('Submitting query:', query);

    // Show loading state
    showLoadingState();

    try {
        const response = await submitResearchQuery(query);
        currentResponse = response;

        console.log('Received response:', response);

        // Render answer and references
        renderResearchResults(response);

        // Show success state
        showSuccessState();

    } catch (error) {
        console.error('Research query failed:', error);
        showErrorState(error.message);
    }
}

/**
 * Submit research query to API
 * @param {string} query - User's question
 * @returns {Promise<Object>} API response
 */
async function submitResearchQuery(query) {
    const endpoint = `${API_BASE}/api/research/ask`;

    console.log('Calling API:', endpoint);

    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            num_sources: 10,
            search_mode: 'hybrid'
        })
    });

    if (!response.ok) {
        let errorMessage = 'Failed to get research answer';
        try {
            const error = await response.json();
            errorMessage = error.detail || error.error || errorMessage;
        } catch (e) {
            errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
    }

    return await response.json();
}

/**
 * Render research results
 * @param {Object} response - API response
 */
function renderResearchResults(response) {
    // Render answer
    const answerDisplay = document.getElementById('answer-display');
    if (answerDisplay) {
        renderAnswer(response, answerDisplay);
    }

    // Render references
    const referencesList = document.getElementById('references-list');
    if (referencesList) {
        renderReferenceCards(response.sources, referencesList, currentView);
    }

    // Show metadata (optional)
    console.log('Research completed:', {
        sources: response.sources.length,
        processing_time: response.metadata.processing_time_ms + 'ms',
        model: response.metadata.model_used
    });
}

/**
 * Switch view mode (detailed/simple)
 * @param {string} view - 'detailed' or 'simple'
 */
function switchView(view) {
    currentView = view;

    // Update button states
    document.querySelectorAll('.view-toggle').forEach(btn => {
        const isActive = btn.dataset.view === view;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-pressed', isActive);
    });

    // Re-render references if we have results
    if (currentResponse) {
        const referencesList = document.getElementById('references-list');
        if (referencesList) {
            renderReferenceCards(currentResponse.sources, referencesList, view);
        }
    }
}

/**
 * Show loading state
 */
function showLoadingState() {
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    const answerDisplay = document.getElementById('answer-display');
    const errorState = document.getElementById('error-state');
    const referencesEmpty = document.getElementById('references-empty');
    const referencesList = document.getElementById('references-list');

    if (emptyState) emptyState.classList.add('hidden');
    if (loadingState) loadingState.classList.remove('hidden');
    if (answerDisplay) answerDisplay.classList.add('hidden');
    if (errorState) errorState.classList.add('hidden');

    if (referencesEmpty) referencesEmpty.classList.add('hidden');
    if (referencesList) referencesList.classList.add('hidden');

    // Disable form
    const queryInput = document.getElementById('query-input');
    const askButton = document.querySelector('.ask-button');
    if (queryInput) queryInput.disabled = true;
    if (askButton) askButton.disabled = true;
}

/**
 * Show success state
 */
function showSuccessState() {
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    const answerDisplay = document.getElementById('answer-display');
    const errorState = document.getElementById('error-state');
    const referencesEmpty = document.getElementById('references-empty');
    const referencesList = document.getElementById('references-list');

    if (emptyState) emptyState.classList.add('hidden');
    if (loadingState) loadingState.classList.add('hidden');
    if (answerDisplay) answerDisplay.classList.remove('hidden');
    if (errorState) errorState.classList.add('hidden');

    if (referencesEmpty) referencesEmpty.classList.add('hidden');
    if (referencesList) referencesList.classList.remove('hidden');

    // Enable form
    const queryInput = document.getElementById('query-input');
    const askButton = document.querySelector('.ask-button');
    if (queryInput) queryInput.disabled = false;
    if (askButton) askButton.disabled = false;
}

/**
 * Show error state
 * @param {string} message - Error message
 */
function showErrorState(message) {
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    const answerDisplay = document.getElementById('answer-display');
    const errorState = document.getElementById('error-state');
    const errorMessage = document.getElementById('error-message');

    if (emptyState) emptyState.classList.add('hidden');
    if (loadingState) loadingState.classList.add('hidden');
    if (answerDisplay) answerDisplay.classList.add('hidden');
    if (errorState) errorState.classList.remove('hidden');

    if (errorMessage) {
        errorMessage.textContent = message || 'An error occurred. Please try again.';
    }

    // Enable form
    const queryInput = document.getElementById('query-input');
    const askButton = document.querySelector('.ask-button');
    if (queryInput) queryInput.disabled = false;
    if (askButton) askButton.disabled = false;
}

/**
 * Show simple error without changing state
 * @param {string} message - Error message
 */
function showError(message) {
    alert(message);
}

/**
 * Handle retry button click
 */
function handleRetry() {
    const form = document.getElementById('research-form');
    if (form) {
        form.dispatchEvent(new Event('submit'));
    }
}

// Export for debugging
window.researchDebug = {
    currentView,
    currentResponse,
    submitQuery: submitResearchQuery,
    switchView
};

console.log('Research controller loaded');
