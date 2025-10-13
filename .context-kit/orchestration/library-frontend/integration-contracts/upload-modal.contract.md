# Upload Modal Contract

**Provider**: `upload-modal.js` (Agent 5)
**Consumer**: `library-manager.js` (Agent 2)
**External Integration**: Copyparty API (localhost:8000)

---

## Module Interface

### **Export**

```javascript
export class UploadModal;
```

---

## Class: UploadModal

### **Constructor**

```javascript
constructor(options = {})
```

**Options**:

| Field              | Type   | Default                      | Description                          |
|--------------------|--------|------------------------------|--------------------------------------|
| `copypartyUrl`     | string | `'http://localhost:8000'`    | Copyparty base URL                   |
| `uploadPath`       | string | `'/uploads'`                 | Upload endpoint path                 |
| `supportedTypes`   | array  | See below                    | Allowed file extensions              |
| `maxFileSize`      | number | `100 * 1024 * 1024` (100MB)  | Max file size in bytes               |

**Default Supported Types**:
```javascript
['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.mp3', '.wav', '.flac', '.m4a']
```

---

## Public Methods

### **Method: init()**

```javascript
init()
```

**Purpose**: Initialize modal, attach global drag listeners

**Side Effects**:
- Attaches `dragenter` and `dragover` listeners to `document.body`
- Creates modal DOM element and appends to body
- Sets initial state to hidden

---

### **Method: show()**

```javascript
show()
```

**Purpose**: Display the modal

**Behavior**:
- Adds visible class to modal
- Traps focus within modal
- Prevents body scroll

---

### **Method: hide()**

```javascript
hide()
```

**Purpose**: Hide the modal

**Behavior**:
- Removes visible class
- Restores focus to previous element
- Re-enables body scroll

---

### **Method: destroy()**

```javascript
destroy()
```

**Purpose**: Clean up resources

**Behavior**:
- Removes event listeners
- Removes modal from DOM

---

## Events Emitted

### **Event 1: uploadStart**

**Dispatched When**: Upload begins for a file

**Event Detail**:
```javascript
{
  filename: string,      // Original filename
  size: number,          // File size in bytes
  index: number,         // File index in batch (0-based)
  total: number          // Total files in batch
}
```

**Example**:
```javascript
{
  filename: 'report.pdf',
  size: 2456789,
  index: 0,
  total: 3
}
```

---

### **Event 2: uploadProgress**

**Dispatched When**: Upload progress changes (throttled to every 100ms)

**Event Detail**:
```javascript
{
  filename: string,      // Original filename
  progress: number,      // Upload progress 0.0-1.0
  loaded: number,        // Bytes uploaded
  total: number          // Total bytes
}
```

**Example**:
```javascript
{
  filename: 'report.pdf',
  progress: 0.45,
  loaded: 1105555,
  total: 2456789
}
```

---

### **Event 3: uploadComplete**

**Dispatched When**: File upload completes successfully

**Event Detail**:
```javascript
{
  filename: string,      // Original filename
  file_path: string,     // Server path to uploaded file
  size: number,          // File size in bytes
  response: object       // Copyparty response (if available)
}
```

**Example**:
```javascript
{
  filename: 'report.pdf',
  file_path: '/uploads/report.pdf',
  size: 2456789,
  response: { status: 'ok', url: '/uploads/report.pdf' }
}
```

**Consumer Action**:
LibraryManager should:
1. Create a loading card for this document
2. Add to grid (at top)
3. WebSocket will send processing updates

---

### **Event 4: uploadError**

**Dispatched When**: Upload fails

**Event Detail**:
```javascript
{
  filename: string,      // Original filename
  error: string,         // Error message
  code: string           // Error code
}
```

**Error Codes**:
- `'FILE_TOO_LARGE'` - Exceeds max size
- `'UNSUPPORTED_TYPE'` - File type not allowed
- `'UPLOAD_FAILED'` - Network/server error

**Example**:
```javascript
{
  filename: 'huge-file.pdf',
  error: 'File exceeds maximum size of 100MB',
  code: 'FILE_TOO_LARGE'
}
```

---

### **Event 5: uploadBatchComplete**

**Dispatched When**: All files in batch finish (success or error)

**Event Detail**:
```javascript
{
  total: number,         // Total files
  successful: number,    // Files uploaded successfully
  failed: number         // Files that failed
}
```

**Example**:
```javascript
{
  total: 5,
  successful: 4,
  failed: 1
}
```

---

## Copyparty Integration

### **Upload Endpoint**

```http
POST http://localhost:8000/uploads
Content-Type: multipart/form-data

file: [binary data]
```

**Response** (Success):
```json
{
  "status": "ok",
  "url": "/uploads/report.pdf",
  "path": "/path/to/uploads/report.pdf"
}
```

**Response** (Error):
```json
{
  "error": "Upload failed",
  "details": "..."
}
```

---

### **Upload Implementation**

```javascript
async uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const xhr = new XMLHttpRequest();

  // Progress tracking
  xhr.upload.addEventListener('progress', (e) => {
    if (e.lengthComputable) {
      this.emitUploadProgress(file.name, e.loaded / e.total, e.loaded, e.total);
    }
  });

  // Upload
  return new Promise((resolve, reject) => {
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const response = JSON.parse(xhr.responseText);
        resolve(response);
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error'));
    });

    xhr.open('POST', `${this.copypartyUrl}${this.uploadPath}`);
    xhr.send(formData);
  });
}
```

---

## File Validation

### **Validation Rules**

1. **File Extension**
   - Must be in `supportedTypes` array
   - Case-insensitive check
   - Error: `UNSUPPORTED_TYPE`

2. **File Size**
   - Must be ≤ `maxFileSize`
   - Default: 100MB
   - Error: `FILE_TOO_LARGE`

3. **File Name**
   - Should sanitize: remove special characters, path traversal
   - Warn on duplicate names (optional)

---

### **Validation Implementation**

```javascript
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
```

---

## Modal UI Structure

### **HTML Structure**

```html
<div class="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-modal-title">
  <div class="upload-modal__backdrop"></div>
  <div class="upload-modal__container">
    <div class="upload-modal__content">
      <h2 id="upload-modal-title" class="upload-modal__title">Drop files to upload</h2>

      <div class="upload-modal__drop-zone">
        <svg class="upload-modal__icon" aria-hidden="true">
          <!-- Upload icon -->
        </svg>
        <p class="upload-modal__message">Drop your documents here</p>
        <p class="upload-modal__hint">Supported: PDF, DOCX, PPTX, MP3, WAV (max 100MB)</p>
      </div>

      <div class="upload-modal__progress" hidden>
        <div class="upload-modal__progress-list">
          <!-- Dynamic progress items -->
        </div>
      </div>

      <button class="upload-modal__close" aria-label="Cancel upload">Cancel</button>
    </div>
  </div>
</div>
```

---

### **States**

1. **Idle** (waiting for drop)
   - Show drop zone
   - Hide progress list

2. **Uploading**
   - Show progress list
   - Show progress bars for each file
   - Disable close button or show "Cancel" with confirmation

3. **Complete**
   - Show success message
   - Auto-hide after 2 seconds

4. **Error**
   - Show error message(s)
   - Allow retry or close

---

## LibraryManager Integration (Consumer)

### **Initialization**

```javascript
class LibraryManager {
  constructor() {
    this.uploadModal = new UploadModal({
      copypartyUrl: 'http://localhost:8000',
      uploadPath: '/uploads'
    });
    this.uploadModal.init();
    this.attachUploadListeners();
  }

  attachUploadListeners() {
    document.addEventListener('uploadComplete', (event) => {
      this.handleUploadComplete(event.detail);
    });

    document.addEventListener('uploadError', (event) => {
      this.handleUploadError(event.detail);
    });

    document.addEventListener('uploadBatchComplete', (event) => {
      this.handleBatchComplete(event.detail);
    });
  }

  handleUploadComplete(detail) {
    const { filename, file_path } = detail;

    // Create loading card
    const card = createDocumentCard({
      filename,
      thumbnailUrl: '',
      dateAdded: new Date(),
      detailsUrl: '#',
      state: 'loading'
    });

    // Add to grid (at top)
    this.documentGrid.prepend(card);

    // Generate temporary doc_id (will be replaced by WebSocket)
    const tempId = `temp_${Date.now()}`;
    this.documentCards.set(tempId, card);

    // WebSocket will send processing updates with real doc_id
    // LibraryManager will replace temp card when processing starts
  }

  handleUploadError(detail) {
    const { filename, error } = detail;
    // Show toast or inline error (but user said no toasts!)
    // Log to console instead
    console.error(`Upload failed: ${filename} - ${error}`);
  }

  handleBatchComplete(detail) {
    const { successful, failed } = detail;
    console.log(`Upload batch complete: ${successful} successful, ${failed} failed`);
  }
}
```

---

## Testing Requirements

### **Provider Validation** (Agent 5)
- [ ] Modal shows on drag-over
- [ ] Modal hides on drag-leave (after delay)
- [ ] File validation works (extension, size)
- [ ] Upload progress tracking works
- [ ] Multi-file upload works
- [ ] Events emitted with correct detail
- [ ] Error handling works (network, validation)
- [ ] Modal focus trap works
- [ ] Keyboard navigation (ESC to close)

### **Consumer Validation** (Agent 2)
- [ ] LibraryManager receives upload events
- [ ] Loading cards created on uploadComplete
- [ ] Cards added to grid (at top)
- [ ] WebSocket updates picked up correctly
- [ ] Temp cards replaced with real cards

---

## Accessibility Requirements

- Modal has `role="dialog"` and `aria-modal="true"`
- Modal title has unique ID referenced by `aria-labelledby`
- Focus trapped within modal when visible
- ESC key closes modal
- Close button has `aria-label`
- Progress bars have `role="progressbar"` with `aria-valuenow`

---

## Example Full Flow

```javascript
// 1. User drags file over page
//    → UploadModal detects dragenter
//    → Modal shows

// 2. User drops 3 files
//    → UploadModal validates each file
//    → Emits uploadStart for each

document.addEventListener('uploadStart', (e) => {
  console.log(`Starting upload: ${e.detail.filename} (${e.detail.index + 1}/${e.detail.total})`);
});

// 3. Upload progresses
document.addEventListener('uploadProgress', (e) => {
  console.log(`${e.detail.filename}: ${Math.round(e.detail.progress * 100)}%`);
});

// 4. Upload completes
document.addEventListener('uploadComplete', (e) => {
  // LibraryManager creates loading card
  const card = createDocumentCard({
    filename: e.detail.filename,
    state: 'loading'
  });
  grid.prepend(card);
});

// 5. All files finish
document.addEventListener('uploadBatchComplete', (e) => {
  console.log(`Batch complete: ${e.detail.successful}/${e.detail.total} successful`);
  // Modal auto-hides after 2s
});

// 6. Copyparty webhook triggers worker
//    → Worker processes document
//    → WebSocket sends status updates
//    → LibraryManager updates cards
```

---

## Change Log

- 2025-10-13: Initial contract specification
- Note: User prefers no toast notifications
- Status: **DRAFT** (to be implemented in Wave 1)
