import { Outlet, useLocation } from 'react-router-dom';
import { useTitle } from '../../contexts/TitleContext';
import Header from './Header';
import Footer from './Footer';
import './Layout.css';

/**
 * Layout Component
 *
 * Main layout wrapper for all pages
 * Provides consistent Header and Footer across routes
 *
 * Route-specific header props:
 * - / → Document Library (with research link)
 * - /details/:id → Dynamic filename (with back button)
 * - /research → Research (with back button)
 */
export default function Layout() {
  const location = useLocation();
  const { title, isLoading, headerContent } = useTitle();

  // Determine header props based on current route
  const getHeaderProps = () => {
    const path = location.pathname;

    // Details page - use dynamic title from context
    // Don't render title until loaded to prevent flash
    if (path.startsWith('/details/')) {
      return {
        title: isLoading ? '' : title,
        showBackButton: true,
        backTo: '/',
        filterBar: null
      };
    }

    // Research page
    if (path === '/research') {
      return {
        title: 'Research',
        showBackButton: true,
        backTo: '/',
        filterBar: null
      };
    }

    // Default (library/home)
    return {
      title: '',
      showBackButton: false,
      filterBar: headerContent
    };
  };

  const headerProps = getHeaderProps();

  return (
    <div className="layout">
      {/* Skip navigation for keyboard and screen reader users (WCAG 2.4.1) */}
      <div className="skip-links">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
      </div>

      <Header {...headerProps} />

      <main id="main-content" className="layout__main" role="main">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}
