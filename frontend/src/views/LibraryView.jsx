/**
 * LibraryView - Main document library page
 *
 * Complete implementation with filtering, sorting, uploading, and real-time updates.
 * Integrates FilterBar, DocumentGrid, and UploadModal with WebSocket for live document status.
 *
 * Wave 2 - Library Agent
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocuments } from '../hooks/useDocuments.js';
import { useWebSocket } from '../hooks/useWebSocket.js';
import { useDocumentStore } from '../stores/useDocumentStore.js';
import { useTitle } from '../contexts/TitleContext.jsx';
import { WS_URL } from '../constants/config.js';
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
  const { setHeaderContent } = useTitle();

  // Get filters from store
  const filters = useDocumentStore((state) => state.filters);
  const tempDocuments = useDocumentStore((state) => state.tempDocuments);
  const tempDocumentsVersion = useDocumentStore((state) => state.tempDocumentsVersion);
  const getTempDocument = useCallback((doc_id) => {
    return useDocumentStore.getState().tempDocuments.get(doc_id);
  }, []);
  const getTempDocumentCount = useCallback(() => {
    return useDocumentStore.getState().tempDocuments.size;
  }, []);
  const removeTempDocument = useDocumentStore((state) => state.removeTempDocument);
  const setTempDocumentStatus = useDocumentStore((state) => state.setTempDocumentStatus);
  const updateTempDocumentProgress = useDocumentStore(
    (state) => state.updateTempDocumentProgress
  );

  // Fetch documents with current filters
  const { documents, totalCount, isLoading, error, refetch, deleteDocument, isDeleting } =
    useDocuments(filters);

  // Merge real documents with temp documents for optimistic UI
  const mergedDocuments = useMemo(() => {
    // Convert temp documents Map to array
    const tempDocs = Array.from(tempDocuments.entries()).map(([tempId, data]) => ({
      temp_id: tempId,
      doc_id: tempId,
      filename: data.filename,
      file_type: data.filename.split('.').pop(),
      upload_date: new Date().toISOString(),
      status: data.status,
      processing_progress: data.progress / 100,
      processing_stage: data.stage || (data.status === 'uploading' ? 'Uploading...' : 'Processing...'),
    }));

    // Merge temp docs at the beginning (newest first)
    return [...tempDocs, ...(documents || [])];
  }, [documents, tempDocumentsVersion]); // Re-render when temp documents change

  // WebSocket for real-time document status updates
  const { isConnected, registerUploadBatch } = useWebSocket(WS_URL, {
    onMessage: useCallback(
      (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', data);

          // Handle both 'document_status' and 'status_update' message types
          if (data.type === 'document_status' || data.type === 'status_update') {
            const { doc_id, status, stage, progress } = data;
            console.log('📊 Status update:', { doc_id, status, stage, progress });

            // Look up temp document by doc_id (using fresh state to avoid stale closures)
            const tempDoc = getTempDocument(doc_id);
            const allTempDocs = useDocumentStore.getState().tempDocuments;

            console.log('🔍 Looking for temp doc:', {
              incoming_doc_id: doc_id,
              found: !!tempDoc,
              tempDocCount: getTempDocumentCount(),
              all_temp_doc_ids: Array.from(allTempDocs.keys())
            });

            if (tempDoc) {
              if (status === 'completed') {
                // Remove temp document and refetch to get real document
                console.log('✅ Document completed, removing temp and refetching');
                removeTempDocument(doc_id);
                refetch();
              } else if (status === 'processing' || status === 'parsing' || status === 'embedding_visual' || status === 'embedding_text' || status === 'storing') {
                // Update status, stage, and progress (all processing states)
                console.log('🔄 Updating temp document:', { doc_id: doc_id?.slice(0, 8), status: 'processing', stage, progress });
                setTempDocumentStatus(doc_id, 'processing', stage);
                if (progress !== undefined) {
                  updateTempDocumentProgress(doc_id, Math.round(progress * 100));
                }
              } else if (status === 'failed') {
                // Mark as failed
                console.log('❌ Document failed');
                setTempDocumentStatus(doc_id, 'failed');
              }
            } else if (status === 'completed') {
              // Document completed but no temp doc found, just refetch
              console.log('⚠️ No temp doc found but status is completed, refetching');
              refetch();
            }
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      },
      [
        getTempDocument,
        getTempDocumentCount,
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
      navigate(`/details/${docId}`);
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

  // Set FilterBar in header on mount, clear on unmount
  useEffect(() => {
    setHeaderContent(<FilterBar totalCount={totalCount} onFilterChange={handleFilterChange} />);
    return () => {
      setHeaderContent(null);
    };
  }, [totalCount, handleFilterChange, setHeaderContent]);

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
      <UploadModal
        onUploadComplete={handleUploadComplete}
        registerUploadBatch={registerUploadBatch}
      />
    </div>
  );
}
