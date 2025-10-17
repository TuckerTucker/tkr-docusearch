/**
 * Style Selector Component
 *
 * Manages the visual style theme selection dropdown.
 * Handles theme loading, persistence, and UI interactions.
 */

import { THEMES, DEFAULT_THEME, getThemeList, getTheme } from './theme-config.js';

const STORAGE_KEY = 'docusearch-visual-style';
const THEME_LINK_ID = 'visual-style-theme';

/**
 * StyleSelector class - manages visual style theme switching
 */
export class StyleSelector {
  constructor() {
    this.currentThemeId = null;
    this.button = null;
    this.dropdown = null;
    this.list = null;
    this.isOpen = false;
  }

  /**
   * Initialize the style selector
   */
  init() {
    this.button = document.getElementById('style-selector-button');
    this.dropdown = document.getElementById('style-selector-dropdown');
    this.list = this.dropdown?.querySelector('.style-selector__list');

    if (!this.button || !this.dropdown || !this.list) {
      console.error('StyleSelector: Required DOM elements not found');
      return;
    }

    // Load saved theme or default
    this.currentThemeId = this.loadSavedTheme();

    // Render theme options
    this.renderOptions();

    // Apply the current theme
    this.loadTheme(this.currentThemeId);

    // Setup event listeners
    this.setupEventListeners();

    console.log(`StyleSelector initialized with theme: ${this.currentThemeId}`);
  }

  /**
   * Load saved theme from localStorage
   * @returns {string} Theme ID
   */
  loadSavedTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && THEMES[saved]) {
        return saved;
      }
    } catch (error) {
      console.warn('StyleSelector: Failed to load saved theme', error);
    }
    return DEFAULT_THEME;
  }

  /**
   * Save theme to localStorage
   * @param {string} themeId - Theme ID to save
   */
  saveTheme(themeId) {
    try {
      localStorage.setItem(STORAGE_KEY, themeId);
    } catch (error) {
      console.warn('StyleSelector: Failed to save theme', error);
    }
  }

  /**
   * Load a theme by dynamically swapping the CSS file
   * @param {string} themeId - Theme ID to load
   */
  loadTheme(themeId) {
    const theme = getTheme(themeId);
    if (!theme) {
      console.error(`StyleSelector: Theme not found: ${themeId}`);
      return;
    }

    // Remove existing theme link if present
    const existingLink = document.getElementById(THEME_LINK_ID);
    if (existingLink) {
      existingLink.remove();
    }

    // Create new link element for theme CSS
    const link = document.createElement('link');
    link.id = THEME_LINK_ID;
    link.rel = 'stylesheet';
    link.href = theme.file;

    // Insert after the main styles.css
    const mainStyles = document.querySelector('link[href="styles.css"]');
    if (mainStyles && mainStyles.nextSibling) {
      mainStyles.parentNode.insertBefore(link, mainStyles.nextSibling);
    } else {
      document.head.appendChild(link);
    }

    this.currentThemeId = themeId;
    this.saveTheme(themeId);
    this.updateActiveState();

    console.log(`StyleSelector: Loaded theme: ${theme.name}`);
  }

  /**
   * Render theme options in the dropdown
   */
  renderOptions() {
    const themes = getThemeList();

    this.list.innerHTML = themes.map(theme => `
      <li class="style-selector__item">
        <button
          class="style-selector__option ${theme.id === this.currentThemeId ? 'style-selector__option--active' : ''}"
          role="menuitem"
          data-theme-id="${theme.id}">
          <div class="style-selector__option-content">
            <div class="style-selector__option-name">${theme.name}</div>
            <div class="style-selector__option-description">${theme.description}</div>
          </div>
          <svg class="style-selector__checkmark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </button>
      </li>
    `).join('');

    // Add click handlers to options
    this.list.querySelectorAll('.style-selector__option').forEach(option => {
      option.addEventListener('click', (e) => {
        const themeId = e.currentTarget.dataset.themeId;
        this.loadTheme(themeId);
        this.closeDropdown();
      });
    });
  }

  /**
   * Update the active state of theme options
   */
  updateActiveState() {
    this.list.querySelectorAll('.style-selector__option').forEach(option => {
      const themeId = option.dataset.themeId;
      if (themeId === this.currentThemeId) {
        option.classList.add('style-selector__option--active');
      } else {
        option.classList.remove('style-selector__option--active');
      }
    });
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Toggle dropdown on button click
    this.button.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleDropdown();
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (this.isOpen && !this.dropdown.contains(e.target) && !this.button.contains(e.target)) {
        this.closeDropdown();
      }
    });

    // Keyboard navigation
    this.button.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.closeDropdown();
        this.button.focus();
      }
    });

    // Dropdown keyboard navigation
    this.dropdown.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeDropdown();
        this.button.focus();
      }
    });
  }

  /**
   * Toggle dropdown open/closed
   */
  toggleDropdown() {
    if (this.isOpen) {
      this.closeDropdown();
    } else {
      this.openDropdown();
    }
  }

  /**
   * Open the dropdown
   */
  openDropdown() {
    this.dropdown.classList.add('style-selector__dropdown--open');
    this.button.setAttribute('aria-expanded', 'true');
    this.isOpen = true;

    // Focus first option
    const firstOption = this.list.querySelector('.style-selector__option');
    if (firstOption) {
      firstOption.focus();
    }
  }

  /**
   * Close the dropdown
   */
  closeDropdown() {
    this.dropdown.classList.remove('style-selector__dropdown--open');
    this.button.setAttribute('aria-expanded', 'false');
    this.isOpen = false;
  }
}

/**
 * Initialize the style selector when DOM is ready
 */
export function initStyleSelector() {
  const selector = new StyleSelector();
  selector.init();
  return selector;
}
