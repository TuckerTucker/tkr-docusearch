import { Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import ErrorBoundary from './components/ErrorBoundary'
import { TitleProvider } from './contexts/TitleContext'
import Layout from './components/layout/Layout'

// Lazy load route components for better performance
const LibraryView = lazy(() => import('./views/LibraryView'))
const DetailsView = lazy(() => import('./views/DetailsView'))
const ResearchView = lazy(() => import('./views/ResearchView'))
const ResearchExploreView = lazy(() => import('./views/ResearchExploreView'))
const LocalInferenceView = lazy(() => import('./views/LocalInferenceView'))

// Loading component for suspense fallback
const PageLoader = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    fontSize: '1.2rem',
    color: 'var(--text-secondary, #666)'
  }}>
    Loading...
  </div>
)

/**
 * App - Root component with routing configuration
 *
 * Routes:
 * - / → LibraryView (main document library)
 * - /details/:id → DetailsView (document detail page)
 * - /research → ResearchView (AI research interface)
 * - /research-explore → ResearchExploreView (experimental research interface)
 * - /local-inference → LocalInferenceView (local MLX inference test)
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
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<LibraryView />} />
              <Route path="/details/:id" element={<DetailsView />} />
              <Route path="/research" element={<ResearchView />} />
              <Route path="/research-explore" element={<ResearchExploreView />} />
              <Route path="/local-inference" element={<LocalInferenceView />} />
            </Route>
          </Routes>
        </Suspense>
      </TitleProvider>
    </ErrorBoundary>
  )
}

export default App
