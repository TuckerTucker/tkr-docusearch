# UI HTML Structure Contract

**Provider**: ui-static-setup-agent
**Consumers**: ui-styling-agent, upload-logic-agent, monitoring-logic-agent
**Wave**: 2
**Status**: Specification

## Overview

Defines the semantic HTML structure for the custom upload interface. All HTML must be accessible, semantic, and provide clear hooks for CSS styling and JavaScript functionality.

## File Structure

```
src/ui/
├── index.html          # Main upload page
├── status.html         # Queue monitoring page (optional standalone)
└── (mounted at /ui)
```

## index.html - Main Upload Page

### Document Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="DocuSearch - Upload and search documents with AI">
    <title>DocuSearch Upload</title>
    <link rel="stylesheet" href="/ui/styles.css">
</head>
<body>
    <div id="app">
        <!-- Header -->
        <header class="app-header">
            <h1 class="app-title">DocuSearch</h1>
            <p class="app-subtitle">Upload documents for AI-powered search</p>
        </header>

        <!-- Main Content -->
        <main class="app-main">
            <!-- Upload Section -->
            <section id="upload-section" class="upload-section">
                <!-- File Drop Zone -->
                <div id="drop-zone" class="drop-zone">
                    <div class="drop-zone-content">
                        <svg class="drop-zone-icon" aria-hidden="true">
                            <!-- Upload icon SVG -->
                        </svg>
                        <p class="drop-zone-text">
                            Drag and drop files here, or
                            <label for="file-input" class="file-input-label">browse</label>
                        </p>
                        <input
                            type="file"
                            id="file-input"
                            class="file-input"
                            multiple
                            accept=".pdf,.docx,.pptx,.xlsx,.md,.html,.csv,.png,.jpg,.jpeg,.tiff,.bmp,.webp,.vtt,.wav,.mp3,.xml,.json"
                            aria-label="Choose files to upload"
                        />
                    </div>
                </div>

                <!-- Format Info -->
                <details class="format-info">
                    <summary class="format-info-summary">Supported Formats (21 total)</summary>
                    <div class="format-info-content">
                        <div class="format-category">
                            <h3 class="format-category-title">Documents (6)</h3>
                            <ul class="format-list">
                                <li>PDF - Portable Document Format</li>
                                <li>DOCX - Microsoft Word</li>
                                <li>PPTX - Microsoft PowerPoint</li>
                                <li>XLSX - Microsoft Excel</li>
                                <li>MD - Markdown</li>
                                <li>HTML - Web pages</li>
                            </ul>
                        </div>
                        <div class="format-category">
                            <h3 class="format-category-title">Images (6)</h3>
                            <ul class="format-list">
                                <li>PNG, JPEG, TIFF, BMP, WEBP</li>
                            </ul>
                        </div>
                        <div class="format-category">
                            <h3 class="format-category-title">Data (2)</h3>
                            <ul class="format-list">
                                <li>CSV - Comma-separated values</li>
                                <li>JSON - Docling native format</li>
                            </ul>
                        </div>
                        <div class="format-category">
                            <h3 class="format-category-title">Audio (3)</h3>
                            <ul class="format-list">
                                <li>VTT - Subtitles/captions</li>
                                <li>WAV, MP3 - Audio (with ASR)</li>
                            </ul>
                        </div>
                    </div>
                </details>
            </section>

            <!-- Processing Queue Section -->
            <section id="queue-section" class="queue-section">
                <header class="queue-header">
                    <h2 class="queue-title">Processing Queue</h2>
                    <div class="queue-stats">
                        <span id="queue-active-count" class="queue-stat">
                            <span class="queue-stat-value">0</span>
                            <span class="queue-stat-label">active</span>
                        </span>
                        <span id="queue-completed-count" class="queue-stat">
                            <span class="queue-stat-value">0</span>
                            <span class="queue-stat-label">completed</span>
                        </span>
                    </div>
                </header>

                <!-- Queue Items Container -->
                <div id="queue-items" class="queue-items">
                    <!-- Queue items will be inserted here by JavaScript -->
                    <!-- Example structure:
                    <article class="queue-item" data-doc-id="abc123" data-status="embedding_visual">
                        <div class="queue-item-header">
                            <h3 class="queue-item-filename">report.pdf</h3>
                            <span class="queue-item-status">Processing</span>
                        </div>
                        <div class="queue-item-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 65%"></div>
                            </div>
                            <span class="progress-text">65% - Visual embeddings</span>
                        </div>
                        <div class="queue-item-details">
                            <span class="queue-item-time">1m 30s elapsed</span>
                            <span class="queue-item-eta">~48s remaining</span>
                        </div>
                    </article>
                    -->
                </div>

                <!-- Empty State -->
                <div id="queue-empty" class="queue-empty">
                    <p>No documents uploaded yet. Drag and drop files above to get started.</p>
                </div>
            </section>
        </main>

        <!-- Footer -->
        <footer class="app-footer">
            <p class="footer-text">
                DocuSearch - AI-powered document search with ColPali
            </p>
        </footer>

        <!-- Toast Notifications -->
        <div id="toast-container" class="toast-container" aria-live="polite" aria-atomic="true">
            <!-- Toast messages inserted here by JavaScript -->
        </div>
    </div>

    <!-- Scripts -->
    <script type="module" src="/ui/upload.js"></script>
    <script type="module" src="/ui/monitor.js"></script>
</body>
</html>
```

---

## status.html - Standalone Queue Monitor (Optional)

Simplified queue-only view for monitoring existing uploads:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuSearch - Processing Status</title>
    <link rel="stylesheet" href="/ui/styles.css">
</head>
<body>
    <div id="app">
        <header class="app-header">
            <h1 class="app-title">Processing Status</h1>
        </header>

        <main class="app-main">
            <section id="queue-section" class="queue-section">
                <!-- Same queue structure as index.html -->
                <div id="queue-items" class="queue-items"></div>
                <div id="queue-empty" class="queue-empty">
                    <p>No documents currently processing.</p>
                </div>
            </section>
        </main>
    </div>

    <script type="module" src="/ui/monitor.js"></script>
</body>
</html>
```

---

## HTML Element Contracts

### Required IDs (for JavaScript access)

| ID | Element | Purpose |
|----|---------|---------|
| `app` | `<div>` | Root application container |
| `drop-zone` | `<div>` | File drop target |
| `file-input` | `<input>` | File picker |
| `upload-section` | `<section>` | Upload area |
| `queue-section` | `<section>` | Queue display area |
| `queue-items` | `<div>` | Queue items container |
| `queue-empty` | `<div>` | Empty state message |
| `queue-active-count` | `<span>` | Active count display |
| `queue-completed-count` | `<span>` | Completed count display |
| `toast-container` | `<div>` | Toast notification area |

### Required Classes (for CSS styling)

**Layout Classes**:
- `app-header`, `app-main`, `app-footer`: Page sections
- `upload-section`, `queue-section`: Feature sections

**Upload Classes**:
- `drop-zone`: Drag-and-drop target
- `drop-zone-content`: Inner content wrapper
- `drop-zone-icon`: Upload icon
- `drop-zone-text`: Instruction text
- `file-input`: Hidden file input
- `file-input-label`: Styled label for file input

**Queue Classes**:
- `queue-header`, `queue-title`: Queue section header
- `queue-stats`, `queue-stat`: Statistics display
- `queue-items`: Queue container
- `queue-item`: Individual queue item
- `queue-item-header`, `queue-item-filename`, `queue-item-status`: Item header
- `queue-item-progress`: Progress section
- `progress-bar`, `progress-fill`: Progress bar components
- `progress-text`: Progress percentage text
- `queue-item-details`: Additional details
- `queue-empty`: Empty state

**State Classes** (applied by JavaScript):
- `drop-zone--active`: When dragging over
- `drop-zone--error`: On validation error
- `queue-item--completed`: Completed items
- `queue-item--failed`: Failed items
- `queue-item--processing`: Active processing

---

## Data Attributes (for JavaScript state)

Queue items must include:
- `data-doc-id`: Document ID for status tracking
- `data-status`: Current processing status
- `data-progress`: Progress value (0.0-1.0)

Example:
```html
<article
    class="queue-item queue-item--processing"
    data-doc-id="abc123"
    data-status="embedding_visual"
    data-progress="0.65"
>
```

---

## Accessibility Requirements

### Semantic HTML
- Use `<header>`, `<main>`, `<section>`, `<article>`, `<footer>`
- Heading hierarchy: `<h1>` → `<h2>` → `<h3>`
- Form labels associated with inputs

### ARIA Attributes
- `aria-label` on file input
- `aria-live="polite"` on toast container
- `aria-atomic="true"` on toast container
- `aria-hidden="true"` on decorative icons

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Tab order: file input → format details → queue items
- Enter/Space to activate buttons and labels

### Focus Management
- Visible focus indicators (handled by CSS)
- Focus trap in modals (if added later)
- Focus returns to file input after upload

---

## Responsive Breakpoints

HTML must support these CSS breakpoints:

- **Mobile**: 320px - 767px (single column)
- **Tablet**: 768px - 1023px (flexible layout)
- **Desktop**: 1024px+ (two-column or wide single column)

No inline styles - all responsive behavior via CSS.

---

## Static File Mounting

### FastAPI Integration

The worker must serve static files:

```python
# In worker_webhook.py
from fastapi.staticfiles import StaticFiles

app.mount("/ui", StaticFiles(directory="src/ui", html=True), name="ui")
```

**Routes**:
- `http://localhost:8002/ui/` → `src/ui/index.html`
- `http://localhost:8002/ui/status.html` → `src/ui/status.html`
- `http://localhost:8002/ui/styles.css` → `src/ui/styles.css`
- `http://localhost:8002/ui/upload.js` → `src/ui/upload.js`
- `http://localhost:8002/ui/monitor.js` → `src/ui/monitor.js`

---

## Acceptance Tests

### HTML Validation
```bash
# W3C HTML validator
curl -s -H "Content-Type: text/html; charset=utf-8" \
  --data-binary @src/ui/index.html \
  https://validator.w3.org/nu/?out=json

# Expected: No errors
```

### Accessibility Audit
```bash
# axe-core CLI
axe http://localhost:8002/ui/ --tags wcag2a,wcag2aa

# Expected: No violations
```

### Semantic Structure
```bash
# Check heading hierarchy
grep -E '<h[1-6]' src/ui/index.html

# Expected:
# <h1> (1x) - Page title
# <h2> (1x) - Queue title
# <h3> (4x) - Format categories
```

### Required Elements
```python
from bs4 import BeautifulSoup

html = open("src/ui/index.html").read()
soup = BeautifulSoup(html, "html.parser")

# Check required IDs
required_ids = ["app", "drop-zone", "file-input", "queue-items", "queue-empty"]
for id in required_ids:
    assert soup.find(id=id) is not None, f"Missing required ID: {id}"

# Check file input accept attribute
file_input = soup.find(id="file-input")
assert ".pdf" in file_input["accept"]
assert ".md" in file_input["accept"]

# Check ARIA attributes
toast_container = soup.find(id="toast-container")
assert toast_container["aria-live"] == "polite"
```

---

## Integration Points

**Provides to**:
- `ui-styling-agent`: Class names and element structure for CSS
- `upload-logic-agent`: DOM elements for upload interaction
- `monitoring-logic-agent`: DOM elements for progress display

**Depends on**:
- `status-api.contract.md`: API endpoints for JavaScript to call (indirect)

---

## Implementation Notes

- Keep HTML minimal and semantic
- No inline JavaScript or CSS
- All dynamic content via JavaScript DOM manipulation
- SVG icons embedded or loaded from `/ui/assets/`
- Use `<template>` tags for queue item templates (optional optimization)
- Ensure HTML works without JavaScript (graceful degradation)
