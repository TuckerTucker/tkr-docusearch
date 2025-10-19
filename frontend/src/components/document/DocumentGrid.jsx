/**
 * DocumentGrid Component
 *
 * Responsive grid layout for document cards with loading and empty states.
 *
 * Wave 2 - Library Agent
 */

import DocumentCard from './DocumentCard.jsx';
import LoadingSpinner from '../common/LoadingSpinner.jsx';

/**
 * Empty State Component
 */
function EmptyState() {
  return (
    <div className="document-grid__empty" role="status">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="64"
        height="64"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className="document-grid__empty-icon"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
      <h2 className="document-grid__empty-title">No documents found</h2>
      <p className="document-grid__empty-message">
        Upload documents or try adjusting your filters
      </p>
    </div>
  );
}

/**
 * Loading State Component
 */
function LoadingState() {
  return (
    <div className="document-grid__loading" role="status">
      <LoadingSpinner size="medium" />
      <p className="document-grid__loading-message">Loading documents...</p>
    </div>
  );
}

/**
 * DocumentGrid Component
 *
 * @param {Object} props - Component props
 * @param {Array} props.documents - Array of document objects
 * @param {boolean} [props.isLoading=false] - Loading state
 * @param {Function} [props.onDeleteDocument] - Delete handler
 * @param {Function} [props.onViewDetails] - View details handler
 * @returns {JSX.Element} Document grid
 */
export default function DocumentGrid({
  documents = [],
  isLoading = false,
  onDeleteDocument,
  onViewDetails,
}) {
  // Loading state
  if (isLoading) {
    return <LoadingState />;
  }

  // Empty state
  if (documents.length === 0) {
    return <EmptyState />;
  }

  // Grid with documents
  return (
    <div className="document-grid" role="list">
      {documents.map((doc) => (
        <DocumentCard
          key={doc.doc_id || doc.temp_id}
          document={doc}
          onDelete={onDeleteDocument ? (docId, filename) => onDeleteDocument(docId, filename) : undefined}
          onViewDetails={onViewDetails}
        />
      ))}
    </div>
  );
}
