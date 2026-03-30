/**
 * useResearchSession Hook - Multi-turn research sessions
 *
 * Manages conversation state with session-backed research queries.
 * Each session maintains context across multiple question/answer turns,
 * allowing follow-up questions that reference prior conversation history.
 *
 * @returns {Object} Session interface for multi-turn research
 * @returns {Function} returns.ask - Async function to submit query within session
 * @returns {Array} returns.turns - Conversation history
 * @returns {string|null} returns.sessionId - Active session ID
 * @returns {Array} returns.latestSources - Sources from most recent assistant turn
 * @returns {boolean} returns.isLoading - Loading state
 * @returns {Error|null} returns.error - Error if query failed
 * @returns {Function} returns.reset - Clear session and start fresh
 */
import { useState, useCallback, useRef } from 'react'
import { api } from '../services/api.js'

export function useResearchSession() {
  const [sessionId, setSessionId] = useState(null)
  const [turns, setTurns] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const sessionIdRef = useRef(null)

  const ask = useCallback(async (query) => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await api.research.sessions.ask({
        session_id: sessionIdRef.current,
        query,
      })

      sessionIdRef.current = data.session_id
      setSessionId(data.session_id)
      setTurns((prev) => {
        const next = [
          ...prev,
          {
            role: 'user',
            content: query,
            timestamp: new Date().toISOString(),
          },
          {
            role: 'assistant',
            content: data.answer,
            sources: data.sources || [],
            citations: data.citations || [],
            citationMap: data.citation_map || {},
            metadata: data.metadata || null,
            timestamp: new Date().toISOString(),
          },
        ]
        return next
      })

      return data
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    sessionIdRef.current = null
    setSessionId(null)
    setTurns([])
    setIsLoading(false)
    setError(null)
  }, [])

  // Sources from the latest assistant turn (for the references panel)
  const latestAssistantTurn = [...turns].reverse().find((t) => t.role === 'assistant')

  return {
    ask,
    turns,
    sessionId,
    latestSources: latestAssistantTurn?.sources || [],
    isLoading,
    error,
    reset,
  }
}
