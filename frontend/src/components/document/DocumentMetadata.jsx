/**
 * DocumentMetadata Component
 *
 * Displays document title for completed documents.
 * Extracted sub-component for DocumentCard.
 *
 * @param {Object} props - Component props
 * @param {string} props.displayName - Formatted display name without extension
 * @param {string} props.status - Document processing status
 * @returns {JSX.Element} Title element or null
 */

export default function DocumentMetadata({ displayName, status }) {
  // Only show title for completed documents
  if (status === 'completed') {
    return <h3 className="document-card__title">{displayName}</h3>;
  }
  return null;
}
