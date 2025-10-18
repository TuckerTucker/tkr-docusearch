/**
 * ContentViewer Component
 *
 * Conditional content viewer that renders appropriate media component
 * based on document file type (Slideshow for documents, AudioPlayer for audio).
 *
 * Wave 2 - Details Agent
 */

import Slideshow from '../../components/media/Slideshow.jsx';
import AudioPlayer from '../../components/media/AudioPlayer.jsx';

/**
 * Content viewer with type-based rendering
 *
 * @param {Object} props - Component props
 * @param {Object} props.document - Document with metadata and content
 * @param {Array} [props.chunks=[]] - Text chunks for audio sync
 * @param {Function} [props.onTimeUpdate] - Audio time update callback
 * @param {Function} [props.onPageChange] - Slideshow page change callback
 */
export default function ContentViewer({
  document,
  chunks = [],
  onTimeUpdate,
  onPageChange
}) {
  if (!document) {
    return (
      <div className="content-viewer-empty">
        <p>No document loaded.</p>
      </div>
    );
  }

  const fileType = document.file_type?.toLowerCase();

  // Document types with visual pages (PDF, DOCX, PPTX)
  const visualTypes = ['pdf', 'docx', 'pptx'];
  const isVisual = visualTypes.includes(fileType);

  // Audio types (MP3, WAV)
  const audioTypes = ['mp3', 'wav', 'audio'];
  const isAudio = audioTypes.includes(fileType);

  if (isVisual && document.pageImages && document.pageImages.length > 0) {
    return (
      <Slideshow
        document={document}
        onPageChange={onPageChange}
      />
    );
  }

  if (isAudio) {
    return (
      <AudioPlayer
        document={document}
        chunks={chunks}
        onTimeUpdate={onTimeUpdate}
      />
    );
  }

  // Fallback for unsupported types or missing content
  return (
    <div className="content-viewer-unsupported">
      <p>No visual preview available for this document type.</p>
      <p className="file-info">
        File type: <strong>{fileType}</strong>
      </p>
      {document.filename && (
        <p className="file-info">
          Filename: <strong>{document.filename}</strong>
        </p>
      )}
    </div>
  );
}
