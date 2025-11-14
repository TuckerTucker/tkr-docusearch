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

import { useState, useRef, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useDocumentDetails } from '../hooks/useDocumentDetails.js';
import { useTitle } from '../contexts/TitleContext.jsx';
import { formatFilename } from '../utils/formatting.js';
import ContentViewer from '../features/details/ContentViewer.jsx';
import TextAccordion from '../features/details/TextAccordion.jsx';
import LoadingSpinner from '../components/common/LoadingSpinner.jsx';
import { useChunkNavigation } from '../features/details/hooks/useChunkNavigation.ts';

export default function DetailsView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setTitle, setIsLoading: setTitleLoading } = useTitle();

  // Fetch document and markdown
  const { document, markdown, isLoading, error } = useDocumentDetails(id);

  // Helper function to extract chunk index from chunk_id
  // Format: "doc-id-pageN" where N is 1-indexed (page1 = chunk index 0)
  const getChunkIndexFromId = useCallback((chunkId) => {
    if (!chunkId) return null;
    const match = chunkId.match(/page(\d+)$/);
    if (match) {
      const pageNum = parseInt(match[1], 10);
      return pageNum - 1; // Convert to 0-based index
    }
    return null;
  }, []);

  // Handle chunk navigation from URL parameter
  const handleChunkNavigate = useCallback((chunkId) => {
    console.log(`[DetailsView] Chunk navigation requested: ${chunkId}`);

    if (!document) {
      console.log('[DetailsView] Document not loaded yet, deferring chunk navigation');
      return;
    }

    // Detect audio documents by file extension
    const isAudio = document.filename && (
      document.filename.toLowerCase().endsWith('.mp3') ||
      document.filename.toLowerCase().endsWith('.wav')
    );

    // For audio documents, extract chunk index and seek to start time
    if (isAudio && document.chunks) {
      const chunkIndex = getChunkIndexFromId(chunkId);
      console.log(`[DetailsView] Audio detected, chunk index: ${chunkIndex}, total chunks: ${document.chunks.length}`);

      if (chunkIndex !== null && chunkIndex < document.chunks.length) {
        const chunk = document.chunks[chunkIndex];
        const startTime = chunk.start_time;
        console.log(`[DetailsView] Audio: Seeking to chunk ${chunkIndex} at ${startTime}s`);

        // Seek audio player when it's ready
        if (audioPlayerRef.current) {
          audioPlayerRef.current.seekTo(startTime);
          console.log('[DetailsView] seekTo called successfully');
        } else {
          // Store the time to seek to once player is ready
          console.log('[DetailsView] Audio player not ready, will seek once mounted');
          setTimeout(() => {
            if (audioPlayerRef.current) {
              console.log('[DetailsView] Retrying seekTo after delay');
              audioPlayerRef.current.seekTo(startTime);
            } else {
              console.log('[DetailsView] Audio player still not ready after delay');
            }
          }, 1000);
        }
      } else {
        console.log(`[DetailsView] Invalid chunk index or out of bounds: ${chunkIndex}`);
      }
    } else if (document.pages && document.pages.length > 0) {
      // For visual documents (PDF/DOCX/PPTX), extract page number from chunk_id
      const pageNumber = getChunkIndexFromId(chunkId);
      if (pageNumber !== null) {
        // Convert from 0-based index back to 1-based page number
        const targetPage = pageNumber + 1;
        console.log(`[DetailsView] Visual document: Navigating to page ${targetPage} from chunk ${chunkId}`);

        // Navigate slideshow to page
        if (slideshowRef.current && slideshowRef.current.navigateToPage) {
          slideshowRef.current.navigateToPage(targetPage);
          setCurrentPage(targetPage);
          console.log('[DetailsView] Slideshow navigation successful');
        } else {
          console.log('[DetailsView] Slideshow not ready, will navigate once mounted');
          setTimeout(() => {
            if (slideshowRef.current && slideshowRef.current.navigateToPage) {
              console.log('[DetailsView] Retrying slideshow navigation after delay');
              slideshowRef.current.navigateToPage(targetPage);
              setCurrentPage(targetPage);
            } else {
              console.log('[DetailsView] Slideshow still not ready after delay');
            }
          }, 500);
        }

        // Set active chunk for text accordion highlighting
        setActiveChunk({ chunk_id: chunkId });
      } else {
        console.log(`[DetailsView] Could not extract page number from chunk_id: ${chunkId}`);
      }
    }
  }, [document, getChunkIndexFromId]);

  // Use chunk navigation hook
  const { initialChunkId } = useChunkNavigation({
    onChunkNavigate: handleChunkNavigate,
  });

  // Navigate to initial chunk when document loads (for both audio and visual documents)
  useEffect(() => {
    if (initialChunkId && document) {
      console.log(`[DetailsView] Document loaded with chunk parameter, navigating to: ${initialChunkId}`);
      handleChunkNavigate(initialChunkId);
    }
  }, [document, initialChunkId, handleChunkNavigate]);

  // Navigate to page from URL parameter (for visual documents without chunk)
  useEffect(() => {
    const pageParam = searchParams.get('page');
    if (pageParam && document && document.pages && !initialChunkId) {
      const pageNumber = parseInt(pageParam, 10);
      if (!isNaN(pageNumber) && pageNumber > 0) {
        console.log(`[DetailsView] Navigating to page ${pageNumber} from page parameter`);
        if (slideshowRef.current && slideshowRef.current.navigateToPage) {
          slideshowRef.current.navigateToPage(pageNumber);
          setCurrentPage(pageNumber);
        } else {
          setTimeout(() => {
            if (slideshowRef.current && slideshowRef.current.navigateToPage) {
              console.log('[DetailsView] Retrying page navigation after delay');
              slideshowRef.current.navigateToPage(pageNumber);
              setCurrentPage(pageNumber);
            }
          }, 500);
        }
      }
    }
  }, [document, searchParams, initialChunkId]);

  // Update page title when document loads
  useEffect(() => {
    // Set loading state immediately on mount
    setTitleLoading(true);

    if (document?.filename) {
      const displayName = formatFilename(document.filename);
      setTitle(displayName);
      setTitleLoading(false);
      window.document.title = displayName;
    }

    return () => {
      setTitle('Document Library');
      setTitleLoading(false);
      window.document.title = 'DocuSearch - Multimodal Document RAG Library'; // Reset on unmount
    };
  }, [document, setTitle, setTitleLoading]);

  // Refs to access media player methods
  const audioPlayerRef = useRef(null);
  const slideshowRef = useRef(null);

  // State for bidirectional sync
  const [activeChunk, setActiveChunk] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);

  // Handle back navigation
  const handleBack = () => {
    navigate('/');
  };

  // Handle audio time update (for accordion sync)
  const handleTimeUpdate = useCallback((chunk) => {
    setActiveChunk(chunk);
  }, []);

  // Handle timestamp click in accordion (for audio seeking)
  const handleTimestampClick = useCallback((timestamp) => {
    // Access audio player's seekTo method via ref
    if (audioPlayerRef.current) {
      audioPlayerRef.current.seekTo(timestamp);
      console.log(`[DetailsView] Seeking audio to ${timestamp}s`);
    }
  }, []);

  // Handle page change in slideshow (for accordion sync)
  const handlePageChange = useCallback((pageNumber) => {
    console.log(`[DetailsView] Slideshow page changed to: ${pageNumber}`);
    setCurrentPage(pageNumber);
  }, []);

  // Handle page click in accordion (for slideshow navigation)
  const handlePageClick = useCallback((pageNumber) => {
    console.log(`[DetailsView] Accordion clicked, navigating to page: ${pageNumber}`);
    if (slideshowRef.current && slideshowRef.current.navigateToPage) {
      slideshowRef.current.navigateToPage(pageNumber);
    } else {
      console.error(`[DetailsView] slideshowRef.current is null or navigateToPage not available`);
    }
  }, []);

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
          <button onClick={handleBack} className="back-button" aria-label="Go back to Library">
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
      {/* Semantic heading for page structure */}
      <h2 id="content-viewer-title" className="sr-only">Document Content</h2>
      <div className="details-content">
        <section className="details-viewer" aria-labelledby="content-viewer-title">
          <ContentViewer
            document={document}
            chunks={chunks}
            onTimeUpdate={handleTimeUpdate}
            onPageChange={handlePageChange}
            audioPlayerRef={audioPlayerRef}
            slideshowRef={slideshowRef}
          />
        </section>

        <section className="details-text" aria-labelledby="text-content-title">
          <h3 id="text-content-title" className="sr-only">Text Content and Transcript</h3>
          <TextAccordion
            document={document}
            markdown={markdown?.content || markdown}
            chunks={chunks}
            onTimestampClick={handleTimestampClick}
            onPageClick={handlePageClick}
            activeChunk={activeChunk}
            currentPage={currentPage}
          />
        </section>
      </div>
    </div>
  );
}
