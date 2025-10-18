# Frontend Utilities Reference

**Wave 1 - Foundation Agent**

This document provides a comprehensive reference for all utility functions, constants, and error handling available in the React frontend.

## Directory Structure

```
frontend/src/
├── utils/
│   ├── clipboard.js          # Clipboard operations
│   ├── download.js           # File download utilities
│   ├── formatting.js         # Date/time/size formatters
│   ├── url.js                # URL builders
│   ├── assets.js             # SVG assets and icons
│   └── index.js              # Barrel export
├── constants/
│   ├── config.js             # App configuration
│   ├── routes.js             # Route constants
│   └── index.js              # Barrel export
└── components/
    └── ErrorBoundary.jsx     # Error boundary component
```

## Utilities

### Clipboard Utils (`utils/clipboard.js`)

```javascript
import { copyToClipboard, stripFrontmatter } from '@/utils/clipboard'

// Copy text to clipboard with visual feedback
await copyToClipboard(text, buttonElement)
// Returns: Promise<boolean>

// Strip YAML frontmatter from markdown
const cleanMarkdown = stripFrontmatter(markdown)
```

### Download Utils (`utils/download.js`)

```javascript
import {
  downloadMarkdown,
  downloadVTT,
  downloadTextAsFile,
  downloadFile
} from '@/utils/download'

// Download markdown file for a document
await downloadMarkdown(docId, buttonElement)

// Download VTT captions for audio
await downloadVTT(docId, buttonElement)

// Download text as file
downloadTextAsFile(text, 'filename.txt', 'text/plain')

// Generic file download
downloadFile('/api/file/url', 'filename.ext')
```

### Formatting Utils (`utils/formatting.js`)

```javascript
import {
  formatDate,
  formatFileSize,
  formatDuration,
  formatTimestamp,
  formatRelativeTime
} from '@/utils/formatting'

// Format date: "Jan 15, 2025"
const formattedDate = formatDate('2025-01-15T10:30:00Z')

// Format file size: "1.5 MB"
const size = formatFileSize(1572864)

// Format duration: "2:34:15" or "5:32"
const duration = formatDuration(9255)

// Format timestamp (always HH:MM:SS): "01:23:45"
const timestamp = formatTimestamp(5025)

// Format relative time: "2 hours ago"
const relTime = formatRelativeTime('2025-01-15T08:30:00Z')
```

### URL Utils (`utils/url.js`)

```javascript
import {
  buildDocumentUrl,
  buildThumbnailUrl,
  buildPageImageUrl,
  buildCoverArtUrl,
  buildMarkdownUrl,
  buildVTTUrl,
  buildAudioUrl,
  buildSearchUrl
} from '@/utils/url'

// Document detail page: "/details/abc123"
const detailUrl = buildDocumentUrl('abc123')

// Thumbnail: "/api/documents/abc123/thumbnail?page=1"
const thumbUrl = buildThumbnailUrl('abc123', 1)

// Page image: "/api/documents/abc123/pages/5"
const pageUrl = buildPageImageUrl('abc123', 5)

// Cover art: "/api/documents/abc123/cover-art"
const coverUrl = buildCoverArtUrl('abc123')

// Markdown: "/documents/abc123/markdown"
const mdUrl = buildMarkdownUrl('abc123')

// VTT captions: "/documents/abc123/vtt"
const vttUrl = buildVTTUrl('abc123')

// Audio source: "/documents/abc123/audio"
const audioUrl = buildAudioUrl('abc123')

// Search API: "/api/search?query=test&limit=50&offset=0"
const searchUrl = buildSearchUrl('test', { limit: 50, offset: 0 })
```

### Assets (`utils/assets.js`)

```javascript
import { DEFAULT_ALBUM_ART_SVG } from '@/utils/assets'

// Default gray microphone icon as base64 data URI
<img src={DEFAULT_ALBUM_ART_SVG} alt="Default album art" />
```

## Constants

### Config (`constants/config.js`)

```javascript
import {
  API_BASE_URL,
  WS_URL,
  COPYPARTY_URL,
  DEFAULT_PAGE_SIZE,
  SEARCH_DEBOUNCE_MS,
  RECONNECT_MAX_ATTEMPTS,
  REQUEST_TIMEOUT_MS,
  SUPPORTED_FILE_TYPES,
  FILE_TYPE_CATEGORIES,
  SORT_OPTIONS,
  DEFAULT_SORT,
  PROCESSING_STATUS,
  THEMES,
  STORAGE_KEYS
} from '@/constants/config'

// API endpoints
API_BASE_URL        // '/api' or VITE_API_URL
WS_URL              // 'ws://localhost:8002/ws' or VITE_WS_URL
COPYPARTY_URL       // 'http://localhost:8000' or VITE_COPYPARTY_URL

// Pagination & timing
DEFAULT_PAGE_SIZE          // 50
SEARCH_DEBOUNCE_MS         // 300
RECONNECT_MAX_ATTEMPTS     // 10
REQUEST_TIMEOUT_MS         // 30000

// File types
SUPPORTED_FILE_TYPES       // { document: ['.pdf', '.docx', '.pptx'], audio: ['.mp3', '.wav'] }
FILE_TYPE_CATEGORIES       // { all: 'All Types', document: 'Documents', audio: 'Audio' }

// Sorting
SORT_OPTIONS              // { date_desc, date_asc, name_asc, name_desc }
DEFAULT_SORT              // 'date_desc'

// Status
PROCESSING_STATUS         // { PENDING, PROCESSING, COMPLETE, FAILED }

// Theme
THEMES                    // { LIGHT: 'light', DARK: 'dark' }

// Storage
STORAGE_KEYS              // { THEME, LAST_SEARCH, SORT_PREFERENCE }
```

### Routes (`constants/routes.js`)

```javascript
import {
  ROUTES,
  buildDetailsPath,
  parseDetailsPath,
  isDetailsPath
} from '@/constants/routes'

// Route paths
ROUTES.LIBRARY    // '/'
ROUTES.DETAILS    // '/details/:id'
ROUTES.RESEARCH   // '/research'

// Build details path: "/details/abc123"
const path = buildDetailsPath('abc123')

// Parse document ID from path: "abc123" or null
const docId = parseDetailsPath('/details/abc123')

// Check if path is details path: true/false
const isDetails = isDetailsPath('/details/abc123')
```

## Components

### ErrorBoundary (`components/ErrorBoundary.jsx`)

React class component that catches JavaScript errors in child component tree.

```javascript
import ErrorBoundary from '@/components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <YourApp />
    </ErrorBoundary>
  )
}
```

**Features:**
- Catches and logs errors from child components
- Displays user-friendly fallback UI
- Shows error details in expandable section (dev mode)
- "Try Again" button to reset error state
- "Go to Home" button for navigation
- Styled with kraft paper theme variables

**Methods:**
- `getDerivedStateFromError(error)` - Update state on error
- `componentDidCatch(error, errorInfo)` - Log error details
- `handleReset()` - Reset error boundary state

## Import Patterns

### Direct Imports

```javascript
import { formatDate, formatFileSize } from '@/utils/formatting'
import { API_BASE_URL, DEFAULT_PAGE_SIZE } from '@/constants/config'
import { ROUTES, buildDetailsPath } from '@/constants/routes'
```

### Barrel Imports

```javascript
import * as utils from '@/utils'
import * as constants from '@/constants'

// Usage
utils.formatDate('2025-01-15')
constants.API_BASE_URL
```

## Usage Examples

### Document Card with Formatting

```javascript
import { formatDate, formatFileSize, buildThumbnailUrl } from '@/utils'

function DocumentCard({ doc }) {
  return (
    <div className="doc-card">
      <img src={buildThumbnailUrl(doc.id)} alt={doc.filename} />
      <h3>{doc.filename}</h3>
      <p>Uploaded: {formatDate(doc.upload_date)}</p>
      <p>Size: {formatFileSize(doc.file_size)}</p>
    </div>
  )
}
```

### Audio Player with Duration

```javascript
import { formatDuration, buildAudioUrl, buildCoverArtUrl } from '@/utils'
import { DEFAULT_ALBUM_ART_SVG } from '@/utils/assets'

function AudioPlayer({ doc }) {
  const coverArt = doc.has_cover_art ? buildCoverArtUrl(doc.id) : DEFAULT_ALBUM_ART_SVG

  return (
    <div className="audio-player">
      <img src={coverArt} alt="Album art" />
      <audio src={buildAudioUrl(doc.id)} controls />
      <span>{formatDuration(doc.duration)}</span>
    </div>
  )
}
```

### Search with Debouncing

```javascript
import { useState, useEffect } from 'react'
import { SEARCH_DEBOUNCE_MS, buildSearchUrl } from '@/constants'

function SearchBar() {
  const [query, setQuery] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query) {
        fetch(buildSearchUrl(query))
          .then(res => res.json())
          .then(data => console.log(data))
      }
    }, SEARCH_DEBOUNCE_MS)

    return () => clearTimeout(timer)
  }, [query])

  return <input value={query} onChange={e => setQuery(e.target.value)} />
}
```

### Navigation with Routes

```javascript
import { useNavigate } from 'react-router-dom'
import { buildDetailsPath } from '@/constants/routes'

function DocumentList({ documents }) {
  const navigate = useNavigate()

  const handleClick = (docId) => {
    navigate(buildDetailsPath(docId))
  }

  return (
    <ul>
      {documents.map(doc => (
        <li key={doc.id} onClick={() => handleClick(doc.id)}>
          {doc.filename}
        </li>
      ))}
    </ul>
  )
}
```

## Testing Utilities

All utilities are pure functions and can be easily tested:

```javascript
import { formatDate, formatFileSize, formatDuration } from '@/utils/formatting'

describe('Formatting utils', () => {
  test('formatDate returns formatted date', () => {
    expect(formatDate('2025-01-15T10:30:00Z')).toBe('Jan 15, 2025')
  })

  test('formatFileSize returns human-readable size', () => {
    expect(formatFileSize(1572864)).toBe('1.5 MB')
  })

  test('formatDuration returns HH:MM:SS for long durations', () => {
    expect(formatDuration(9255)).toBe('2:34:15')
  })
})
```

## Next Steps

These utilities are now available for use by all agents:

- **Library Agent**: Use formatting utils for document cards
- **Details Agent**: Use URL builders for page images and downloads
- **Research Agent**: Use URL builders for API endpoints
- **Layout Agent**: Use constants for theme and configuration

## Notes

- All utilities use ES6 modules with named exports
- Utilities are framework-agnostic (work with any React setup)
- Constants use environment variables with sensible defaults
- ErrorBoundary uses kraft paper theme CSS variables
- All utilities include JSDoc comments for IDE autocomplete
