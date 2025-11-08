/**
 * useStyleSelector Hook
 *
 * Custom hook for managing theme selection state and keyboard/click-outside behavior.
 * Encapsulates all dropdown logic for StyleSelector component.
 *
 * @returns {Object} Theme and dropdown state with handlers
 * @returns {string} returns.style - Current selected style ID
 * @returns {boolean} returns.isOpen - Dropdown open state
 * @returns {Object} returns.currentTheme - Current theme object with id, name, description
 * @returns {Array<Object>} returns.themeList - Array of all available themes
 * @returns {Object} returns.dropdownRef - React ref for dropdown element
 * @returns {Object} returns.buttonRef - React ref for button element
 * @returns {Function} returns.handleButtonClick - Click handler for toggle button
 * @returns {Function} returns.handleKeyDown - Keydown handler for Escape key
 * @returns {Function} returns.handleSelectStyle - Handler for theme selection
 *
 * @example
 * // Basic usage in StyleSelector component
 * const {
 *   currentTheme,
 *   themeList,
 *   isOpen,
 *   handleButtonClick,
 *   handleKeyDown,
 *   handleSelectStyle,
 *   dropdownRef,
 *   buttonRef,
 * } = useStyleSelector();
 *
 * return (
 *   <div>
 *     <button ref={buttonRef} onClick={handleButtonClick}>
 *       {currentTheme.name}
 *     </button>
 *     {isOpen && (
 *       <div ref={dropdownRef} onKeyDown={handleKeyDown}>
 *         {themeList.map(theme => (
 *           <button key={theme.id} onClick={() => handleSelectStyle(theme.id)}>
 *             {theme.name}
 *           </button>
 *         ))}
 *       </div>
 *     )}
 *   </div>
 * );
 */

import { useState, useRef, useEffect } from 'react';
import { useThemeStore } from '../stores/useThemeStore';

const THEMES = {
  'kraft-paper': {
    id: 'kraft-paper',
    name: 'Kraft Paper',
    description: 'Warm kraft paper aesthetic with natural tones',
  },
  'notebook': {
    id: 'notebook',
    name: 'Notebook',
    description: 'Grayscale notebook style with handwritten font',
  },
  'blue-on-black': {
    id: 'blue-on-black',
    name: 'Blue on Black',
    description: 'Modern blue and purple accents',
  },
  'gold-on-blue': {
    id: 'gold-on-blue',
    name: 'Gold on Blue',
    description: 'Elegant gold on blue with serif typography',
  },
  'graphite': {
    id: 'graphite',
    name: 'Graphite',
    description: 'Professional grayscale with modern sans-serif',
  },
};

export default function useStyleSelector() {
  const style = useThemeStore((state) => state.style);
  const setStyle = useThemeStore((state) => state.setStyle);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);

  const currentTheme = THEMES[style] || THEMES['kraft-paper'];
  const themeList = Object.values(THEMES);

  // Handle click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        !isOpen ||
        (dropdownRef.current && dropdownRef.current.contains(event.target)) ||
        (buttonRef.current && buttonRef.current.contains(event.target))
      ) {
        return;
      }
      setIsOpen(false);
    }

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isOpen]);

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
    setIsOpen(!isOpen);
  };

  return {
    style,
    isOpen,
    currentTheme,
    themeList,
    dropdownRef,
    buttonRef,
    handleButtonClick,
    handleKeyDown,
    handleSelectStyle,
  };
}
