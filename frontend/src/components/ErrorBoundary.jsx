import { Component } from 'react';
import ErrorBoundaryErrorDisplay from './ErrorBoundaryErrorDisplay.jsx';
import ErrorBoundaryActions from './ErrorBoundaryActions.jsx';
import './ErrorBoundary.css';

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
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <h1>Something went wrong</h1>
            <p className="error-message">
              An unexpected error occurred. Please try again.
            </p>
            <ErrorBoundaryErrorDisplay error={this.state.error} errorInfo={this.state.errorInfo} />
            <ErrorBoundaryActions onReset={this.handleReset} />
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary
