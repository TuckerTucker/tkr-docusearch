import { Outlet, useLocation } from 'react-router-dom';
import { useTitle } from '../../contexts/TitleContext';
import Header from './Header';
import Footer from './Footer';
import './Layout.css';

/**
 * Layout Component
 *
 * Main layout wrapper for all pages providing consistent Header and Footer across routes.
 * Manages route-specific header configurations and provides accessibility features including
 * skip navigation links for keyboard and screen reader users (WCAG 2.4.1).
 *
 * Route-specific header props:
 * - / → Document Library (with research link, filter bar)
 * - /details/:id → Dynamic filename (with back button, no filter bar)
 * - /research → Research (with back button, no filter bar)
 *
 * @returns {JSX.Element} Layout wrapper with Header, main content area (Outlet), and Footer
 *
 * @example
 * // Used as the root layout in React Router configuration
 * import { createBrowserRouter, RouterProvider } from 'react-router-dom';
 * import Layout from './components/layout/Layout';
 * import Library from './pages/Library';
 * import DocumentDetails from './pages/DocumentDetails';
 *
 * const router = createBrowserRouter([
 *   {
 *     path: '/',
 *     element: <Layout />,
 *     children: [
 *       { index: true, element: <Library /> },
 *       { path: 'details/:id', element: <DocumentDetails /> },
 *       { path: 'research', element: <Research /> }
 *     ]
 *   }
 * ]);
 *
 * function App() {
 *   return <RouterProvider router={router} />;
 * }
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
      <Header {...headerProps} />

      <main className="layout__main" role="main">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}
