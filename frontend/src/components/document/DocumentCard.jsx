/**
 * DocumentCard Component
 *
 * Display document information card with thumbnail, badge, and action button.
 * Supports two variants: document (tall 385x270) and audio (square 300x270).
 * Three states: completed, processing, failed.
 *
 * Wave 2 - Library Agent
 */

import DocumentBadge from './DocumentBadge.jsx';
import DeleteButton from './DeleteButton.jsx';
import DocumentThumbnail from './DocumentThumbnail.jsx';
import DocumentMetadata from './DocumentMetadata.jsx';
import DocumentActions from './DocumentActions.jsx';
import useDocumentCard from '../../hooks/useDocumentCard.js';

/**
 * DocumentCard Component
 *
 * Displays a document information card with thumbnail, badge, and action button.
 * Supports two variants (document: tall 385x270, audio: square 300x270) and four states
 * (uploading, processing, completed, failed). Provides delete functionality and navigation
 * to document details page.
 *
 * @param {Object} props - Component props
 * @param {Object} props.document - Document data object
 * @param {string} props.document.doc_id - Unique document identifier
 * @param {string} props.document.filename - Full filename with extension
 * @param {string} props.document.file_type - File type/extension (e.g., 'pdf', 'mp3')
 * @param {string} props.document.upload_date - ISO 8601 upload timestamp
 * @param {string} [props.document.thumbnail_url] - Thumbnail image URL (document files)
 * @param {string} [props.document.cover_art_url] - Cover art URL (audio files, takes precedence)
 * @param {('uploading'|'processing'|'completed'|'failed')} [props.document.status='completed'] - Document processing status
 * @param {string} [props.document.error_message] - Error message displayed when status is 'failed'
 * @param {string} [props.document.processing_stage] - Current processing stage label (e.g., "Generating embeddings...")
 * @param {number} [props.document.processing_progress] - Processing progress (0-1)
 * @param {Function} [props.onDelete] - Delete handler called with (doc_id, filename)
 * @param {Function} [props.onViewDetails] - View details handler (currently unused, navigation via Link)
 * @param {boolean} [props.priority=false] - Whether to prioritize loading this card's image (for above-fold cards)
 * @returns {JSX.Element} Document card article element
 *
 * @example
 * // Completed document card with delete handler
 * import DocumentCard from './components/document/DocumentCard';
 *
 * function Library() {
 *   const handleDelete = async (docId, filename) => {
 *     await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
 *     // Refresh document list
 *   };
 *
 *   return (
 *     <DocumentCard
 *       document={{
 *         doc_id: '123',
 *         filename: 'report.pdf',
 *         file_type: 'pdf',
 *         upload_date: '2025-10-26T12:00:00Z',
 *         thumbnail_url: '/thumbnails/report_page_0.png',
 *         status: 'completed'
 *       }}
 *       onDelete={handleDelete}
 *       priority={true}
 *     />
 *   );
 * }
 *
 * @example
 * // Processing audio file card
 * <DocumentCard
 *   document={{
 *     doc_id: '456',
 *     filename: 'podcast.mp3',
 *     file_type: 'mp3',
 *     upload_date: '2025-10-26T13:00:00Z',
 *     cover_art_url: '/covers/podcast_cover.png',
 *     status: 'processing',
 *     processing_stage: 'Generating embeddings...',
 *     processing_progress: 0.65
 *   }}
 * />
 *
 * @example
 * // Failed upload card
 * <DocumentCard
 *   document={{
 *     doc_id: '789',
 *     filename: 'broken.pdf',
 *     file_type: 'pdf',
 *     upload_date: '2025-10-26T14:00:00Z',
 *     status: 'failed',
 *     error_message: 'File corrupted or unsupported format'
 *   }}
 *   onDelete={handleDelete}
 * />
 */
export default function DocumentCard({ document, onDelete, priority = false }) {
  const {
    doc_id,
    filename,
    upload_date,
    status,
    error_message,
    processing_stage,
    processing_progress,
    variant,
    displayName,
    thumbnailSrc,
    cardClasses,
    isDeleting,
    handleDelete,
  } = useDocumentCard(document, onDelete);

  return (
    <article className={cardClasses} role="article" aria-label={`Document: ${filename}`}>
      <div className="document-card__left">
        <DocumentThumbnail
          url={thumbnailSrc}
          filename={filename}
          variant={variant}
          status={status}
          priority={priority}
        />
        <DocumentBadge filename={filename} uploadDate={upload_date} />
        {status === 'completed' && onDelete && (
          <DeleteButton
            docId={doc_id}
            filename={filename}
            onDelete={handleDelete}
            isDeleting={isDeleting}
          />
        )}
      </div>

      <div className="document-card__right">
        <DocumentMetadata displayName={displayName} status={status} />
        <DocumentActions
          status={status}
          stage={processing_stage}
          progress={processing_progress}
          errorMessage={error_message}
          docId={doc_id}
          filename={filename}
        />
      </div>
    </article>
  );
}
