/**
 * UploadModal Component Tests
 *
 * Comprehensive test suite for UploadModal.jsx covering:
 * - File selection and validation
 * - Upload progress tracking
 * - Error handling (file size limits, invalid file types)
 * - Cancel upload functionality
 * - Success state after upload completion
 * - Modal open/close behavior
 * - Integration with upload API
 * - Duplicate file handling
 * - WebSocket connection dependency
 * - Drag and drop functionality
 *
 * Task 7 - Test Agent (Wave 1 Testing Infrastructure)
 * Target Coverage: 80%+
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadModal from '../UploadModal.jsx';
import { api } from '../../../services/api.js';
import { useDocumentStore } from '../../../stores/useDocumentStore.js';

// Mock the API service
vi.mock('../../../services/api.js', () => ({
  api: {
    upload: {
      uploadFile: vi.fn(),
    },
  },
}));

// Mock the document store
vi.mock('../../../stores/useDocumentStore.js', () => {
  const mockStore = {
    addTempDocument: vi.fn(),
    updateTempDocumentProgress: vi.fn(),
    setTempDocumentStatus: vi.fn(),
    clearAllTempDocuments: vi.fn(),
  };

  return {
    useDocumentStore: vi.fn((selector) => {
      if (typeof selector === 'function') {
        return selector(mockStore);
      }
      return mockStore;
    }),
  };
});

describe('UploadModal', () => {
  let mockRegisterUploadBatch;
  let mockOnUploadComplete;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Create mock functions
    mockRegisterUploadBatch = vi.fn();
    mockOnUploadComplete = vi.fn();

    // Setup default mock implementations
    mockRegisterUploadBatch.mockResolvedValue([
      { filename: 'test.pdf', doc_id: 'doc-123', is_duplicate: false },
    ]);

    api.upload.uploadFile.mockImplementation((file, onProgress) => {
      // Simulate upload progress
      if (onProgress) {
        onProgress(50);
        onProgress(100);
      }
      return Promise.resolve({ success: true, filename: file.name });
    });

    // Reset document event listeners
    document.body.innerHTML = '';
  });

  afterEach(() => {
    // Clean up any remaining event listeners
    vi.clearAllTimers();
  });

  describe('Modal Visibility', () => {
    it('should not render when modal is not visible', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should show modal when dragenter event is fired', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      // Simulate drag enter
      fireEvent.dragEnter(document.body, {
        dataTransfer: { files: [] },
      });

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Drop files to upload')).toBeInTheDocument();
    });

    it('should hide modal when dragleave is fired after delay', async () => {
      vi.useFakeTimers();

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      // Show modal
      fireEvent.dragEnter(document.body);
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Hide modal
      fireEvent.dragLeave(document.body);

      // Wait for the 100ms delay
      await act(async () => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });

    it('should show modal when manualUpload event is dispatched', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const event = new CustomEvent('manualUpload', {
        detail: { files: [file] },
      });

      window.dispatchEvent(event);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('should close modal when Cancel button is clicked', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      // Show modal
      fireEvent.dragEnter(document.body);
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Click cancel button
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('should not close modal when Cancel button is clicked during upload', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      // Trigger upload
      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/uploading/i)).toBeInTheDocument();
      });

      // Try to cancel during upload
      const cancelButton = screen.getByRole('button', { name: /uploading/i });
      expect(cancelButton).toBeDisabled();
    });

    it('should close modal by clicking backdrop when not uploading', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      // Show modal
      fireEvent.dragEnter(document.body);

      const backdrop = document.querySelector('.upload-modal__backdrop');
      fireEvent.click(backdrop);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('File Validation', () => {
    it('should accept valid PDF file', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(mockRegisterUploadBatch).toHaveBeenCalledWith([file]);
      });
    });

    it('should accept valid DOCX file', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'document.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(mockRegisterUploadBatch).toHaveBeenCalledWith([file]);
      });
    });

    it('should reject unsupported file type', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.exe', { type: 'application/x-msdownload' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/Unsupported file type: .exe/i)).toBeInTheDocument();
      });

      // Should not attempt to upload
      expect(api.upload.uploadFile).not.toHaveBeenCalled();
    });

    it('should reject file exceeding size limit', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      // Create a file larger than 100MB by mocking the size property
      const file = new File(['content'], 'large.pdf', { type: 'application/pdf' });
      Object.defineProperty(file, 'size', { value: 101 * 1024 * 1024 });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/File exceeds maximum size of 100MB/i)).toBeInTheDocument();
      });

      // Should not attempt to upload
      expect(api.upload.uploadFile).not.toHaveBeenCalled();
    });

    it('should show supported file types in modal', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      fireEvent.dragEnter(document.body);

      expect(screen.getByText(/Supported:/i)).toBeInTheDocument();
      expect(screen.getByText(/PDF, DOCX/i)).toBeInTheDocument();
    });
  });

  describe('File Upload Flow', () => {
    it('should upload single file successfully', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(api.upload.uploadFile).toHaveBeenCalledWith(file, expect.any(Function));
      });

      await waitFor(() => {
        expect(screen.getByText(/✓ Complete/i)).toBeInTheDocument();
      });

      expect(mockOnUploadComplete).toHaveBeenCalledWith({
        total: 1,
        successful: 1,
        failed: 0,
      });
    });

    it('should upload multiple files in parallel', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      mockRegisterUploadBatch.mockResolvedValue([
        { filename: 'test1.pdf', doc_id: 'doc-123', is_duplicate: false },
        { filename: 'test2.pdf', doc_id: 'doc-456', is_duplicate: false },
      ]);

      const files = [
        new File(['content1'], 'test1.pdf', { type: 'application/pdf' }),
        new File(['content2'], 'test2.pdf', { type: 'application/pdf' }),
      ];

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files },
      });

      await waitFor(() => {
        expect(api.upload.uploadFile).toHaveBeenCalledTimes(2);
      });

      await waitFor(() => {
        const completeMessages = screen.getAllByText(/✓ Complete/i);
        expect(completeMessages).toHaveLength(2);
      });

      expect(mockOnUploadComplete).toHaveBeenCalledWith({
        total: 2,
        successful: 2,
        failed: 0,
      });
    });

    it('should track upload progress', async () => {
      let progressCallback;
      api.upload.uploadFile.mockImplementation((file, onProgress) => {
        progressCallback = onProgress;
        return new Promise((resolve) => {
          setTimeout(() => resolve({ success: true, filename: file.name }), 100);
        });
      });

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(progressCallback).toBeDefined();
      });

      // Simulate progress updates
      progressCallback(25);
      await waitFor(() => {
        expect(screen.getByText('25%')).toBeInTheDocument();
      });

      progressCallback(75);
      await waitFor(() => {
        expect(screen.getByText('75%')).toBeInTheDocument();
      });
    });

    it('should handle upload failure gracefully', async () => {
      api.upload.uploadFile.mockRejectedValue(new Error('Network error'));

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/✗ Network error/i)).toBeInTheDocument();
      });

      expect(mockOnUploadComplete).toHaveBeenCalledWith({
        total: 1,
        successful: 0,
        failed: 1,
      });
    });

    it('should handle registration failure', async () => {
      mockRegisterUploadBatch.mockRejectedValue(new Error('Server error'));

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/Server error/i)).toBeInTheDocument();
      });

      // Should not attempt to upload
      expect(api.upload.uploadFile).not.toHaveBeenCalled();
    });

    it('should auto-hide modal after successful upload', async () => {
      vi.useFakeTimers();

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/✓ Complete/i)).toBeInTheDocument();
      });

      // Fast-forward 500ms
      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });

    it('should not auto-hide modal if upload failed', async () => {
      vi.useFakeTimers();

      api.upload.uploadFile.mockRejectedValue(new Error('Upload failed'));

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/✗ Upload failed/i)).toBeInTheDocument();
      });

      // Fast-forward 500ms
      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      // Modal should still be visible
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      vi.useRealTimers();
    });
  });

  describe('File Input Selection', () => {
    it('should handle file selection via file input', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      fireEvent.dragEnter(document.body);

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText(/select files to upload/i);

      await userEvent.upload(input, file);

      await waitFor(() => {
        expect(mockRegisterUploadBatch).toHaveBeenCalledWith([file]);
      });
    });

    it('should reset file input after selection', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      fireEvent.dragEnter(document.body);

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText(/select files to upload/i);

      await userEvent.upload(input, file);

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });
  });

  describe('Duplicate File Handling', () => {
    it('should show duplicate warning when file exists', async () => {
      mockRegisterUploadBatch.mockResolvedValue([
        {
          filename: 'existing.pdf',
          doc_id: 'doc-123',
          is_duplicate: true,
          existing_doc: { doc_id: 'doc-existing', title: 'existing.pdf' },
        },
      ]);

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'existing.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/This file appears to be in the library already/i)).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /✕ Cancel Upload/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /✓ Continue Upload/i })).toBeInTheDocument();
    });

    it('should cancel duplicate upload when user clicks Cancel', async () => {
      mockRegisterUploadBatch.mockResolvedValue([
        {
          filename: 'existing.pdf',
          doc_id: 'doc-123',
          is_duplicate: true,
          existing_doc: { doc_id: 'doc-existing', title: 'existing.pdf' },
        },
      ]);

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'existing.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /✕ Cancel Upload/i })).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /✕ Cancel Upload/i });
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.getByText(/✗ Cancelled \(duplicate\)/i)).toBeInTheDocument();
      });

      // Should not upload
      expect(api.upload.uploadFile).not.toHaveBeenCalled();
    });

    it('should continue duplicate upload when user clicks Continue', async () => {
      mockRegisterUploadBatch.mockResolvedValue([
        {
          filename: 'existing.pdf',
          doc_id: 'doc-123',
          is_duplicate: true,
          existing_doc: { doc_id: 'doc-existing', title: 'existing.pdf' },
        },
      ]);

      // On second call (force upload), return non-duplicate registration
      mockRegisterUploadBatch.mockResolvedValueOnce([
        {
          filename: 'existing.pdf',
          doc_id: 'doc-123',
          is_duplicate: true,
          existing_doc: { doc_id: 'doc-existing', title: 'existing.pdf' },
        },
      ]).mockResolvedValueOnce([
        {
          filename: 'existing.pdf',
          doc_id: 'doc-456',
          is_duplicate: false,
        },
      ]);

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'existing.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /✓ Continue Upload/i })).toBeInTheDocument();
      });

      const continueButton = screen.getByRole('button', { name: /✓ Continue Upload/i });
      fireEvent.click(continueButton);

      await waitFor(() => {
        expect(api.upload.uploadFile).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByText(/✓ Complete/i)).toBeInTheDocument();
      });
    });
  });

  describe('WebSocket Connection', () => {
    it('should wait for WebSocket connection before uploading', async () => {
      const { rerender } = render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={false}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const event = new CustomEvent('manualUpload', {
        detail: { files: [file] },
      });

      window.dispatchEvent(event);

      await waitFor(() => {
        expect(screen.getByText(/Connecting to server/i)).toBeInTheDocument();
      });

      // Should not upload yet
      expect(mockRegisterUploadBatch).not.toHaveBeenCalled();

      // Simulate WebSocket connection
      rerender(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      await waitFor(() => {
        expect(mockRegisterUploadBatch).toHaveBeenCalledWith([file]);
      });
    });
  });

  describe('Store Integration', () => {
    it('should add temp document to store on registration', async () => {
      const mockAddTempDocument = vi.fn();
      useDocumentStore.mockImplementation((selector) => {
        const store = {
          addTempDocument: mockAddTempDocument,
          updateTempDocumentProgress: vi.fn(),
          setTempDocumentStatus: vi.fn(),
          clearAllTempDocuments: vi.fn(),
        };
        return typeof selector === 'function' ? selector(store) : store;
      });

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(mockAddTempDocument).toHaveBeenCalledWith('doc-123', 'test.pdf');
      });
    });

    it('should clear temp documents when forcing duplicate upload', async () => {
      const mockClearAllTempDocuments = vi.fn();
      useDocumentStore.mockImplementation((selector) => {
        const store = {
          addTempDocument: vi.fn(),
          updateTempDocumentProgress: vi.fn(),
          setTempDocumentStatus: vi.fn(),
          clearAllTempDocuments: mockClearAllTempDocuments,
        };
        return typeof selector === 'function' ? selector(store) : store;
      });

      mockRegisterUploadBatch
        .mockResolvedValueOnce([
          {
            filename: 'existing.pdf',
            doc_id: 'doc-123',
            is_duplicate: true,
            existing_doc: { doc_id: 'doc-existing' },
          },
        ])
        .mockResolvedValueOnce([
          {
            filename: 'existing.pdf',
            doc_id: 'doc-456',
            is_duplicate: false,
          },
        ]);

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'existing.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /✓ Continue Upload/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /✓ Continue Upload/i }));

      await waitFor(() => {
        expect(mockClearAllTempDocuments).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      fireEvent.dragEnter(document.body);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'upload-modal-title');
    });

    it('should have accessible file input label', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      fireEvent.dragEnter(document.body);

      const input = screen.getByLabelText(/select files to upload/i);
      expect(input).toBeInTheDocument();
    });

    it('should have accessible cancel button label', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      fireEvent.dragEnter(document.body);

      const cancelButton = screen.getByRole('button', { name: /cancel upload/i });
      expect(cancelButton).toBeInTheDocument();
    });

    it('should disable cancel button during upload', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        const uploadingButton = screen.getByRole('button', { name: /uploading/i });
        expect(uploadingButton).toBeDisabled();
      });
    });
  });

  describe('Drag and Drop', () => {
    it('should handle dragover event', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      const dragOverEvent = new Event('dragover', { bubbles: true, cancelable: true });
      document.body.dispatchEvent(dragOverEvent);

      expect(dragOverEvent.defaultPrevented).toBe(true);
    });

    it('should handle drop event on drop zone', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      fireEvent.dragEnter(document.body);

      const dropZone = document.querySelector('.upload-modal__drop-zone');
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.drop(dropZone, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(mockRegisterUploadBatch).toHaveBeenCalledWith([file]);
      });
    });

    it('should prevent default on drop zone dragover', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      fireEvent.dragEnter(document.body);

      const dropZone = document.querySelector('.upload-modal__drop-zone');
      const dragOverEvent = new Event('dragover', { bubbles: true, cancelable: true });

      dropZone.dispatchEvent(dragOverEvent);

      expect(dragOverEvent.defaultPrevented).toBe(true);
    });
  });

  describe('Mixed Upload Scenarios', () => {
    it('should handle mix of valid and invalid files', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      mockRegisterUploadBatch.mockResolvedValue([
        { filename: 'valid.pdf', doc_id: 'doc-123', is_duplicate: false },
      ]);

      const files = [
        new File(['content'], 'valid.pdf', { type: 'application/pdf' }),
        new File(['content'], 'invalid.exe', { type: 'application/x-msdownload' }),
      ];

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files },
      });

      await waitFor(() => {
        expect(screen.getByText(/Unsupported file type: .exe/i)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(api.upload.uploadFile).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle partial upload failures', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      mockRegisterUploadBatch.mockResolvedValue([
        { filename: 'file1.pdf', doc_id: 'doc-123', is_duplicate: false },
        { filename: 'file2.pdf', doc_id: 'doc-456', is_duplicate: false },
      ]);

      api.upload.uploadFile
        .mockResolvedValueOnce({ success: true, filename: 'file1.pdf' })
        .mockRejectedValueOnce(new Error('Network error'));

      const files = [
        new File(['content1'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['content2'], 'file2.pdf', { type: 'application/pdf' }),
      ];

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files },
      });

      await waitFor(() => {
        expect(screen.getByText(/✓ Complete/i)).toBeInTheDocument();
        expect(screen.getByText(/✗ Network error/i)).toBeInTheDocument();
      });

      expect(mockOnUploadComplete).toHaveBeenCalledWith({
        total: 2,
        successful: 1,
        failed: 1,
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty file drop', async () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [] },
      });

      // Should not call registerUploadBatch
      await new Promise((resolve) => setTimeout(resolve, 100));
      expect(mockRegisterUploadBatch).not.toHaveBeenCalled();
    });

    it('should handle rapid drag enter/leave events', () => {
      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
        />
      );

      // Rapid drag enter/leave
      fireEvent.dragEnter(document.body);
      fireEvent.dragLeave(document.body);
      fireEvent.dragEnter(document.body);

      // Modal should still be visible
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should reset file map after successful upload', async () => {
      vi.useFakeTimers();

      render(
        <UploadModal
          registerUploadBatch={mockRegisterUploadBatch}
          isWebSocketConnected={true}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText(/✓ Complete/i)).toBeInTheDocument();
      });

      // Fast-forward to auto-hide
      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      // Upload same file again - should work
      fireEvent.dragEnter(document.body);
      fireEvent.drop(document.body, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(mockRegisterUploadBatch).toHaveBeenCalledTimes(2);
      });

      vi.useRealTimers();
    });
  });
});
