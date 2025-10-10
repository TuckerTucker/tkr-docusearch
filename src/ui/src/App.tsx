import React, { useState, useCallback, useRef } from 'react';
import { DocumentCard } from './components/DocumentCard/DocumentCard';
import { ToastContainer } from './components/Toast/ToastContainer';
import { WorkerStatus } from './components/WorkerStatus/WorkerStatus';
import { getMockDocuments } from './lib/mockData';
import type { DocumentCardProps, ViewMode, DocumentStatus, DownloadFormat } from './lib/types';
import { cn } from './lib/utils';
import { validateFile } from './services/uploadService';
import { useToast } from './hooks/useToast';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcut';

function App() {
  // State
  const [documents, setDocuments] = useState<DocumentCardProps[]>(getMockDocuments());
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'status'>('date');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const { toasts, dismissToast, success, error, warning, info } = useToast();

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
  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    let successCount = 0;
    let errorCount = 0;

    fileArray.forEach((file) => {
      const validation = validateFile(file);
      if (!validation.valid) {
        error(validation.error || 'Invalid file');
        errorCount++;
        return;
      }

      successCount++;

      // Create mock uploading document
      const newDoc: DocumentCardProps = {
        id: `doc-${Date.now()}-${Math.random()}`,
        title: file.name,
        status: 'uploading',
        fileType: file.name.split('.').pop()?.toUpperCase() || 'FILE',
        progress: 0,
        stages: [
          { label: 'Upload', status: 'in-progress' },
          { label: 'Transcribe Audio', status: 'pending' },
          { label: 'Embeddings', status: 'pending' },
          { label: 'Finalizing', status: 'pending' },
        ],
      };

      setDocuments((prev) => [newDoc, ...prev]);

      // Simulate upload progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        if (progress <= 100) {
          setDocuments((prev) =>
            prev.map((doc) =>
              doc.id === newDoc.id
                ? { ...doc, progress }
                : doc
            )
          );
        } else {
          clearInterval(interval);
          // Transition to processing
          setDocuments((prev) =>
            prev.map((doc) =>
              doc.id === newDoc.id
                ? {
                    ...doc,
                    status: 'processing',
                    progress: 25,
                    stages: [
                      { label: 'Upload', status: 'completed' },
                      { label: 'Transcribe Audio', status: 'in-progress' },
                      { label: 'Embeddings', status: 'pending' },
                      { label: 'Finalizing', status: 'pending' },
                    ],
                  }
                : doc
            )
          );
        }
      }, 200);
    });

    // Show success toast
    if (successCount > 0) {
      success(
        successCount === 1
          ? 'File uploaded successfully'
          : `${successCount} files uploaded successfully`
      );
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
  const handleDelete = useCallback((id: string) => {
    const doc = documents.find((d) => d.id === id);
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    if (doc) {
      success(`"${doc.title}" deleted`);
    }
  }, [documents, success]);

  const handleDownload = useCallback((id: string, format: DownloadFormat) => {
    const doc = documents.find((d) => d.id === id);
    console.log(`Downloading document ${id} as ${format}`);
    if (doc) {
      info(`Downloading "${doc.title}" as ${format.toUpperCase()}`);
    }
  }, [documents, info]);

  const handleCancel = useCallback((id: string) => {
    const doc = documents.find((d) => d.id === id);
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    if (doc) {
      warning(`Upload cancelled: "${doc.title}"`);
    }
  }, [documents, warning]);

  const handleRetry = useCallback((id: string) => {
    const doc = documents.find((d) => d.id === id);
    setDocuments((prev) =>
      prev.map((doc) =>
        doc.id === id
          ? {
              ...doc,
              status: 'processing',
              progress: 0,
              errorMessage: undefined,
              stages: [
                { label: 'Upload', status: 'completed' },
                { label: 'Transcribe Audio', status: 'in-progress' },
                { label: 'Embeddings', status: 'pending' },
                { label: 'Finalizing', status: 'pending' },
              ],
            }
          : doc
      )
    );
    if (doc) {
      info(`Retrying: "${doc.title}"`);
    }
  }, [documents, info]);

  return (
    <div className="min-h-screen bg-background">
      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold">DocuSearch</h1>
              <p className="text-sm text-muted-foreground">
                Document Library with ColPali Search
              </p>
            </div>

            {/* Worker status and view mode toggle */}
            <div className="flex items-center gap-3">
              <WorkerStatus />

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
            'mb-8 border-2 border-dashed rounded-lg p-12',
            'transition-all cursor-pointer',
            'hover:border-primary hover:bg-accent/50',
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
              className="mx-auto h-12 w-12 text-muted-foreground"
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
            <p className="mt-4 text-sm font-medium">
              Drop files here or click to upload
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              PDF, DOCX, PPTX, TXT, or MD files
            </p>
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
              placeholder="Search documents... (Ctrl+K)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                'w-full pl-10 pr-4 py-2 rounded-md border',
                'bg-background text-foreground',
                'placeholder:text-muted-foreground',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                'transition-shadow'
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
        {filteredDocuments.length === 0 ? (
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
