import React, { useState, useCallback, useRef, useEffect } from 'react';
import { DocumentCard } from './components/DocumentCard/DocumentCard';
import { DocumentListSkeleton } from './components/Skeleton/Skeleton';
import { ToastContainer } from './components/Toast/ToastContainer';
import { WorkerStatus } from './components/WorkerStatus/WorkerStatus';
import type { DocumentCardProps, ViewMode, DocumentStatus, DownloadFormat } from './lib/types';
import { cn } from './lib/utils';
import { validateFile, uploadFile as uploadFileService } from './services/uploadService';
import { listDocuments, downloadDocument as downloadDocumentService, deleteDocument as deleteDocumentService, reprocessDocument } from './services/documentService';
import { useToast } from './hooks/useToast';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcut';
import { useMediaQuery } from './hooks/useMediaQuery';

function App() {
  // State
  const [documents, setDocuments] = useState<DocumentCardProps[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'status'>('date');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const { toasts, dismissToast, success, error, warning, info } = useToast();

  // Track active upload cancel functions by temporary document ID
  const uploadCancelFunctions = useRef<Map<string, () => void>>(new Map());

  // Responsive breakpoints
  const isMobile = useMediaQuery('(max-width: 640px)');

  // Load documents on mount
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setIsLoading(true);
        const docs = await listDocuments();
        setDocuments(docs);
      } catch (err) {
        console.error('Failed to load documents:', err);
        error('Failed to load documents');
      } finally {
        setIsLoading(false);
      }
    };

    loadDocuments();

    // Refresh documents every 5 seconds
    const interval = setInterval(loadDocuments, 5000);
    return () => clearInterval(interval);
  }, [error]);

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      combo: { key: 'u', ctrl: true },
      callback: () => {
        fileInputRef.current?.click();
        info('Upload shortcut: Ctrl+U');
      },
    },
    {
      combo: { key: 'k', ctrl: true },
      callback: () => {
        searchInputRef.current?.focus();
      },
    },
    {
      combo: { key: 'l', ctrl: true },
      callback: () => {
        setViewMode('list');
        info('Switched to list view');
      },
    },
    {
      combo: { key: 'g', ctrl: true },
      callback: () => {
        setViewMode('grid');
        info('Switched to grid view');
      },
    },
  ]);

  // Filter and sort documents
  const filteredDocuments = documents
    .filter((doc) => {
      // Status filter
      if (statusFilter !== 'all' && doc.status !== statusFilter) {
        return false;
      }

      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          doc.title.toLowerCase().includes(query) ||
          doc.fileType.toLowerCase().includes(query) ||
          doc.author?.toLowerCase().includes(query)
        );
      }

      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'name') {
        return a.title.localeCompare(b.title);
      }
      if (sortBy === 'status') {
        return a.status.localeCompare(b.status);
      }
      // Default: sort by date (newest first)
      const dateA = new Date(a.dateProcessed || a.published || 0).getTime();
      const dateB = new Date(b.dateProcessed || b.published || 0).getTime();
      return dateB - dateA;
    });

  // Upload handlers
  const handleFileSelect = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    let successCount = 0;

    for (const file of fileArray) {
      const validation = validateFile(file);
      if (!validation.valid) {
        error(validation.error || 'Invalid file');
        continue;
      }

      // Generate temporary document ID for this upload
      const tempId = `upload-${file.name}-${Date.now()}`;

      // Create temporary document entry in state
      const tempDocument: DocumentCardProps = {
        id: tempId,
        title: file.name,
        status: 'uploading' as DocumentStatus,
        fileType: file.name.split('.').pop()?.toUpperCase() || 'UNKNOWN',
        progress: 0,
        stages: [
          { label: 'Upload', status: 'in-progress' },
          { label: 'Processing', status: 'pending' },
          { label: 'Embeddings', status: 'pending' },
          { label: 'Complete', status: 'pending' },
        ],
      };

      setDocuments((prev) => [tempDocument, ...prev]);

      try {
        // Upload to Copyparty with progress tracking and cancel function
        const { promise, cancel } = uploadFileService(file, (progress) => {
          // Update progress in document state
          setDocuments((prev) =>
            prev.map((doc) =>
              doc.id === tempId ? { ...doc, progress } : doc
            )
          );
        });

        // Store cancel function
        uploadCancelFunctions.current.set(tempId, cancel);

        // Await upload completion
        await promise;

        // Remove cancel function (upload complete)
        uploadCancelFunctions.current.delete(tempId);

        // Remove temporary document (backend will add the real one)
        setDocuments((prev) => prev.filter((doc) => doc.id !== tempId));

        successCount++;
      } catch (err) {
        // Remove cancel function
        uploadCancelFunctions.current.delete(tempId);

        // Check if it was a cancellation
        const errorMessage = (err as Error).message;
        if (errorMessage === 'Upload cancelled') {
          // Remove from document list (already handled by cancel handler)
          return;
        }

        // Show error state in document
        setDocuments((prev) =>
          prev.map((doc) =>
            doc.id === tempId
              ? {
                  ...doc,
                  status: 'error' as DocumentStatus,
                  errorMessage: `Upload failed: ${errorMessage}`,
                  stages: doc.stages?.map((stage, idx) =>
                    idx === 0 ? { ...stage, status: 'error' } : stage
                  ),
                }
              : doc
          )
        );

        console.error(`Failed to upload ${file.name}:`, err);
        error(`Failed to upload ${file.name}`);
      }
    }

    // Show success toast
    if (successCount > 0) {
      success(
        successCount === 1
          ? 'File uploaded successfully. Processing will begin shortly.'
          : `${successCount} files uploaded successfully. Processing will begin shortly.`
      );

      // Refresh document list after a short delay
      setTimeout(async () => {
        const docs = await listDocuments();
        setDocuments(docs);
      }, 2000);
    }
  }, [success, error]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect]
  );

  const handleClickUpload = () => {
    fileInputRef.current?.click();
  };

  // Document handlers
  const handleDelete = useCallback(async (id: string) => {
    const doc = documents.find((d) => d.id === id);

    try {
      const result = await deleteDocumentService(id);
      if (result) {
        setDocuments((prev) => prev.filter((doc) => doc.id !== id));
        if (doc) {
          success(`"${doc.title}" deleted`);
        }
      } else {
        error('Failed to delete document');
      }
    } catch (err) {
      console.error(`Failed to delete document ${id}:`, err);
      error('Failed to delete document');
    }
  }, [documents, success, error]);

  const handleDownload = useCallback(async (id: string, format: DownloadFormat) => {
    const doc = documents.find((d) => d.id === id);

    try {
      if (doc) {
        info(`Downloading "${doc.title}" as ${format.toUpperCase()}...`);
      }

      const blobUrl = await downloadDocumentService(id, format);

      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = doc ? `${doc.title}.${format}` : `document.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up blob URL
      setTimeout(() => URL.revokeObjectURL(blobUrl), 100);

      if (doc) {
        success(`Downloaded "${doc.title}"`);
      }
    } catch (err) {
      console.error(`Failed to download document ${id}:`, err);
      error('Failed to download document');
    }
  }, [documents, info, success, error]);

  const handleCancel = useCallback((id: string) => {
    const doc = documents.find((d) => d.id === id);

    // Call the cancel function if it exists
    const cancelFn = uploadCancelFunctions.current.get(id);
    if (cancelFn) {
      cancelFn();
      uploadCancelFunctions.current.delete(id);
    }

    // Remove from document list
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));

    if (doc) {
      warning(`Upload cancelled: "${doc.title}"`);
    }
  }, [documents, warning]);

  const handleRetry = useCallback(async (id: string) => {
    const doc = documents.find((d) => d.id === id);

    try {
      const result = await reprocessDocument(id);
      if (result) {
        if (doc) {
          info(`Retrying: "${doc.title}"`);
        }

        // Refresh documents after a short delay
        setTimeout(async () => {
          const docs = await listDocuments();
          setDocuments(docs);
        }, 1000);
      } else {
        error('Failed to reprocess document');
      }
    } catch (err) {
      console.error(`Failed to reprocess document ${id}:`, err);
      error('Failed to reprocess document');
    }
  }, [documents, info, error]);

  return (
    <div className="min-h-screen bg-background">
      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <header className={cn(
        'sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60',
        'app-header'
      )}>
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h1 className={cn(
                'font-bold truncate',
                isMobile ? 'text-lg' : 'text-2xl'
              )}>
                DocuSearch
              </h1>
              {!isMobile && (
                <p className="text-sm text-muted-foreground">
                  Document Library with ColPali Search
                </p>
              )}
            </div>

            {/* Worker status and view mode toggle */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {!isMobile && <WorkerStatus />}

              {/* View mode toggle */}
              <div className="flex items-center gap-2 border rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                  viewMode === 'list'
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                )}
                aria-label="List view"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                  viewMode === 'grid'
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                )}
                aria-label="Grid view"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Upload zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClickUpload}
          className={cn(
            'mb-8 border-2 border-dashed rounded-lg',
            'transition-all cursor-pointer',
            'hover:border-primary hover:bg-accent/50',
            'upload-zone',
            isMobile ? 'p-6' : 'p-12',
            isDragging
              ? 'border-primary bg-accent scale-[1.02]'
              : 'border-border'
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.pptx,.txt,.md"
            onChange={(e) => handleFileSelect(e.target.files)}
            className="hidden"
          />
          <div className="text-center">
            <svg
              className={cn(
                'mx-auto text-muted-foreground',
                isMobile ? 'h-8 w-8' : 'h-12 w-12'
              )}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className={cn(
              'mt-4 font-medium',
              isMobile ? 'text-sm' : 'text-base'
            )}>
              {isMobile ? 'Tap to upload' : 'Drop files here or click to upload'}
            </p>
            {!isMobile && (
              <p className="mt-1 text-xs text-muted-foreground">
                PDF, DOCX, PPTX, TXT, or MD files
              </p>
            )}
          </div>
        </div>

        {/* Search and Sort Controls */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          {/* Search bar */}
          <div className="flex-1 relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              ref={searchInputRef}
              type="text"
              placeholder={isMobile ? 'Search...' : 'Search documents... (Ctrl+K)'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                'w-full pl-10 pr-4 py-2 rounded-md border',
                'bg-background text-foreground',
                'placeholder:text-muted-foreground',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                'transition-shadow',
                'search-container'
              )}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-accent"
                aria-label="Clear search"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Sort controls */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'date' | 'status')}
              className={cn(
                'px-3 py-2 rounded-md border bg-background',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                'text-sm'
              )}
            >
              <option value="date">Date</option>
              <option value="name">Name</option>
              <option value="status">Status</option>
            </select>
          </div>
        </div>

        {/* Status filters */}
        <div className="mb-6 flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-muted-foreground">Filter:</span>
          {(['all', 'uploading', 'processing', 'completed', 'error'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                'px-3 py-1 text-xs font-medium rounded-full transition-colors',
                'border',
                statusFilter === status
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'border-border hover:bg-accent'
              )}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
              <span className="ml-1.5 opacity-60">
                ({status === 'all' ? documents.length : documents.filter(d => d.status === status).length})
              </span>
            </button>
          ))}
        </div>

        {/* Document grid/list */}
        {isLoading && documents.length === 0 ? (
          <DocumentListSkeleton count={3} view={viewMode === 'grid' ? 'grid' : 'list'} />
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              {statusFilter === 'all'
                ? 'No documents yet. Upload some files to get started!'
                : `No ${statusFilter} documents.`}
            </p>
          </div>
        ) : (
          <div
            className={cn(
              'gap-4',
              viewMode === 'grid'
                ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
                : 'flex flex-col'
            )}
          >
            {filteredDocuments.map((doc) => (
              <DocumentCard
                key={doc.id}
                {...doc}
                view={viewMode}
                onCancel={() => handleCancel(doc.id)}
                onDelete={() => handleDelete(doc.id)}
                onProcessAgain={() => handleRetry(doc.id)}
                onDownload={(format) => handleDownload(doc.id, format)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>Wave 3 Complete • Search • Sort • Keyboard Shortcuts • Toast Notifications</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
