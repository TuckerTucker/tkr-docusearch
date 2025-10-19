/**
 * DetailsView - Document detail page with slideshow/audio player
 *
 * Full implementation with two-column layout:
 * - Left: ContentViewer (Slideshow or AudioPlayer)
 * - Right: TextAccordion (Markdown and chunks)
 *
 * Features:
 * - Document metadata display
 * - PDF/PPTX slideshow viewer with keyboard navigation
 * - Audio player with album art and VTT captions
 * - Transcript accordion with bidirectional sync
 * - Download and clipboard actions
 * - Back to library navigation
 *
 * Wave 2 - Details Agent
 */

import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDocumentDetails } from '../hooks/useDocumentDetails.js';
import { useTitle } from '../contexts/TitleContext.jsx';
import ContentViewer from '../features/details/ContentViewer.jsx';
import TextAccordion from '../features/details/TextAccordion.jsx';
import LoadingSpinner from '../components/common/LoadingSpinner.jsx';

export default function DetailsView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { setTitle, setIsLoading: setTitleLoading } = useTitle();

  // Fetch document and markdown
  const { document, markdown, isLoading, error } = useDocumentDetails(id);

  // Update page title when document loads
  useEffect(() => {
    // Set loading state immediately on mount
    setTitleLoading(true);

    if (document?.filename) {
      setTitle(document.filename);
      setTitleLoading(false);
      window.document.title = document.filename;
    }

    return () => {
      setTitle('Document Library');
      setTitleLoading(false);
      window.document.title = 'frontend'; // Reset on unmount
    };
  }, [document, setTitle, setTitleLoading]);

  // Ref to access audio player methods (for accordion click-to-seek)
  const audioPlayerRef = useRef(null);

  // State for bidirectional sync
  const [activeChunk, setActiveChunk] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);

  // Handle back navigation
  const handleBack = () => {
    navigate('/');
  };

  // Handle audio time update (for accordion sync)
  const handleTimeUpdate = (chunk) => {
    setActiveChunk(chunk);
  };

  // Handle timestamp click in accordion (for audio seeking)
  const handleTimestampClick = (timestamp) => {
    // Access audio player's seekTo method via ref
    if (audioPlayerRef.current) {
      audioPlayerRef.current.seekTo(timestamp);
      console.log(`[DetailsView] Seeking audio to ${timestamp}s`);
    }
  };

  // Handle page change in slideshow
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="details-view">
        <div className="details-loading">
          <LoadingSpinner size="medium" />
          <p>Loading document...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="details-view">
        <header className="details-header">
          <button onClick={handleBack} className="back-button">
            ← Back to Library
          </button>
        </header>
        <div className="details-error">
          <h2>Document Not Found</h2>
          <p>{error.message || 'Could not load document details.'}</p>
          <button onClick={handleBack} className="btn-primary">
            Return to Library
          </button>
        </div>
      </div>
    );
  }

  // No document
  if (!document) {
    return (
      <div className="details-view">
        <header className="details-header">
          <button onClick={handleBack} className="back-button">
            ← Back to Library
          </button>
        </header>
        <div className="details-error">
          <h2>Document Not Found</h2>
          <p>The requested document could not be found.</p>
          <button onClick={handleBack} className="btn-primary">
            Return to Library
          </button>
        </div>
      </div>
    );
  }

  // Extract chunks from document
  const chunks = document.chunks || [];

  return (
    <div className="details-view">
      <div className="details-content">
        <div className="details-viewer">
          <ContentViewer
            document={document}
            chunks={chunks}
            onTimeUpdate={handleTimeUpdate}
            onPageChange={handlePageChange}
            audioPlayerRef={audioPlayerRef}
          />
        </div>

        <div className="details-text">
          <TextAccordion
            document={document}
            markdown={markdown?.content || markdown}
            chunks={chunks}
            onTimestampClick={handleTimestampClick}
            activeChunk={activeChunk}
          />
        </div>
      </div>
    </div>
  );
}
