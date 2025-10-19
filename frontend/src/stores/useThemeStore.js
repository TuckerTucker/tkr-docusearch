/**
 * Theme Store - Theme and style management
 *
 * Manages theme (light/dark/system) and visual style with Zustand + persist.
 * Applies theme changes to DOM and dispatches custom events.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/stores.contract.md
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Detect system theme preference
 *
 * @returns {string} 'light' or 'dark'
 */
function detectSystemTheme() {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/**
 * Apply theme to DOM
 *
 * @param {string} theme - 'light' or 'dark'
 */
function applyTheme(theme) {
  if (typeof document === 'undefined') return;

  const html = document.documentElement;
  if (theme === 'dark') {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }

  // Dispatch custom event for theme change
  window.dispatchEvent(
    new CustomEvent('themechange', {
      detail: { theme },
    })
  );
}

/**
 * Load style CSS file dynamically
 *
 * @param {string} style - Style name (e.g., 'kraft-paper')
 */
function loadStyle(style) {
  if (typeof document === 'undefined') return;

  // Remove existing style link
  const existingLink = document.getElementById('theme-style-link');
  if (existingLink) {
    existingLink.remove();
  }

  // Force a small delay to ensure the old stylesheet is fully removed
  // This helps prevent FOUC and ensures clean CSS variable replacement
  setTimeout(() => {
    // Always add a new style link (all themes including kraft-paper)
    const link = document.createElement('link');
    link.id = 'theme-style-link';
    link.rel = 'stylesheet';
    // Add cache-busting parameter to force reload
    link.href = `/styles/themes/${style}.css?t=${Date.now()}`;

    // Force a repaint to ensure CSS variables are applied
    link.onload = () => {
      document.body.style.display = 'none';
      document.body.offsetHeight; // Trigger reflow
      document.body.style.display = '';
    };

    document.head.appendChild(link);

    // Dispatch custom event for style change
    window.dispatchEvent(
      new CustomEvent('stylechange', {
        detail: { style },
      })
    );
  }, 50); // Small delay to ensure clean removal
}

/**
 * Theme store with persistence
 */
export const useThemeStore = create(
  persist(
    (set, get) => ({
      // State
      theme: 'system', // 'light' | 'dark' | 'system'
      style: 'kraft-paper', // 'kraft-paper' | 'graphite' | 'notebook' | 'gold-on-blue' | 'blue-on-black'
      systemTheme: detectSystemTheme(), // 'light' | 'dark'

      // Actions
      setTheme: (theme) => {
        set({ theme });
        const effectiveTheme = theme === 'system' ? get().systemTheme : theme;
        applyTheme(effectiveTheme);
      },

      setStyle: (style) => {
        set({ style });
        loadStyle(style);
      },

      detectSystemTheme: () => {
        const systemTheme = detectSystemTheme();
        set({ systemTheme });

        // If using system theme, update applied theme
        const { theme } = get();
        if (theme === 'system') {
          applyTheme(systemTheme);
        }
      },

      getEffectiveTheme: () => {
        const { theme, systemTheme } = get();
        return theme === 'system' ? systemTheme : theme;
      },

      // Initialize theme on load
      _initialize: () => {
        const effectiveTheme = get().getEffectiveTheme();
        applyTheme(effectiveTheme);
        loadStyle(get().style);

        // Listen for system theme changes
        if (typeof window !== 'undefined') {
          window
            .matchMedia('(prefers-color-scheme: dark)')
            .addEventListener('change', () => {
              get().detectSystemTheme();
            });
        }
      },
    }),
    {
      name: 'docusearch-theme',
      partialize: (state) => ({
        theme: state.theme,
        style: state.style,
      }),
    }
  )
);

// Initialize theme on module load
if (typeof window !== 'undefined') {
  useThemeStore.getState()._initialize();
}
