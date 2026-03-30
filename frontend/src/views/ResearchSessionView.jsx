import { useState, useCallback, useRef, useEffect } from 'react'
import { useResearchSession } from '../hooks/useResearchSession.js'
import QueryInput from '../components/research/QueryInput.jsx'
import AnswerDisplay from '../components/research/AnswerDisplay.jsx'
import ReferencesPanel from '../features/research/ReferencesPanel.jsx'
import './ResearchSessionView.css'

/**
 * ResearchSessionView - Multi-turn research conversation interface
 *
 * Two-panel layout matching ResearchView structure. Left panel displays a scrollable
 * conversation thread of user questions and AI-generated answers with inline citations.
 * A sticky query input sits at the bottom. Right panel shows source references for
 * the active assistant turn.
 *
 * Features:
 * - Multi-turn conversation with session-backed context
 * - Auto-scroll to latest turn
 * - Bidirectional citation highlighting between answer and references
 * - Per-turn source references in side panel
 * - New session reset button
 * - Empty, loading, error states
 * - Accessible conversation log with live region semantics
 */
export default function ResearchSessionView() {
  const { ask, turns, sessionId, latestSources, isLoading, error, reset } =
    useResearchSession()

  // Track active reference for bidirectional highlighting
  const [activeReference, setActiveReference] = useState(null)

  // Which assistant turn's sources to show (null = latest)
  const [activeTurnIndex, setActiveTurnIndex] = useState(null)

  // Ref for auto-scrolling to bottom of thread
  const threadEndRef = useRef(null)

  // Auto-scroll to bottom when new turns are added
  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns.length])

  // Clear active reference when turns change
  useEffect(() => {
    setActiveReference(null)
  }, [turns.length])

  // Determine which assistant turn's sources to display
  const assistantTurns = turns.filter((t) => t.role === 'assistant')
  const activeTurn =
    activeTurnIndex !== null
      ? assistantTurns[activeTurnIndex]
      : assistantTurns[assistantTurns.length - 1]
  const activeReferences = activeTurn?.sources || []

  /**
   * Handle query submission
   */
  const handleQuerySubmit = useCallback(
    async (queryText) => {
      try {
        await ask(queryText)
      } catch (err) {
        console.error('Session query failed:', err)
      }
    },
    [ask]
  )

  /**
   * Handle citation click - scroll to reference and highlight
   */
  const handleCitationClick = useCallback((citationNumber) => {
    setActiveReference(citationNumber)

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
    setActiveReference(isHovering ? citationNumber : null)
  }, [])

  /**
   * Handle reference hover - highlight citation in answer
   */
  const handleReferenceHover = useCallback((citationNumber, isHovering) => {
    if (isHovering) {
      setActiveReference(citationNumber)

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
   * Handle clicking an assistant turn to show its sources
   */
  const handleTurnSourceSelect = useCallback(
    (turnIndex) => {
      setActiveTurnIndex((prev) => (prev === turnIndex ? null : turnIndex))
    },
    []
  )

  return (
    <div className="research-session-view">
      <h2 className="sr-only">Research Conversation</h2>

      <div className="research-session-view__layout">
        {/* Left panel: Conversation thread + sticky input */}
        <section
          className="research-session-view__main-panel"
          aria-label="Research conversation"
        >
          {/* Conversation turns */}
          {turns.map((turn, index) => (
            <div
              key={index}
              className={`conversation-turn conversation-turn--${turn.role}`}
            >
              {turn.role === 'user' ? (
                <div className="conversation-turn__user-message">
                  {turn.content}
                </div>
              ) : (
                <div className="conversation-turn__assistant-message">
                  <AnswerDisplay
                    answer={turn.content}
                    references={turn.sources}
                    activeReference={activeReference}
                    onCitationClick={handleCitationClick}
                    onCitationHover={handleCitationHover}
                  />
                  {turn.metadata && (
                    <div className="conversation-turn__meta">
                      <span>{turn.metadata.model_used}</span>
                      <span> · </span>
                      <span>{turn.sources?.length || 0} sources</span>
                      {turn.metadata.processing_time_ms > 0 && (
                        <span> · {turn.metadata.processing_time_ms}ms</span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="conversation-turn conversation-turn--loading">
              Researching...
            </div>
          )}

          {error && (
            <div className="conversation-turn conversation-turn--error">
              {error.message || 'Research query failed. Please try again.'}
            </div>
          )}

          <div ref={threadEndRef} />

          {/* Input */}
          <div className="research-session-view__input-dock">
            {sessionId && (
              <button
                className="research-session-view__new-session"
                onClick={reset}
                type="button"
                aria-label="Start a new research session"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden="true"
                >
                  <polyline points="1 4 1 10 7 10" />
                  <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                </svg>
                New Session
              </button>
            )}
            <QueryInput onSubmit={handleQuerySubmit} isLoading={isLoading} />
          </div>
        </section>

        {/* Right panel: References for active turn */}
        <section
          className="research-session-view__side-panel"
          aria-label="Source References"
        >
          <h3 className="sr-only">Source References</h3>
          <ReferencesPanel
            references={activeReferences}
            activeReference={activeReference}
            onReferenceHover={handleReferenceHover}
          />
        </section>
      </div>
    </div>
  )
}
