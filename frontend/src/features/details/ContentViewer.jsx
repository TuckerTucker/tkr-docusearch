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
 * @param {React.Ref} [props.slideshowRef] - Ref to access slideshow methods
 */
export default function ContentViewer({
  document,
  chunks = [],
  onTimeUpdate,
  onPageChange,
  audioPlayerRef,
  slideshowRef
}) {
  if (!document) {
    return (
      <div className="content-viewer-empty">
        <p>No document loaded.</p>
      </div>
    );
  }

  const fileType = document.file_type?.toLowerCase();
  const fileExtension = document.filename?.split('.').pop()?.toLowerCase();

  // Debug logging
  console.log('[ContentViewer] Document:', document);
  console.log('[ContentViewer] File type:', fileType);
  console.log('[ContentViewer] File extension:', fileExtension);
  console.log('[ContentViewer] Filename:', document.filename);

  // Document types with visual pages (PDF, DOCX, PPTX)
  // Check both file_type field AND file extension (fallback for when file_type is null)
  const visualTypes = ['pdf', 'docx', 'pptx'];
  const isVisual = visualTypes.includes(fileType) || visualTypes.includes(fileExtension);

  // Audio types (MP3, WAV) - check file type AND file extension
  const audioTypes = ['mp3', 'wav', 'audio'];
  const isAudio = audioTypes.includes(fileType) || ['mp3', 'wav'].includes(fileExtension);

  console.log('[ContentViewer] Is visual?', isVisual);
  console.log('[ContentViewer] Is audio?', isAudio);

  if (isVisual && document.pages && document.pages.length > 0) {
    console.log('[ContentViewer] Rendering Slideshow');
    return (
      <Slideshow
        ref={slideshowRef}
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
