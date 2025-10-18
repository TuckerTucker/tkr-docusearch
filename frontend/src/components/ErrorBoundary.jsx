import { Component } from 'react'

/**
 * ErrorBoundary - React error boundary component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 *
 * Wave 1 - Foundation Agent
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // Log error details to console
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    // Update state with error details
    this.setState({
      error,
      errorInfo
    })

    // You could also log the error to an error reporting service here
    // e.g., Sentry.captureException(error)
  }

  handleReset = () => {
    // Reset error boundary state
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <h1>Something went wrong</h1>
            <p className="error-message">
              An unexpected error occurred. Please try again.
            </p>

            {this.state.error && (
              <details className="error-details">
                <summary>Error details</summary>
                <pre className="error-stack">
                  <strong>{this.state.error.toString()}</strong>
                  {this.state.errorInfo && (
                    <>
                      {'\n\n'}
                      {this.state.errorInfo.componentStack}
                    </>
                  )}
                </pre>
              </details>
            )}

            <div className="error-actions">
              <button
                onClick={this.handleReset}
                className="btn btn-primary"
                type="button"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="btn btn-secondary"
                type="button"
              >
                Go to Home
              </button>
            </div>
          </div>

          <style>{`
            .error-boundary {
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              padding: 2rem;
              background-color: var(--bg-primary, #f5f5f5);
            }

            .error-boundary-content {
              max-width: 600px;
              background-color: var(--bg-secondary, #ffffff);
              padding: 2rem;
              border-radius: 0.5rem;
              box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .error-boundary h1 {
              font-size: 1.5rem;
              font-weight: 600;
              margin-bottom: 1rem;
              color: var(--fg-primary, #333);
            }

            .error-message {
              margin-bottom: 1.5rem;
              color: var(--fg-secondary, #666);
              line-height: 1.5;
            }

            .error-details {
              margin-bottom: 1.5rem;
              padding: 1rem;
              background-color: var(--bg-primary, #f5f5f5);
              border-radius: 0.25rem;
              border: 1px solid var(--border-color, #ddd);
            }

            .error-details summary {
              cursor: pointer;
              font-weight: 500;
              margin-bottom: 0.5rem;
              color: var(--fg-secondary, #666);
            }

            .error-details summary:hover {
              color: var(--fg-primary, #333);
            }

            .error-stack {
              margin-top: 0.5rem;
              padding: 0.75rem;
              background-color: #f8f8f8;
              border-radius: 0.25rem;
              overflow-x: auto;
              font-size: 0.875rem;
              line-height: 1.5;
              color: #d63031;
              white-space: pre-wrap;
              word-wrap: break-word;
            }

            .error-actions {
              display: flex;
              gap: 1rem;
              flex-wrap: wrap;
            }

            .error-actions .btn {
              padding: 0.5rem 1rem;
              border: none;
              border-radius: 0.25rem;
              font-size: 0.875rem;
              font-weight: 500;
              cursor: pointer;
              transition: all 0.2s;
            }

            .error-actions .btn-primary {
              background-color: var(--primary-base, #9f8d76);
              color: white;
            }

            .error-actions .btn-primary:hover {
              background-color: var(--primary-hover, #8a7a65);
            }

            .error-actions .btn-secondary {
              background-color: transparent;
              color: var(--fg-secondary, #666);
              border: 1px solid var(--border-color, #ddd);
            }

            .error-actions .btn-secondary:hover {
              background-color: var(--bg-primary, #f5f5f5);
            }
          `}</style>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
