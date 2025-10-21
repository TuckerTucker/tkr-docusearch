/**
 * Theme Toggle Module
 *
 * Handles light/dark theme switching with:
 * - System preference detection (prefers-color-scheme)
 * - localStorage persistence
 * - Manual toggle functionality
 *
 * Theme Strategy:
 * 1. Check localStorage for saved preference
 * 2. If no saved preference, use system preference
 * 3. Apply theme by adding/removing .dark class on <html>
 */

const STORAGE_KEY = 'docusearch-theme';
const THEME_LIGHT = 'light';
const THEME_DARK = 'dark';
const THEME_SYSTEM = 'system';

/**
 * Get system theme preference
 * @returns {'light'|'dark'} System theme
 */
function getSystemTheme() {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return THEME_DARK;
  }
  return THEME_LIGHT;
}

/**
 * Get saved theme preference from localStorage
 * @returns {'light'|'dark'|'system'|null} Saved theme or null
 */
function getSavedTheme() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch (e) {
    console.warn('Failed to read theme from localStorage:', e);
    return null;
  }
}

/**
 * Save theme preference to localStorage
 * @param {'light'|'dark'|'system'} theme Theme to save
 */
function saveTheme(theme) {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch (e) {
    console.warn('Failed to save theme to localStorage:', e);
  }
}

/**
 * Get the effective theme to apply
 * @returns {'light'|'dark'} Theme to apply
 */
function getEffectiveTheme() {
  const saved = getSavedTheme();

  if (saved === THEME_LIGHT || saved === THEME_DARK) {
    return saved;
  }

  // Default to system preference
  return getSystemTheme();
}

/**
 * Apply theme to document
 * @param {'light'|'dark'} theme Theme to apply
 */
function applyTheme(theme) {
  const html = document.documentElement;

  if (theme === THEME_DARK) {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }

  console.log(`Theme applied: ${theme}`);
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
  const currentTheme = document.documentElement.classList.contains('dark') ? THEME_DARK : THEME_LIGHT;
  const newTheme = currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK;

  applyTheme(newTheme);
  saveTheme(newTheme);

  console.log(`Theme toggled: ${currentTheme} → ${newTheme}`);
}

/**
 * Apply initial theme
 * Call this immediately (before DOM ready) to avoid flash
 */
function applyInitialTheme() {
  const initialTheme = getEffectiveTheme();
  applyTheme(initialTheme);
  console.log('Initial theme applied:', initialTheme);
}

/**
 * Setup theme toggle button(s)
 * Call this after DOM is ready
 * Supports multiple toggle buttons with IDs: theme-toggle, theme-toggle-footer
 */
function setupToggleButton() {
  const toggleButtonIds = ['theme-toggle', 'theme-toggle-footer'];
  let foundButtons = 0;

  toggleButtonIds.forEach(id => {
    const toggleButton = document.getElementById(id);
    if (toggleButton) {
      toggleButton.addEventListener('click', toggleTheme);
      foundButtons++;
      console.log(`Theme toggle button initialized: ${id}`);
    }
  });

  if (foundButtons === 0) {
    console.warn('No theme toggle buttons found');
  }
}

/**
 * Setup system preference listener
 */
function setupSystemListener() {
  if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    // Only respond to system changes if user hasn't set a manual preference
    mediaQuery.addEventListener('change', (e) => {
      const saved = getSavedTheme();

      // If no saved preference or saved as 'system', follow system
      if (!saved || saved === THEME_SYSTEM) {
        const newTheme = e.matches ? THEME_DARK : THEME_LIGHT;
        applyTheme(newTheme);
        console.log(`System theme changed: ${newTheme}`);
      }
    });
  }
}

/**
 * Initialize theme system
 *
 * Sets up:
 * - Initial theme application
 * - Toggle button listener
 * - System preference change listener
 */
export function initTheme() {
  console.log('Initializing theme system...');

  // Apply initial theme (before page renders to avoid flash)
  applyInitialTheme();

  // Setup toggle button (requires DOM)
  setupToggleButton();

  // Listen for system preference changes
  setupSystemListener();

  console.log('Theme system initialized');
}

/**
 * Apply theme early (before DOM ready)
 * Export this for early initialization
 */
export function applyEarlyTheme() {
  applyInitialTheme();
}

/**
 * Get current theme
 * @returns {'light'|'dark'} Current theme
 */
export function getCurrentTheme() {
  return document.documentElement.classList.contains('dark') ? THEME_DARK : THEME_LIGHT;
}

/**
 * Set theme programmatically
 * @param {'light'|'dark'} theme Theme to set
 */
export function setTheme(theme) {
  if (theme !== THEME_LIGHT && theme !== THEME_DARK) {
    console.error(`Invalid theme: ${theme}`);
    return;
  }

  applyTheme(theme);
  saveTheme(theme);
}
