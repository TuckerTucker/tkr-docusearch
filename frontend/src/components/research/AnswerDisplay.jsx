import { useMemo } from 'react'
import PropTypes from 'prop-types'
import ReactMarkdown from 'react-markdown'
import CitationLink from './CitationLink.jsx'

/**
 * AnswerDisplay Component - Renders AI-generated answer with inline citations
 *
 * Ported from src/frontend/answer-display.js
 *
 * Features:
 * - Markdown rendering with react-markdown
 * - Inline citation links [N] replaced with CitationLink components
 * - Bidirectional highlighting support
 * - Accessibility-compliant
 */
export default function AnswerDisplay({
  answer,
  references,
  activeReference,
  onCitationClick,
  onCitationHover,
}) {
  // Parse citations from answer text
  const parsedAnswer = useMemo(() => {
    if (!answer) return null
    return parseCitationsInAnswer(answer)
  }, [answer])

  if (!answer) {
    return null
  }

  return (
    <div className="answer-display">
      <h2 className="answer-display__title">Answer</h2>

      <div className="answer-display__content">
        <ReactMarkdown
          components={{
            // Override paragraph renderer to include citation links
            p: ({ children }) => (
              <p className="answer-sentence">
                {renderContentWithCitations(
                  children,
                  activeReference,
                  onCitationClick,
                  onCitationHover
                )}
              </p>
            ),
            // Override list item renderer to include citation links
            li: ({ children }) => (
              <li>
                {renderContentWithCitations(
                  children,
                  activeReference,
                  onCitationClick,
                  onCitationHover
                )}
              </li>
            ),
          }}
        >
          {parsedAnswer}
        </ReactMarkdown>
      </div>
    </div>
  )
}

AnswerDisplay.propTypes = {
  answer: PropTypes.string,
  references: PropTypes.array,
  activeReference: PropTypes.number,
  onCitationClick: PropTypes.func,
  onCitationHover: PropTypes.func,
}

/**
 * Parse citations in answer text
 * Replace [N] markers with unique placeholders for processing
 *
 * @param {string} text - Answer text with citation markers
 * @returns {string} Processed text for markdown rendering
 */
function parseCitationsInAnswer(text) {
  // Keep citation markers as-is for now - we'll handle them in rendering
  return text
}

/**
 * Render content with citation links
 *
 * Recursively processes content to find and replace citation markers [N]
 * with CitationLink components
 *
 * @param {ReactNode|Array} children - React children from markdown
 * @param {number} activeReference - Currently active reference number
 * @param {Function} onCitationClick - Citation click handler
 * @param {Function} onCitationHover - Citation hover handler
 * @returns {ReactNode} Processed children with citation links
 */
function renderContentWithCitations(
  children,
  activeReference,
  onCitationClick,
  onCitationHover
) {
  if (typeof children === 'string') {
    return processCitationsInString(
      children,
      activeReference,
      onCitationClick,
      onCitationHover
    )
  }

  if (Array.isArray(children)) {
    return children.map((child, index) => {
      if (typeof child === 'string') {
        return (
          <span key={index}>
            {processCitationsInString(
              child,
              activeReference,
              onCitationClick,
              onCitationHover
            )}
          </span>
        )
      }
      return child
    })
  }

  return children
}

/**
 * Process citation markers in a string
 *
 * Find all [N] patterns and replace with CitationLink components
 *
 * @param {string} text - Text containing citation markers
 * @param {number} activeReference - Currently active reference number
 * @param {Function} onCitationClick - Citation click handler
 * @param {Function} onCitationHover - Citation hover handler
 * @returns {Array<ReactNode>} Mixed array of text and CitationLink components
 */
function processCitationsInString(
  text,
  activeReference,
  onCitationClick,
  onCitationHover
) {
  // Regex to match citation markers: [N] where N is a number
  const citationRegex = /\[(\d+)\]/g
  const parts = []
  let lastIndex = 0
  let match

  while ((match = citationRegex.exec(text)) !== null) {
    const citationNumber = parseInt(match[1], 10)
    const matchStart = match.index

    // Add text before citation
    if (matchStart > lastIndex) {
      parts.push(text.substring(lastIndex, matchStart))
    }

    // Add CitationLink component
    parts.push(
      <CitationLink
        key={`citation-${matchStart}-${citationNumber}`}
        citationNumber={citationNumber}
        onCitationClick={onCitationClick}
        onCitationHover={onCitationHover}
        isActive={activeReference === citationNumber}
      />
    )

    lastIndex = citationRegex.lastIndex
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex))
  }

  return parts.length > 0 ? parts : text
}
