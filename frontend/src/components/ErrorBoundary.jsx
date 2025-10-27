import { Component } from 'react'

/**
 * ErrorBoundary - React error boundary component
 *
 * A React error boundary that catches JavaScript errors anywhere in the child component tree,
 * logs error details to the console, and displays a user-friendly fallback UI with error details
 * and recovery options. Implements React's error boundary lifecycle methods for robust error handling.
 *
 * Error boundaries catch errors during rendering, in lifecycle methods, and in constructors of the
 * whole tree below them. They do NOT catch errors in event handlers, asynchronous code, or server-side
 * rendering.
 *
 * @component
 * @extends {Component}
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to wrap with error boundary protection
 *
 * @returns {JSX.Element} Either renders children normally or displays error fallback UI when an error is caught
 *
 * @example
 * // Basic usage wrapping the entire app
 * import ErrorBoundary from './components/ErrorBoundary';
 *
 * function App() {
 *   return (
 *     <ErrorBoundary>
 *       <MainApp />
 *     </ErrorBoundary>
 *   );
 * }
 *
 * @example
 * // Wrapping specific feature sections
 * function Dashboard() {
 *   return (
 *     <div>
 *       <Header />
 *       <ErrorBoundary>
 *         <SearchFeature />
 *       </ErrorBoundary>
 *       <ErrorBoundary>
 *         <ResearchFeature />
 *       </ErrorBoundary>
 *     </div>
 *   );
 * }
 *
 * @example
 * // Nested error boundaries for granular error handling
 * function Layout() {
 *   return (
 *     <ErrorBoundary>
 *       <Sidebar />
 *       <main>
 *         <ErrorBoundary>
 *           <ComplexFeature />
 *         </ErrorBoundary>
 *       </main>
 *     </ErrorBoundary>
 *   );
 * }
 *
 * Wave 1 - Foundation Agent
 */
class ErrorBoundary extends Component {
  /**
   * Initializes the ErrorBoundary component with error state
   *
   * @param {Object} props - Component props containing children to protect
   */
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  /**
   * Static lifecycle method called when an error is thrown in a descendant component
   *
   * @static
   * @param {Error} error - The error that was thrown
   * @returns {Object} Updated state object to trigger fallback UI rendering
   */
  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true }
  }

  /**
   * Lifecycle method called after an error has been thrown by a descendant component
   * Logs error details and updates state with full error information for display
   *
   * @param {Error} error - The error that was thrown
   * @param {Object} errorInfo - Object containing componentStack with information about component stack trace
   * @param {string} errorInfo.componentStack - Stack trace showing which components threw the error
   */
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

  /**
   * Resets the error boundary state to allow retry
   * Called when user clicks "Try Again" button in the error UI
   *
   * @returns {void}
   */
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
