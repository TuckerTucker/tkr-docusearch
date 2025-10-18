import './LoadingSpinner.css';

/**
 * LoadingSpinner Component
 *
 * Simple spinner component for loading states
 *
 * @param {Object} props
 * @param {'small'|'medium'} props.size - Spinner size (small: 20px, medium: 40px)
 * @param {string} props.className - Additional CSS classes
 * @param {string} props.label - Accessible label for screen readers
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
