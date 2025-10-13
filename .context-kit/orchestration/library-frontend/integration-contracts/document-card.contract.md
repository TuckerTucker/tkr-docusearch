# DocumentCard Component Contract

**Provider**: `document-card.js` (Agent 3)
**Consumers**: `library-manager.js` (Agent 2)
**Status**: New implementation (migrated from POC)

---

## Module Interface

### **Exports**

```javascript
export function createDocumentCard(options);
export function updateCardState(card, status);
export const Icons; // Icon name mappings
```

---

## Function 1: createDocumentCard

### **Signature**

```javascript
/**
 * Create a DocumentCard element
 *
 * @param {Object} options - Card configuration
 * @returns {HTMLElement} DocumentCard element
 */
function createDocumentCard(options)
```

---

### **Parameters**

**`options` Object**:

| Field               | Type          | Required | Default         | Description                          |
|---------------------|---------------|----------|-----------------|--------------------------------------|
| `filename`          | string        | Yes      | -               | Full filename with extension         |
| `thumbnailUrl`      | string        | Yes      | -               | URL to thumbnail image               |
| `dateAdded`         | string\|Date  | Yes      | -               | Date added (ISO or Date object)      |
| `detailsUrl`        | string        | Yes      | -               | URL for details button/link          |
| `variant`           | string        | No       | auto-detect     | 'document' or 'audio'                |
| `placeholderColor`  | string        | No       | '#E9E9E9'       | Background for missing images        |
| `state`             | string        | No       | 'completed'     | Card state (see below)               |
| `processingStatus`  | object        | No       | null            | Processing status (required if processing) |

**State Values**:
- `'completed'` - Document fully processed, shows active details button
- `'loading'` - Document being loaded, shows spinner, disabled button
- `'processing'` - Document being processed, shows progress bar, disabled button

**Processing Status Object** (required when `state === 'processing'`):
```javascript
{
  stage: string,    // Current stage (e.g., "Embedding images")
  progress: number  // Progress 0.0-1.0
}
```

**Variant Auto-Detection**:
- Based on file extension
- `pdf`, `docx`, `pptx`, `xlsx`, `txt`, `md`, `html` → `'document'` (tall)
- `mp3`, `wav`, `flac`, `m4a`, `mp4`, `avi`, `mov` → `'audio'` (square)

---

### **Return Value**

**HTMLElement** with:
- Class: `document-card document-card--{variant} [document-card--{state}]`
- Role: `article`
- ARIA label: `"Document: {filename}"`

**DOM Structure**:
```html
<article class="document-card document-card--document" role="article" aria-label="Document: report.pdf">
  <div class="document-card__left">
    <img class="document-card__thumbnail" src="..." alt="Thumbnail for report.pdf">
    <div class="document-card__badge" aria-label="Added October 12, File type: PDF">
      <div class="document-card__badge-filetype">
        <div class="document-card__badge-icon-container">
          <i class="document-card__badge-icon" data-lucide="file-text"></i>
          <div class="document-card__badge-extension">PDF</div>
        </div>
      </div>
      <div class="document-card__badge-date">Added<br>October 12</div>
    </div>
  </div>
  <div class="document-card__right">
    <!-- State-specific content here -->
  </div>
</article>
```

---

### **States and Right Column Content**

#### **Completed State**
```html
<div class="document-card__right">
  <h3 class="document-card__title">quarterly-report</h3>
  <a class="document-card__button" href="#details">Details</a>
</div>
```

#### **Loading State**
```html
<div class="document-card__right">
  <div class="document-card__processing-info">
    <div class="document-card__status">
      <div class="document-card__spinner" role="status" aria-label="Loading"></div>
      <div class="document-card__status-label">Loading document...</div>
    </div>
  </div>
  <button class="document-card__button" disabled>Details</button>
</div>
```

#### **Processing State**
```html
<div class="document-card__right">
  <div class="document-card__processing-info">
    <div class="document-card__status">
      <div class="document-card__spinner" role="status" aria-label="Processing"></div>
      <div class="document-card__status-label">Embedding images</div>
    </div>
    <div class="document-card__progress-container">
      <div class="document-card__progress" role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100">
        <div class="document-card__progress-bar" style="width: 45%"></div>
      </div>
      <div class="document-card__progress-text">45%</div>
    </div>
  </div>
  <button class="document-card__button" disabled>Details</button>
</div>
```

---

## Function 2: updateCardState

### **Signature**

```javascript
/**
 * Update an existing card's processing state
 *
 * @param {HTMLElement} card - The card element to update
 * @param {Object} status - Processing status
 */
function updateCardState(card, status)
```

---

### **Parameters**

**`card`**: HTMLElement
- Must be a card element created by `createDocumentCard()`

**`status`**: Object

| Field      | Type   | Required | Description                          |
|------------|--------|----------|--------------------------------------|
| `state`    | string | Yes      | 'loading', 'processing', 'completed' |
| `stage`    | string | No       | Current processing stage             |
| `progress` | number | No       | Progress 0.0-1.0                     |

---

### **Behavior**

**Updates**:
1. Removes previous state classes (`document-card--loading`, `document-card--processing`)
2. Adds new state class (if not 'completed')
3. Updates processing-specific elements:
   - `.document-card__status-label` - Stage text
   - `.document-card__progress-bar` - Width (%)
   - `.document-card__progress-text` - Percentage text
   - `.document-card__progress` - ARIA `aria-valuenow`

**State Transitions**:
- `loading` → `processing`: Updates spinner and adds progress bar
- `processing` → `processing`: Updates progress/stage
- `processing` → `completed`: Removes spinner/progress (partial - full rebuild recommended)

**Note**: Transitioning to `completed` state only removes processing classes. For full completed state (with active button), recommend recreating the card.

---

## Icons Export

### **Object Structure**

```javascript
export const Icons = {
  document: 'file-text',
  audio: 'volume-2',
  video: 'video'
};
```

**Purpose**: Maps icon types to Lucide icon names (for reference only, inline SVG used in implementation)

---

## CSS Classes Required

### **Card Container**
- `.document-card` - Base card styles
- `.document-card--document` - Tall variant (200×262px thumbnail)
- `.document-card--audio` - Square variant (200×200px thumbnail)
- `.document-card--loading` - Loading state styles
- `.document-card--processing` - Processing state styles

### **Card Components**
- `.document-card__left` - Left column (thumbnail + badge)
- `.document-card__right` - Right column (title + button/status)
- `.document-card__thumbnail` - Thumbnail image
- `.document-card__badge` - Metadata badge
- `.document-card__badge-filetype` - File type container
- `.document-card__badge-icon-container` - Icon + extension container
- `.document-card__badge-icon` - File type icon
- `.document-card__badge-extension` - Extension text
- `.document-card__badge-date` - Date added text
- `.document-card__title` - Document title (completed state)
- `.document-card__button` - Details button/link

### **Processing Elements**
- `.document-card__processing-info` - Container for status + progress
- `.document-card__status` - Status container (spinner + label)
- `.document-card__spinner` - Animated spinner
- `.document-card__status-label` - Stage text
- `.document-card__progress-container` - Progress bar + percentage wrapper
- `.document-card__progress` - Progress bar track
- `.document-card__progress-bar` - Progress bar fill
- `.document-card__progress-text` - Percentage text

---

## Consumer Implementation (LibraryManager)

### **Initial Card Creation**

```javascript
import { createDocumentCard } from './document-card.js';

// Create completed card (from API data)
const card = createDocumentCard({
  filename: 'quarterly-report.pdf',
  thumbnailUrl: '/images/abc123.../page001_thumb.jpg',
  dateAdded: new Date('2025-10-12T14:23:00'),
  detailsUrl: `/documents/${doc.doc_id}`,
  state: 'completed'
});

// Add to grid
this.documentGrid.appendChild(card);
this.documentCards.set(doc.doc_id, card);
```

---

### **Real-Time Updates (WebSocket)**

```javascript
import { updateCardState } from './document-card.js';

// WebSocket message: processing started
handleStatusUpdate(message) {
  const { doc_id, status, progress, stage, filename } = message;

  let card = this.documentCards.get(doc_id);

  if (!card && status === 'processing') {
    // Create new processing card
    card = createDocumentCard({
      filename,
      thumbnailUrl: '',
      dateAdded: new Date(),
      detailsUrl: '#',
      state: 'processing',
      processingStatus: { stage, progress }
    });
    this.documentCards.set(doc_id, card);
    this.documentGrid.prepend(card); // Add at top
  } else if (card && status === 'processing') {
    // Update existing card
    updateCardState(card, { state: 'processing', stage, progress });
  } else if (card && status === 'completed') {
    // Reload library to get full document data
    // OR: Update to completed state (partial support)
    updateCardState(card, { state: 'completed' });
    // Recommended: Fetch from API and replace card
    this.refreshDocument(doc_id);
  }
}
```

---

## Testing Requirements

### **Provider Validation** (Agent 3)
- [ ] `createDocumentCard()` returns valid HTMLElement
- [ ] Completed state shows active button
- [ ] Loading state shows spinner and disabled button
- [ ] Processing state shows progress bar
- [ ] Variant detection works for all file types
- [ ] `updateCardState()` updates progress correctly
- [ ] State transitions work (loading → processing → completed)
- [ ] Thumbnail error handling (missing images)
- [ ] Date formatting works (string and Date objects)

### **Consumer Validation** (Agent 2)
- [ ] Can create cards from API data
- [ ] Can create processing cards from WebSocket messages
- [ ] Can update cards on progress changes
- [ ] Cards render correctly in grid
- [ ] Accessibility attributes present (ARIA, roles)

---

## Example Usage

### **Example 1: Completed Document**
```javascript
const card = createDocumentCard({
  filename: 'report.pdf',
  thumbnailUrl: '/images/abc123/page001_thumb.jpg',
  dateAdded: '2025-10-12T14:23:00',
  detailsUrl: '/documents/abc123'
});
// Result: Card with thumbnail, metadata, active button
```

### **Example 2: Processing Document**
```javascript
const card = createDocumentCard({
  filename: 'presentation.pptx',
  thumbnailUrl: '',
  dateAdded: new Date(),
  detailsUrl: '#',
  state: 'processing',
  processingStatus: {
    stage: 'Embedding images',
    progress: 0.45
  }
});
// Result: Card with spinner, progress bar at 45%, disabled button
```

### **Example 3: Update Progress**
```javascript
updateCardState(card, {
  state: 'processing',
  stage: 'Storing vectors',
  progress: 0.95
});
// Result: Progress bar updates to 95%, stage label changes
```

---

## Dependencies

**None** - Pure component, no external dependencies

**Icon Strategy**:
- Remove Lucide dependency from POC
- Use inline SVG icons for file types
- Simpler, faster, no external library

---

## Change Log

- 2025-10-13: Initial contract based on POC implementation
- Removed Lucide dependency (use inline SVG)
- Added WebSocket integration examples
- Status: **DRAFT** (to be implemented in Wave 1)
