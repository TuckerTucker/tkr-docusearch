/**
 * DeleteButtonSmall Component
 *
 * Small trash icon delete button (hover state).
 * Extracted sub-component for DeleteButton.
 *
 * @param {Object} props - Component props
 * @param {string} props.filename - Document filename
 * @param {Function} props.onClick - Click handler
 * @param {boolean} props.disabled - Disable state
 * @returns {JSX.Element} Small delete button
 */

export default function DeleteButtonSmall({ filename, onClick, disabled }) {
  return (
    <button
      className="delete-button delete-button--small"
      onClick={onClick}
      disabled={disabled}
      aria-label={`Delete ${filename}`}
      title={`Delete ${filename}`}
      type="button"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6" />
      </svg>
    </button>
  );
}
