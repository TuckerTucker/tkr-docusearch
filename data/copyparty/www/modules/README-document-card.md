# DocumentCard Component

A reusable, accessible document information card component for displaying document metadata, thumbnails, and actions.

## Features

✓ **Two variants**: Document (tall 200×262) and Audio (square 200×200)
✓ **Auto-detection**: Automatically selects variant based on file extension
✓ **Three states**: Completed, Loading, and Processing with real-time updates
✓ **Loading states**: Animated skeleton loaders for thumbnail and badge
✓ **Processing states**: Live progress tracking with spinner, progress bar, and percentage
✓ **Responsive**: Adapts to mobile screens
✓ **Accessible**: ARIA labels, keyboard navigation, focus management, progressbar roles
✓ **Lucide icons**: Beautiful, consistent icons for documents, audio, and video files
✓ **Graceful degradation**: Placeholder backgrounds for missing thumbnails
✓ **Hover effects**: Smooth transitions and interactive states
✓ **WebSocket ready**: Easy integration with real-time status updates

## Files

- `document-card.js` - Component module
- `styles.css` - Component styles (lines 1042-1342)
- `document-card-demo.html` - Demo page with all states

## Dependencies

- **Lucide Icons** - Icon library for file type badges
  ```html
  <script src="https://unpkg.com/lucide@latest"></script>
  ```

## Usage

### Basic Example

```javascript
import { createDocumentCard } from './modules/document-card.js';

const card = createDocumentCard({
  filename: 'quarterly-report-q3-2023.pdf',
  thumbnailUrl: '/uploads/.page_images/report.pdf/page_1.png',
  dateAdded: new Date('2023-09-26'),
  detailsUrl: '/document/123'
});

document.querySelector('#container').appendChild(card);
```

### Loading State

```javascript
import { createDocumentCard } from './modules/document-card.js';

const card = createDocumentCard({
  filename: 'loading-document.pdf',
  thumbnailUrl: '',
  dateAdded: new Date(),
  detailsUrl: '/document/123',
  state: 'loading'  // Shows skeleton loaders and spinner
});

document.querySelector('#container').appendChild(card);
```

### Processing State

```javascript
import { createDocumentCard } from './modules/document-card.js';

const card = createDocumentCard({
  filename: 'processing-document.pdf',
  thumbnailUrl: '',
  dateAdded: new Date(),
  detailsUrl: '/document/123',
  state: 'processing',
  processingStatus: {
    stage: 'Embedding images',
    progress: 0.45  // 0.0 to 1.0
  }
});

document.querySelector('#container').appendChild(card);
```

### Updating State Dynamically

```javascript
import { createDocumentCard, updateCardState } from './modules/document-card.js';

// Create card in processing state
const card = createDocumentCard({
  filename: 'document.pdf',
  thumbnailUrl: '',
  dateAdded: new Date(),
  detailsUrl: '/document/123',
  state: 'processing',
  processingStatus: { stage: 'Parsing document', progress: 0.1 }
});

document.querySelector('#container').appendChild(card);

// Update progress
updateCardState(card, {
  state: 'processing',
  stage: 'Embedding images',
  progress: 0.45
});
```

### Batch Rendering

```javascript
import { renderDocumentCards } from './modules/document-card.js';

renderDocumentCards('#container', [
  {
    filename: 'presentation.pptx',
    thumbnailUrl: '/path/to/thumbnail.png',
    dateAdded: 'September 26',
    detailsUrl: '/document/456'
  },
  {
    filename: 'podcast-episode.mp3',
    thumbnailUrl: '/path/to/album-art.png',
    dateAdded: new Date(),
    detailsUrl: '/document/789',
    state: 'processing',
    processingStatus: { stage: 'Storing vectors', progress: 0.95 }
  }
]);
```

## API Reference

### `createDocumentCard(options)`

Creates a single DocumentCard element.

**Options:**
- `filename` (string, required) - Full filename with extension
- `thumbnailUrl` (string, required) - URL to thumbnail image
- `dateAdded` (string|Date, required) - Processing date
- `detailsUrl` (string, required) - URL for details button
- `variant` (string, optional) - 'document' or 'audio' (auto-detected if not provided)
- `placeholderColor` (string, optional) - Background color for missing images (default: '#E9E9E9')
- `state` (string, optional) - Card state: 'completed', 'loading', or 'processing' (default: 'completed')
- `processingStatus` (object, optional) - Processing status info (required if state is 'processing')
  - `stage` (string) - Current processing stage (e.g., 'Embedding images')
  - `progress` (number) - Progress from 0.0 to 1.0

**Returns:** HTMLElement (article)

### `createDocumentCards(documents)`

Creates multiple DocumentCard elements.

**Parameters:**
- `documents` (Array<Object>) - Array of document options

**Returns:** DocumentFragment

### `renderDocumentCards(container, documents)`

Renders multiple DocumentCards to a container.

**Parameters:**
- `container` (HTMLElement|string) - Container element or CSS selector
- `documents` (Array<Object>) - Array of document options

### `updateCardState(card, status)`

Updates an existing card's processing state dynamically. Useful for WebSocket status updates.

**Parameters:**
- `card` (HTMLElement) - The card element to update
- `status` (object) - Status update
  - `state` (string) - 'loading', 'processing', or 'completed'
  - `stage` (string, optional) - Current processing stage
  - `progress` (number, optional) - Progress from 0.0 to 1.0

**Example:**
```javascript
updateCardState(card, {
  state: 'processing',
  stage: 'Embedding text',
  progress: 0.75
});
```

## File Type Support

### Documents (Tall Variant)
- PDF, DOCX, DOC, PPTX, PPT
- XLSX, XLS, TXT, MD, HTML
- Icon: Lucide `file-text`

### Audio (Square Variant)
- MP3, WAV, FLAC, AAC, OGG, M4A
- Icon: Lucide `volume-2`

### Video (Square Variant)
- MP4, AVI, MOV, WMV, WebM
- Icon: Lucide `video`

## HTML Structure

```html
<article class="document-card document-card--document">
  <div class="document-card__left">
    <img class="document-card__thumbnail" src="..." alt="..." />
    <div class="document-card__badge">
      <div class="document-card__badge-date">Added September 26</div>
      <svg class="document-card__badge-icon">...</svg>
      <div class="document-card__badge-extension">PDF</div>
    </div>
  </div>
  <div class="document-card__right">
    <h3 class="document-card__title">quarterly-report-q3-2023</h3>
    <a class="document-card__button" href="...">Details</a>
  </div>
</article>
```

## CSS Classes

### Base Classes
- `.document-card` - Main container
- `.document-card--document` - Tall variant modifier
- `.document-card--audio` - Square variant modifier
- `.document-card--loading` - Loading state modifier
- `.document-card--processing` - Processing state modifier

### Element Classes
- `.document-card__left` - Left column (thumbnail + badge)
- `.document-card__right` - Right column (title + button OR processing info)
- `.document-card__thumbnail` - Thumbnail image
- `.document-card__badge` - Info badge overlay
- `.document-card__badge-date` - Date text
- `.document-card__badge-icon` - File type icon
- `.document-card__badge-extension` - Extension label
- `.document-card__title` - Document title
- `.document-card__button` - Details button

### Processing State Classes
- `.document-card__processing-info` - Container for processing elements
- `.document-card__status` - Container for spinner and status label
- `.document-card__spinner` - Rotating spinner animation
- `.document-card__status-label` - Processing stage text
- `.document-card__progress-container` - Container for progress bar and percentage
- `.document-card__progress` - Progress bar track
- `.document-card__progress-bar` - Progress bar fill
- `.document-card__progress-text` - Percentage text

## Styling

The component uses CSS variables from the main stylesheet:

```css
--spacing-xs, --spacing-sm, --spacing-md
--font-size-xs, --font-size-sm, --font-size-base
--color-border-focus
--radius-md
--shadow-md, --shadow-lg
--transition-base, --transition-fast
```

## Accessibility

- Semantic HTML (`<article>`, `<h3>`)
- ARIA labels for screen readers
- Keyboard navigation support
- Focus indicators
- Loading states
- Alt text for images

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6 modules required
- CSS Grid support required

## Demo

View the demo at: `document-card-demo.html`

## Integration with DocuSearch

The component is designed to work with:
- Document processing results from `/api/status`
- Thumbnail images from `/uploads/.page_images/`
- Document detail pages at `/document/{id}`
- Real-time WebSocket status updates

### Search Results Integration

```javascript
import { renderDocumentCards } from './modules/document-card.js';

fetch('/api/search?q=quarterly+report')
  .then(res => res.json())
  .then(data => {
    const cards = data.results.map(doc => ({
      filename: doc.filename,
      thumbnailUrl: doc.thumbnail_url,
      dateAdded: doc.processing_date,
      detailsUrl: `/document/${doc.id}`
    }));

    renderDocumentCards('#results', cards);
  });
```

### WebSocket Real-Time Updates

```javascript
import { createDocumentCard, updateCardState } from './modules/document-card.js';

// Store cards by doc_id for easy lookup
const cardMap = new Map();

// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8002/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'status_update') {
    const { doc_id, status, progress, stage, filename } = data;

    // Get or create card
    let card = cardMap.get(doc_id);

    if (!card) {
      // Create new card in processing state
      card = createDocumentCard({
        filename: filename,
        thumbnailUrl: '',
        dateAdded: new Date(),
        detailsUrl: `/document/${doc_id}`,
        state: 'processing',
        processingStatus: { stage, progress }
      });
      card.dataset.docId = doc_id;
      document.querySelector('#container').appendChild(card);
      cardMap.set(doc_id, card);
    } else {
      // Update existing card
      const cardState = status === 'completed' ? 'completed' : 'processing';
      updateCardState(card, {
        state: cardState,
        stage: stage,
        progress: progress
      });
    }
  }
};

// Status enum mapping (from src/processing/status_models.py)
// QUEUED, PARSING, EMBEDDING_VISUAL, EMBEDDING_TEXT, STORING → 'processing'
// COMPLETED → 'completed'
// FAILED → handle error state
```
