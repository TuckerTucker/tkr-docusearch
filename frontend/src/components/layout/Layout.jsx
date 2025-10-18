import { Outlet, useLocation } from 'react-router-dom';
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
 * - /details/:id → Document Details (with back button)
 * - /research → Research (with back button)
 */
export default function Layout() {
  const location = useLocation();

  // Determine header props based on current route
  const getHeaderProps = () => {
    const path = location.pathname;

    // Details page
    if (path.startsWith('/details/')) {
      return {
        title: 'Document Details',
        showBackButton: true,
        backTo: '/',
        showResearchLink: false
      };
    }

    // Research page
    if (path === '/research') {
      return {
        title: 'Research',
        showBackButton: true,
        backTo: '/',
        showResearchLink: false
      };
    }

    // Default (library/home)
    return {
      title: 'Document Library',
      showBackButton: false,
      showResearchLink: true
    };
  };

  const headerProps = getHeaderProps();

  return (
    <div className="layout">
      <Header {...headerProps} />

      <main className="layout__main">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}
