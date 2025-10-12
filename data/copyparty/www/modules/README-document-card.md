# DocumentCard Component

A reusable, accessible document information card component for displaying document metadata, thumbnails, and actions.

## Features

✓ **Two variants**: Document (tall 200×262) and Audio (square 200×200)
✓ **Auto-detection**: Automatically selects variant based on file extension
✓ **Responsive**: Adapts to mobile screens
✓ **Accessible**: ARIA labels, keyboard navigation, focus management
✓ **Icon support**: SVG icons for documents, audio, and video files
✓ **Graceful degradation**: Placeholder backgrounds for missing thumbnails
✓ **Hover effects**: Smooth transitions and interactive states

## Files

- `document-card.js` - Component module
- `styles.css` - Component styles (lines 1042-1197)
- `document-card-demo.html` - Demo page

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
    detailsUrl: '/document/789'
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

## File Type Support

### Documents (Tall Variant)
- PDF, DOCX, DOC, PPTX, PPT
- XLSX, XLS, TXT, MD, HTML

### Audio (Square Variant)
- MP3, WAV, FLAC, AAC, OGG, M4A

### Video (Square Variant)
- MP4, AVI, MOV, WMV, WebM

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

### Element Classes
- `.document-card__left` - Left column (thumbnail + badge)
- `.document-card__right` - Right column (title + button)
- `.document-card__thumbnail` - Thumbnail image
- `.document-card__badge` - Info badge overlay
- `.document-card__badge-date` - Date text
- `.document-card__badge-icon` - File type icon
- `.document-card__badge-extension` - Extension label
- `.document-card__title` - Document title
- `.document-card__button` - Details button

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

Example integration with search results:

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
