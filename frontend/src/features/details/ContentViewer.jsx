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
 * @param {React.Ref} [props.audioPlayerRef] - Ref to access audio player methods
 */
export default function ContentViewer({
  document,
  chunks = [],
  onTimeUpdate,
  onPageChange,
  audioPlayerRef
}) {
  if (!document) {
    return (
      <div className="content-viewer-empty">
        <p>No document loaded.</p>
      </div>
    );
  }

  const fileType = document.file_type?.toLowerCase();

  // Debug logging
  console.log('[ContentViewer] Document:', document);
  console.log('[ContentViewer] File type:', fileType);
  console.log('[ContentViewer] Filename:', document.filename);

  // Document types with visual pages (PDF, DOCX, PPTX)
  const visualTypes = ['pdf', 'docx', 'pptx'];
  const isVisual = visualTypes.includes(fileType);

  // Audio types (MP3, WAV) - check file type AND file extension
  const audioTypes = ['mp3', 'wav', 'audio'];
  const fileExtension = document.filename?.split('.').pop()?.toLowerCase();
  const isAudio = audioTypes.includes(fileType) || ['mp3', 'wav'].includes(fileExtension);

  console.log('[ContentViewer] File extension:', fileExtension);
  console.log('[ContentViewer] Is audio?', isAudio);
  console.log('[ContentViewer] Is visual?', isVisual);

  if (isVisual && document.pages && document.pages.length > 0) {
    console.log('[ContentViewer] Rendering Slideshow');
    return (
      <Slideshow
        document={document}
        onPageChange={onPageChange}
      />
    );
  }

  if (isAudio) {
    console.log('[ContentViewer] Rendering AudioPlayer');
    return (
      <AudioPlayer
        ref={audioPlayerRef}
        document={document}
        chunks={chunks}
        onTimeUpdate={onTimeUpdate}
      />
    );
  }

  // Fallback for unsupported types or missing content
  console.log('[ContentViewer] Rendering fallback (no visual preview)');
  return (
    <div className="content-viewer-unsupported">
      <p>No visual preview available for this document type.</p>
      <p className="file-info">
        File type: <strong>{fileType}</strong>
      </p>
      <p className="file-info">
        File extension: <strong>{fileExtension}</strong>
      </p>
      {document.filename && (
        <p className="file-info">
          Filename: <strong>{document.filename}</strong>
        </p>
      )}
    </div>
  );
}
