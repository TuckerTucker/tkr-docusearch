import { Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import { TitleProvider } from './contexts/TitleContext'
import Layout from './components/layout/Layout'
import LibraryView from './views/LibraryView'
import DetailsView from './views/DetailsView'
import ResearchView from './views/ResearchView'
import ResearchExploreView from './views/ResearchExploreView'
import LocalInferenceView from './views/LocalInferenceView'

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
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<LibraryView />} />
            <Route path="/details/:id" element={<DetailsView />} />
            <Route path="/research" element={<ResearchView />} />
            <Route path="/research-explore" element={<ResearchExploreView />} />
            <Route path="/local-inference" element={<LocalInferenceView />} />
          </Route>
        </Routes>
      </TitleProvider>
    </ErrorBoundary>
  )
}

export default App
