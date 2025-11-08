import { useState, useCallback, useRef, useEffect } from 'react'
import { useResearch } from '../hooks/useResearch.js'
import ResearchPanel from '../features/research/ResearchPanel.jsx'
import ReferencesPanel from '../features/research/ReferencesPanel.jsx'
import { downloadResearchMarkdown } from '../utils/download.js'

/**
 * ResearchView - AI research interface with citation highlighting
 *
 * Ported from src/frontend/research.html + research-controller.js
 *
 * Features:
 * - Natural language query input with validation
 * - AI-generated answers with inline citations
 * - Reference card list with thumbnails
 * - Bidirectional citation highlighting
 * - Two-panel responsive layout
 * - Empty, loading, error states
 */
export default function ResearchView() {
  const { ask, answer, references, query, metadata, isLoading, error, reset } = useResearch()

  // Track active reference for bidirectional highlighting
  const [activeReference, setActiveReference] = useState(null)

  // Refs for scrolling
  const referencePanelRef = useRef(null)

  /**
   * Handle query submission
   */
  const handleQuerySubmit = useCallback(
    async (queryText) => {
      try {
        await ask(queryText)
      } catch (err) {
        console.error('Research query failed:', err)
        // Error is already tracked in useResearch hook
      }
    },
    [ask]
  )

  /**
   * Handle citation click - scroll to reference and highlight
   */
  const handleCitationClick = useCallback((citationNumber) => {
    setActiveReference(citationNumber)

    // Scroll to reference card
    const referenceCard = document.querySelector(
      `[data-citation-id="${citationNumber}"]`
    )

    if (referenceCard) {
      referenceCard.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }
  }, [])

  /**
   * Handle citation hover - highlight reference
   */
  const handleCitationHover = useCallback((citationNumber, isHovering) => {
    if (isHovering) {
      setActiveReference(citationNumber)
    } else {
      setActiveReference(null)
    }
  }, [])

  /**
   * Handle reference hover - highlight citation
   */
  const handleReferenceHover = useCallback((citationNumber, isHovering) => {
    if (isHovering) {
      setActiveReference(citationNumber)

      // Optionally scroll citation into view
      const citationLink = document.querySelector(
        `[data-citation-number="${citationNumber}"]`
      )

      if (citationLink) {
        const rect = citationLink.getBoundingClientRect()
        const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight

        if (!isVisible) {
          citationLink.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
          })
        }
      }
    } else {
      setActiveReference(null)
    }
  }, [])

  /**
   * Handle download report - generate and download markdown file
   */
  const handleDownloadReport = useCallback(() => {
    if (query && answer && references) {
      downloadResearchMarkdown(query, answer, references, metadata)
    }
  }, [query, answer, references, metadata])

  // Clear active reference when answer changes
  useEffect(() => {
    setActiveReference(null)
  }, [answer])

  return (
    <div className="research-view">
      {/* Semantic heading for page structure (H2 after H1 from Header) */}
      <h2 id="research-view-title" className="sr-only">Research Questions and Answers</h2>
      <div className="research-view__layout">
        {/* Left panel: Query input + Answer display */}
        <section className="research-view__main-panel" aria-labelledby="research-view-title">
          <ResearchPanel
            query={query}
            answer={answer}
            references={references}
            metadata={metadata}
            isLoading={isLoading}
            error={error}
            onQuerySubmit={handleQuerySubmit}
            activeReference={activeReference}
            onCitationClick={handleCitationClick}
            onCitationHover={handleCitationHover}
            onDownloadReport={handleDownloadReport}
          />
        </section>

        {/* Right panel: References list */}
        <section className="research-view__side-panel" ref={referencePanelRef} aria-labelledby="references-panel-title">
          <h3 id="references-panel-title" className="sr-only">Source References</h3>
          <ReferencesPanel
            references={references}
            activeReference={activeReference}
            onReferenceHover={handleReferenceHover}
          />
        </section>
      </div>
    </div>
  )
}
