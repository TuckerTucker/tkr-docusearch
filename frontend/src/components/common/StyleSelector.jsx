import useStyleSelector from '../../hooks/useStyleSelector.js';
import './StyleSelector.css';

/**
 * StyleSelector Component
 *
 * A dropdown selector for visual style themes that provides an accessible
 * interface for switching between different visual aesthetics. Integrates
 * with the theme store to persist and apply user preferences.
 *
 * Features:
 * - Dropdown menu with theme previews and descriptions
 * - Keyboard navigation support (Escape to close)
 * - Click-outside-to-close behavior
 * - Visual indicators for active theme
 * - Accessible ARIA attributes
 * - Smooth open/close animations
 *
 * Available Themes:
 * - kraft-paper: Warm kraft paper aesthetic with natural tones
 * - notebook: Grayscale notebook style with handwritten font
 * - blue-on-black: Modern blue and purple accents
 * - gold-on-blue: Elegant gold on blue with serif typography
 * - graphite: Professional grayscale with modern sans-serif
 *
 * @component
 * @returns {React.ReactElement} The rendered StyleSelector component
 *
 * @example
 * // Basic usage - no props required, connects to theme store automatically
 * import StyleSelector from './components/common/StyleSelector';
 *
 * function AppHeader() {
 *   return (
 *     <header>
 *       <h1>Document Search</h1>
 *       <StyleSelector />
 *     </header>
 *   );
 * }
 *
 * @example
 * // The component integrates with useThemeStore
 * // Theme changes are automatically persisted and applied globally
 * import { useThemeStore } from './stores/useThemeStore';
 *
 * function CustomThemeControls() {
 *   const currentStyle = useThemeStore((state) => state.style);
 *
 *   return (
 *     <div>
 *       <p>Current theme: {currentStyle}</p>
 *       <StyleSelector />
 *     </div>
 *   );
 * }
 */
export default function StyleSelector() {
  const {
    style,
    isOpen,
    currentTheme,
    themeList,
    dropdownRef,
    buttonRef,
    handleButtonClick,
    handleKeyDown,
    handleSelectStyle,
  } = useStyleSelector();

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
