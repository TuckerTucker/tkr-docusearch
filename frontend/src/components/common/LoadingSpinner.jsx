import './LoadingSpinner.css';

/**
 * LoadingSpinner Component
 *
 * A reusable, accessible loading spinner component that displays an animated circular indicator
 * during asynchronous operations. Supports multiple sizes and provides screen reader accessibility
 * through ARIA attributes.
 *
 * @component
 * @param {Object} props - Component props
 * @param {'small'|'medium'} [props.size='medium'] - Size variant of the spinner.
 *   - 'small': 20px diameter, suitable for inline loading states or buttons
 *   - 'medium': 40px diameter, suitable for content areas and full-page loading
 * @param {string} [props.className=''] - Additional CSS classes to apply to the spinner container
 *   for custom styling or positioning
 * @param {string} [props.label='Loading'] - Accessible label announced to screen readers via
 *   aria-label and visually hidden text. Should describe what is loading (e.g., 'Loading search results')
 *
 * @returns {JSX.Element} An accessible loading spinner with animated rotation
 *
 * @example
 * // Basic usage with default medium size
 * <LoadingSpinner />
 *
 * @example
 * // Small spinner for inline loading state
 * <LoadingSpinner size="small" label="Loading results" />
 *
 * @example
 * // Custom styling with additional class
 * <LoadingSpinner
 *   size="medium"
 *   className="my-custom-spinner"
 *   label="Processing document"
 * />
 *
 * @example
 * // Conditional rendering in a component
 * function SearchResults({ isLoading, results }) {
 *   if (isLoading) {
 *     return <LoadingSpinner label="Loading search results" />;
 *   }
 *   return <div>{results.map(r => <div key={r.id}>{r.title}</div>)}</div>;
 * }
 */
export default function LoadingSpinner({
  size = 'medium',
  className = '',
  label = 'Loading'
}) {
  return (
    <div
      className={`loading-spinner loading-spinner--${size} ${className}`}
      role="status"
      aria-label={label}
    >
      <div className="loading-spinner__circle"></div>
      <span className="loading-spinner__sr-only">{label}</span>
    </div>
  );
}
