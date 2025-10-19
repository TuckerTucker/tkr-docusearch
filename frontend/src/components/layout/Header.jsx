import { Link } from 'react-router-dom';
import './Header.css';

/**
 * Header Component
 *
 * Application header with dynamic content based on current route
 *
 * @param {Object} props
 * @param {string} props.title - Page title to display
 * @param {boolean} props.showBackButton - Whether to show back button
 * @param {string} props.backTo - Route to navigate back to (default: '/')
 * @param {React.ReactNode} props.filterBar - Filter bar component to render
 */
export default function Header({
  title = 'Document Search',
  showBackButton = false,
  backTo = '/',
  filterBar = null
}) {
  return (
    <header className="header" role="banner">
      <div className="header__container">
        <div className="header__left">
          {showBackButton && (
            <Link to={backTo} className="header__back-button" aria-label="Go back">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
              <span className="header__back-text">Back to Library</span>
            </Link>
          )}
          {title && <h1 className="header__title">{title}</h1>}
          {filterBar && <div className="header__filter-bar">{filterBar}</div>}
        </div>
      </div>
    </header>
  );
}
