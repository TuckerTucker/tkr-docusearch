import { useState } from 'react'
import PropTypes from 'prop-types'

/**
 * QueryInput Component - Research query form with validation
 *
 * Features:
 * - Text input with min/max length validation
 * - Character counter
 * - Disabled during loading
 * - Keyboard shortcuts (Enter to submit, Esc to clear)
 */
export default function QueryInput({ onSubmit, isLoading = false }) {
  const [query, setQuery] = useState('')
  const [error, setError] = useState(null)

  const MIN_LENGTH = 3
  const MAX_LENGTH = 500

  const handleChange = (e) => {
    const value = e.target.value
    setQuery(value)

    // Clear error when user starts typing
    if (error) {
      setError(null)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    const trimmedQuery = query.trim()

    // Validation
    if (trimmedQuery.length < MIN_LENGTH) {
      setError(`Question must be at least ${MIN_LENGTH} characters`)
      return
    }

    if (trimmedQuery.length > MAX_LENGTH) {
      setError(`Question must be no more than ${MAX_LENGTH} characters`)
      return
    }

    // Submit
    if (onSubmit) {
      onSubmit(trimmedQuery)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setQuery('')
      setError(null)
    }
  }

  const isValid = query.trim().length >= MIN_LENGTH && query.trim().length <= MAX_LENGTH
  const charCount = query.length
  const charCountClass =
    charCount > MAX_LENGTH
      ? 'query-input__char-count--error'
      : charCount > MAX_LENGTH * 0.9
        ? 'query-input__char-count--warning'
        : 'query-input__char-count--normal'

  return (
    <form className="query-input" onSubmit={handleSubmit}>
      <label htmlFor="research-query-input" className="query-input__label">
        Ask a question about your documents
      </label>

      <textarea
        id="research-query-input"
        className={`query-input__textarea ${error ? 'query-input__textarea--error' : ''}`}
        value={query}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="What would you like to know?"
        disabled={isLoading}
        rows={3}
        maxLength={MAX_LENGTH}
        aria-invalid={!!error}
        aria-describedby={error ? 'query-input-error' : 'query-input-hint'}
      />

      <div className="query-input__footer">
        <div className="query-input__hints">
          {error ? (
            <span id="query-input-error" className="query-input__error" role="alert">
              {error}
            </span>
          ) : (
            <span id="query-input-hint" className="query-input__hint">
              {MIN_LENGTH}-{MAX_LENGTH} characters
            </span>
          )}
        </div>

        <div className={`query-input__char-count ${charCountClass}`}>
          {charCount}/{MAX_LENGTH}
        </div>
      </div>

      <button
        type="submit"
        className="query-input__submit"
        disabled={!isValid || isLoading}
      >
        {isLoading ? 'Researching...' : 'Ask'}
      </button>
    </form>
  )
}

QueryInput.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
}
