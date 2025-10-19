import { Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import { TitleProvider } from './contexts/TitleContext'
import Layout from './components/layout/Layout'
import LibraryView from './views/LibraryView'
import DetailsView from './views/DetailsView'
import ResearchView from './views/ResearchView'

/**
 * App - Root component with routing configuration
 *
 * Routes:
 * - / → LibraryView (main document library)
 * - /details/:id → DetailsView (document detail page)
 * - /research → ResearchView (AI research interface)
 *
 * Wave 1 - Foundation Agent
 * - Added ErrorBoundary for application-wide error handling
 *
 * Wave 1 - Layout Agent
 * - Added Layout wrapper with Header and Footer
 * - Dynamic header props based on route
 * - Theme toggle, style selector, and connection status in footer
 */
function App() {
  return (
    <ErrorBoundary>
      <TitleProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<LibraryView />} />
            <Route path="/details/:id" element={<DetailsView />} />
            <Route path="/research" element={<ResearchView />} />
          </Route>
        </Routes>
      </TitleProvider>
    </ErrorBoundary>
  )
}

export default App
