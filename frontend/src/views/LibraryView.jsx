/**
 * LibraryView - Main document library page
 *
 * Complete implementation with filtering, sorting, uploading, and real-time updates.
 * Integrates FilterBar, DocumentGrid, and UploadModal with WebSocket for live document status.
 *
 * Wave 2 - Library Agent
 */

import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocuments } from '../hooks/useDocuments.js';
import { useWebSocket } from '../hooks/useWebSocket.js';
import { useDocumentStore } from '../stores/useDocumentStore.js';
import FilterBar from '../features/library/FilterBar.jsx';
import DocumentGrid from '../components/document/DocumentGrid.jsx';
import UploadModal from '../features/library/UploadModal.jsx';

/**
 * LibraryView Component
 *
 * Main document library page with filtering, sorting, pagination, upload, and real-time updates.
 *
 * @returns {JSX.Element} Library view
 */
export default function LibraryView() {
  const navigate = useNavigate();

  // Get filters from store
  const filters = useDocumentStore((state) => state.filters);
  const tempDocuments = useDocumentStore((state) => state.tempDocuments);
  const removeTempDocument = useDocumentStore((state) => state.removeTempDocument);
  const setTempDocumentStatus = useDocumentStore((state) => state.setTempDocumentStatus);
  const updateTempDocumentProgress = useDocumentStore(
    (state) => state.updateTempDocumentProgress
  );

  // Fetch documents with current filters
  const { documents, totalCount, isLoading, error, refetch, deleteDocument, isDeleting } =
    useDocuments(filters);

  // Merge real documents with temp documents for optimistic UI
  const [mergedDocuments, setMergedDocuments] = useState([]);

  useEffect(() => {
    // Convert temp documents Map to array
    const tempDocs = Array.from(tempDocuments.entries()).map(([tempId, data]) => ({
      temp_id: tempId,
      doc_id: tempId,
      filename: data.filename,
      file_type: data.filename.split('.').pop(),
      upload_date: new Date().toISOString(),
      status: data.status,
      processing_progress: data.progress / 100,
      processing_stage: data.status === 'uploading' ? 'Uploading...' : 'Processing...',
    }));

    // Merge temp docs at the beginning (newest first)
    setMergedDocuments([...tempDocs, ...documents]);
  }, [documents, tempDocuments]);

  // WebSocket for real-time document status updates
  const { isConnected } = useWebSocket('ws://localhost:8002/ws', {
    onMessage: useCallback(
      (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'document_status') {
            const { filename, status, stage, progress } = data;

            // Find temp document by filename
            const tempDoc = Array.from(tempDocuments.entries()).find(
              ([, doc]) => doc.filename === filename
            );

            if (tempDoc) {
              const [tempId] = tempDoc;

              if (status === 'completed') {
                // Remove temp document and refetch to get real document
                removeTempDocument(tempId);
                refetch();
              } else if (status === 'processing') {
                // Update status and progress
                setTempDocumentStatus(tempId, 'processing');
                if (progress !== undefined) {
                  updateTempDocumentProgress(tempId, Math.round(progress * 100));
                }
              } else if (status === 'failed') {
                // Mark as failed
                setTempDocumentStatus(tempId, 'failed');
              }
            } else if (status === 'completed') {
              // Document completed but no temp doc found, just refetch
              refetch();
            }
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      },
      [
        tempDocuments,
        removeTempDocument,
        setTempDocumentStatus,
        updateTempDocumentProgress,
        refetch,
      ]
    ),
  });

  // Handle filter changes
  const handleFilterChange = useCallback(
    (newFilters) => {
      // Filters are already updated in store by FilterBar
      // Just refetch with new filters (happens automatically via useDocuments)
    },
    []
  );

  // Handle document deletion
  const handleDeleteDocument = useCallback(
    async (docId) => {
      if (window.confirm('Are you sure you want to delete this document?')) {
        try {
          await deleteDocument(docId);
        } catch (err) {
          console.error('Error deleting document:', err);
          alert(`Failed to delete document: ${err.message}`);
        }
      }
    },
    [deleteDocument]
  );

  // Handle view details
  const handleViewDetails = useCallback(
    (docId) => {
      navigate(`/document/${docId}`);
    },
    [navigate]
  );

  // Handle upload completion
  const handleUploadComplete = useCallback(
    ({ total, successful, failed }) => {
      console.log(`Upload complete: ${successful}/${total} successful, ${failed} failed`);

      // Refetch documents to show newly uploaded files
      // (they'll appear when WebSocket sends 'completed' status)
    },
    []
  );

  // Show error state
  if (error) {
    return (
      <div className="library-view">
        <div className="library-error" role="alert">
          <h2>Error loading documents</h2>
          <p>{error.message}</p>
          <button onClick={() => refetch()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="library-view">
      {/* Filter bar */}
      <FilterBar totalCount={totalCount} onFilterChange={handleFilterChange} />

      {/* Document grid */}
      <div className="library-content">
        <DocumentGrid
          documents={mergedDocuments}
          isLoading={isLoading}
          onDeleteDocument={handleDeleteDocument}
          onViewDetails={handleViewDetails}
        />
      </div>

      {/* Upload modal (global drag-drop) */}
      <UploadModal onUploadComplete={handleUploadComplete} />
    </div>
  );
}
