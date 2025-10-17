/**
 * UploadModal - Drag-drop upload interface
 *
 * Provides global drag-over detection, lightbox modal display,
 * file validation, and upload to Copyparty API.
 *
 * Provider: upload-agent (Wave 1)
 * Contract: integration-contracts/upload-modal.contract.md
 */

/**
 * Upload Modal Component
 * Emits uploadStart, uploadProgress, uploadComplete, uploadError, uploadBatchComplete events
 */
export class UploadModal {
  /**
   * Create upload modal
   * @param {Object} options - Configuration options
   * @param {string} [options.copypartyUrl='http://localhost:8000'] - Copyparty base URL
   * @param {string} [options.uploadPath='/uploads'] - Upload endpoint path
   * @param {Array} [options.supportedTypes] - Allowed file extensions
   * @param {number} [options.maxFileSize=104857600] - Max file size in bytes (default: 100MB)
   */
  constructor(options = {}) {
    this.copypartyUrl = options.copypartyUrl || 'http://localhost:8000';
    this.uploadPath = options.uploadPath || '/uploads';
    // Must match file_validator.py DEFAULT_FORMATS
    this.supportedTypes = options.supportedTypes || [
      '.pdf', '.docx', '.doc', '.pptx', '.ppt',
      '.xlsx', '.xls', '.html', '.xhtml', '.md', '.asciidoc', '.csv',
      '.mp3', '.wav', '.flac', '.m4a', '.vtt',
      '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp'
    ];
    this.maxFileSize = options.maxFileSize || 100 * 1024 * 1024; // 100MB
    this.auth = options.auth || { username: 'admin', password: 'admin' };

    this.modal = null;
    this.dragCounter = 0;
  }

  /**
   * Initialize modal
   */
  init() {
    this.createModal();
    this.attachGlobalListeners();
  }

  /**
   * Create modal DOM element
   */
  createModal() {
    this.modal = document.createElement('div');
    this.modal.className = 'upload-modal';
    this.modal.setAttribute('role', 'dialog');
    this.modal.setAttribute('aria-modal', 'true');
    this.modal.setAttribute('aria-labelledby', 'upload-modal-title');
    this.modal.style.display = 'none';

    this.modal.innerHTML = `
      <div class="upload-modal__backdrop"></div>
      <div class="upload-modal__container">
        <div class="upload-modal__content">
          <h2 id="upload-modal-title" class="upload-modal__title">Drop files to upload</h2>

          <div class="upload-modal__drop-zone">
            <svg class="upload-modal__icon" xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <p class="upload-modal__message">Drop your documents here</p>
            <p class="upload-modal__hint">or</p>

            <!-- Keyboard-accessible file input -->
            <input
              type="file"
              id="upload-modal-file-input"
              class="upload-modal__file-input"
              multiple
              accept=".pdf,.docx,.doc,.pptx,.ppt,.mp3,.wav,.flac,.m4a"
              aria-label="Select files to upload"
            />
            <label for="upload-modal-file-input" class="upload-modal__file-button">
              Choose Files
            </label>

            <p class="upload-modal__hint">Supported: PDF, DOCX, PPTX, MP3, WAV (max 100MB)</p>
          </div>

          <div class="upload-modal__progress" style="display: none;">
            <div class="upload-modal__progress-list" id="progress-list"></div>
          </div>

          <button class="upload-modal__close" aria-label="Cancel upload">Cancel</button>
        </div>
      </div>
    `;

    document.body.appendChild(this.modal);

    // Close button
    this.modal.querySelector('.upload-modal__close').addEventListener('click', () => {
      this.hide();
    });

    // Drop zone
    const dropZone = this.modal.querySelector('.upload-modal__drop-zone');
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.handleDrop(e);
    });
    // File input change handler for keyboard accessibility
    const fileInput = this.modal.querySelector('#upload-modal-file-input');
    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const files = Array.from(e.target.files);
        if (files.length > 0) {
          this.handleDrop({ dataTransfer: { files } });
          // Clear the input so the same file can be selected again
          fileInput.value = '';
        }
      });
    }

  }

  /**
   * Attach global drag listeners
   */
  attachGlobalListeners() {
    document.body.addEventListener('dragenter', (e) => {
      e.preventDefault();
      this.dragCounter++;

      if (this.dragCounter === 1) {
        this.show();
      }
    });

    document.body.addEventListener('dragleave', (e) => {
      e.preventDefault();
      this.dragCounter--;

      if (this.dragCounter === 0) {
        // Small delay to prevent flicker
        setTimeout(() => {
          if (this.dragCounter === 0) {
            this.hide();
          }
        }, 100);
      }
    });

    document.body.addEventListener('dragover', (e) => {
      e.preventDefault();
    });

    document.body.addEventListener('drop', (e) => {
      e.preventDefault();
      this.dragCounter = 0;
    });
  }

  /**
   * Show modal
   */
  show() {
    if (this.modal) {
      this.modal.style.display = 'flex';
    }
  }

  /**
   * Hide modal
   */
  hide() {
    if (this.modal) {
      this.modal.style.display = 'none';

      // Reset progress display
      const progressSection = this.modal.querySelector('.upload-modal__progress');
      const dropZone = this.modal.querySelector('.upload-modal__drop-zone');
      const progressList = this.modal.querySelector('.upload-modal__progress-list');

      progressSection.style.display = 'none';
      dropZone.style.display = 'block';

      // Clear progress items
      progressList.innerHTML = '';
    }
  }

  /**
   * Handle file drop
   * @param {DragEvent} e - Drop event
   */
  async handleDrop(e) {
    const files = Array.from(e.dataTransfer.files);

    if (files.length === 0) {
      return;
    }

    // Show progress section
    const progressSection = this.modal.querySelector('.upload-modal__progress');
    const dropZone = this.modal.querySelector('.upload-modal__drop-zone');
    dropZone.style.display = 'none';
    progressSection.style.display = 'block';

    // Upload files
    await this.uploadFiles(files);
  }

  /**
   * Upload files
   * @param {Array<File>} files - Files to upload
   */
  async uploadFiles(files) {
    const results = { successful: 0, failed: 0, total: files.length };
    const progressList = this.modal.querySelector('.upload-modal__progress-list');

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Validate file
      const validation = this.validateFile(file);
      if (!validation.valid) {
        this.emitUploadError(file.name, validation.error, validation.code);
        results.failed++;
        continue;
      }

      // Add progress item to UI
      const progressItem = this.createProgressItem(file.name);
      progressList.appendChild(progressItem);

      // Emit start event
      this.emitUploadStart(file.name, file.size, i, files.length);

      try {
        // Upload file
        const response = await this.uploadFile(file, (progress) => {
          const percentage = progress.loaded / progress.total;
          this.updateProgressItem(progressItem, percentage);
          this.emitUploadProgress(file.name, percentage, progress.loaded, progress.total);
        });

        // Mark as complete
        this.completeProgressItem(progressItem);

        // Emit complete event
        this.emitUploadComplete(file.name, response.path || `/uploads/${file.name}`, file.size, response);
        results.successful++;

      } catch (error) {
        // Mark as failed
        this.failProgressItem(progressItem, error.message);
        this.emitUploadError(file.name, error.message, 'UPLOAD_FAILED');
        results.failed++;
      }
    }

    // Emit batch complete
    this.emitUploadBatchComplete(results.total, results.successful, results.failed);

    // Auto-hide after 2 seconds if successful
    if (results.failed === 0) {
      setTimeout(() => {
        this.hide();
      }, 2000);
    }
  }

  /**
   * Create progress item element
   * @param {string} filename - File name
   * @returns {HTMLElement} Progress item element
   */
  createProgressItem(filename) {
    const item = document.createElement('div');
    item.className = 'upload-modal__progress-item';
    item.innerHTML = `
      <div class="upload-modal__progress-filename">${filename}</div>
      <div class="upload-modal__progress-bar">
        <div class="upload-modal__progress-fill" style="width: 0%"></div>
      </div>
      <div class="upload-modal__progress-status">Uploading...</div>
    `;
    return item;
  }

  /**
   * Update progress item
   * @param {HTMLElement} item - Progress item element
   * @param {number} percentage - Progress percentage (0-1)
   */
  updateProgressItem(item, percentage) {
    const fill = item.querySelector('.upload-modal__progress-fill');
    const status = item.querySelector('.upload-modal__progress-status');
    fill.style.width = `${Math.round(percentage * 100)}%`;
    status.textContent = `${Math.round(percentage * 100)}%`;
  }

  /**
   * Mark progress item as complete
   * @param {HTMLElement} item - Progress item element
   */
  completeProgressItem(item) {
    const fill = item.querySelector('.upload-modal__progress-fill');
    const status = item.querySelector('.upload-modal__progress-status');
    fill.style.width = '100%';
    status.textContent = '✓ Complete';
    status.style.color = '#10b981';
    item.classList.add('upload-modal__progress-item--complete');
  }

  /**
   * Mark progress item as failed
   * @param {HTMLElement} item - Progress item element
   * @param {string} error - Error message
   */
  failProgressItem(item, error) {
    const fill = item.querySelector('.upload-modal__progress-fill');
    const status = item.querySelector('.upload-modal__progress-status');
    fill.style.width = '100%';
    fill.style.backgroundColor = '#ef4444';
    status.textContent = `✗ ${error}`;
    status.style.color = '#ef4444';
    item.classList.add('upload-modal__progress-item--failed');
  }

  /**
   * Validate file
   * @param {File} file - File to validate
   * @returns {Object} Validation result
   */
  validateFile(file) {
    // Check extension
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!this.supportedTypes.includes(ext)) {
      return {
        valid: false,
        error: `Unsupported file type: ${ext}`,
        code: 'UNSUPPORTED_TYPE'
      };
    }

    // Check size
    if (file.size > this.maxFileSize) {
      const maxMB = Math.round(this.maxFileSize / 1024 / 1024);
      return {
        valid: false,
        error: `File exceeds maximum size of ${maxMB}MB`,
        code: 'FILE_TOO_LARGE'
      };
    }

    return { valid: true };
  }

  /**
   * Upload single file
   * @param {File} file - File to upload
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>} Upload response
   */
  uploadFile(file, onProgress) {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      // Copyparty expects "act=bput" for basic PUT uploads
      formData.append('act', 'bput');
      formData.append('f', file);

      const xhr = new XMLHttpRequest();

      // Progress tracking
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress({ loaded: e.loaded, total: e.total });
        }
      });

      // Load handler
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch {
            resolve({ status: 'ok' });
          }
        } else {
          reject(new Error(`Upload failed: HTTP ${xhr.status}`));
        }
      });

      // Error handler
      xhr.addEventListener('error', () => {
        reject(new Error('Network error'));
      });

      xhr.open('POST', `${this.copypartyUrl}${this.uploadPath}`);

      // Add HTTP Basic Authentication if configured
      if (this.auth) {
        const credentials = btoa(`${this.auth.username}:${this.auth.password}`);
        xhr.setRequestHeader('Authorization', `Basic ${credentials}`);
      }

      xhr.send(formData);
    });
  }

  // Event emission methods

  emitUploadStart(filename, size, index, total) {
    const event = new CustomEvent('uploadStart', {
      detail: { filename, size, index, total },
      bubbles: true
    });
    document.dispatchEvent(event);
  }

  emitUploadProgress(filename, progress, loaded, total) {
    const event = new CustomEvent('uploadProgress', {
      detail: { filename, progress, loaded, total },
      bubbles: true
    });
    document.dispatchEvent(event);
  }

  emitUploadComplete(filename, file_path, size, response) {
    const event = new CustomEvent('uploadComplete', {
      detail: { filename, file_path, size, response },
      bubbles: true
    });
    document.dispatchEvent(event);
  }

  emitUploadError(filename, error, code) {
    const event = new CustomEvent('uploadError', {
      detail: { filename, error, code },
      bubbles: true
    });
    document.dispatchEvent(event);
    console.error(`Upload error (${filename}):`, error);
  }

  emitUploadBatchComplete(total, successful, failed) {
    const event = new CustomEvent('uploadBatchComplete', {
      detail: { total, successful, failed },
      bubbles: true
    });
    document.dispatchEvent(event);
  }

  /**
   * Destroy modal
   */
  destroy() {
    if (this.modal && this.modal.parentNode) {
      this.modal.parentNode.removeChild(this.modal);
    }
  }
}
