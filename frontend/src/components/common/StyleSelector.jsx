import { useState, useRef, useEffect } from 'react';
import { useThemeStore } from '../../stores/useThemeStore';
import './StyleSelector.css';

/**
 * StyleSelector Component
 *
 * Dropdown selector for visual style themes
 *
 * Styles:
 * - kraft-paper: Warm kraft paper aesthetic
 * - graphite: Professional grayscale
 * - notebook: Grayscale notebook style
 * - gold-on-blue: Elegant gold on blue
 * - blue-on-black: Modern blue and purple
 */

const THEMES = {
  'kraft-paper': {
    id: 'kraft-paper',
    name: 'Kraft Paper',
    description: 'Warm kraft paper aesthetic with natural tones'
  },
  'notebook': {
    id: 'notebook',
    name: 'Notebook',
    description: 'Grayscale notebook style with handwritten font'
  },
  'blue-on-black': {
    id: 'blue-on-black',
    name: 'Blue on Black',
    description: 'Modern blue and purple accents'
  },
  'gold-on-blue': {
    id: 'gold-on-blue',
    name: 'Gold on Blue',
    description: 'Elegant gold on blue with serif typography'
  },
  'graphite': {
    id: 'graphite',
    name: 'Graphite',
    description: 'Professional grayscale with modern sans-serif'
  }
};

export default function StyleSelector() {
  const style = useThemeStore((state) => state.style);
  const setStyle = useThemeStore((state) => state.setStyle);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);
  const isOpeningRef = useRef(false);

  const currentTheme = THEMES[style] || THEMES['kraft-paper'];
  const themeList = Object.values(THEMES);

  // Close dropdown when clicking outside - register once on mount
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        !isOpen ||
        (dropdownRef.current && dropdownRef.current.contains(event.target)) ||
        (buttonRef.current && buttonRef.current.contains(event.target))
      ) {
        return;
      }

      console.log('Clicking outside, closing dropdown');
      setIsOpen(false);
    }

    // Register listener once on mount
    document.addEventListener('click', handleClickOutside);

    // Cleanup on unmount
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isOpen]); // Include isOpen in deps so handler has current value

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      buttonRef.current?.focus();
    }
  };

  const handleSelectStyle = (styleId) => {
    setStyle(styleId);
    setIsOpen(false);
  };

  const handleButtonClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Button clicked, target:', e.target, 'currentTarget:', e.currentTarget, 'isOpen:', isOpen, '-> toggling to:', !isOpen);
    setIsOpen(!isOpen);
  };

  return (
    <div className="style-selector">
      <button
        ref={buttonRef}
        type="button"
        className="style-selector__button"
        onClick={handleButtonClick}
        onKeyDown={handleKeyDown}
        aria-label="Select visual style"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <span className="style-selector__button-text">Style: {currentTheme.name}</span>
        <svg
          className={`style-selector__arrow ${isOpen ? 'style-selector__arrow--open' : ''}`}
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      <div
        ref={dropdownRef}
        className={`style-selector__dropdown ${isOpen ? 'style-selector__dropdown--open' : ''}`}
        role="listbox"
        aria-label="Visual style themes"
        aria-hidden={!isOpen}
        onKeyDown={handleKeyDown}
      >
        <ul className="style-selector__list">
          {themeList.map((theme) => (
            <li key={theme.id} className="style-selector__item">
              <button
                type="button"
                className={`style-selector__option ${
                  theme.id === style ? 'style-selector__option--active' : ''
                }`}
                onClick={() => handleSelectStyle(theme.id)}
                role="option"
                aria-selected={theme.id === style}
              >
                <div className="style-selector__option-content">
                  <div className="style-selector__option-name">{theme.name}</div>
                  <div className="style-selector__option-description">{theme.description}</div>
                </div>
                {theme.id === style && (
                  <svg
                    className="style-selector__checkmark"
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
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
