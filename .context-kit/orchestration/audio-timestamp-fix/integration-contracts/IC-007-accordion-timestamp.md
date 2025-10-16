# IC-007: Accordion Timestamp Contract

**Version**: 1.0
**Status**: ✅ Approved
**Author**: Frontend Specification Agent
**Reviewers**: Frontend Implementation Agent
**Date**: 2025-10-16

---

## Overview

Defines how the accordion component displays transcript segments using chunk timestamps directly from the API instead of parsing markdown. Specifies the updated display logic and section creation.

---

## Current Implementation (To Be Replaced)

### addChunkSections() - Current Approach

**File**: `src/frontend/accordion.js` (Lines ~117-164)

```javascript
addChunkSections() {
    // CURRENT: Parse markdown into segments
    const segments = this.parseMarkdownSegments();

    if (segments.length > 0) {
        // Use parsed segments from markdown (full text)
        segments.forEach((segment, index) => {
            const section = this.createSection({
                id: `segment-${index}`,
                title: `Segment ${index + 1} (${this.formatTime(segment.startTime)} - ${this.formatTime(segment.endTime)})`,
                content: segment.text,
                isOpen: false,
                timestamp: { start: segment.startTime, end: segment.endTime },
                // ...
            });
            this.container.appendChild(section);
        });
    } else {
        // Fallback to using chunks (truncated)
        this.chunks.forEach((chunk, index) => { /* ... */ });
    }
}
```

**Problems**:
- Relies on `parseMarkdownSegments()` for full text
- Falls back to truncated chunks if parsing fails
- Duplicate logic for segment vs chunk handling
- Complex and fragile

---

## New Implementation (Using Chunk Timestamps)

### Updated addChunkSections()

```javascript
addChunkSections() {
    /**
     * Display chunk sections with timestamps.
     * Uses chunk.start_time/end_time directly from API.
     * Text comes from chunk.text_content (already cleaned).
     */

    if (!this.chunks || this.chunks.length === 0) {
        console.warn('[Accordion] No chunks available');
        return;
    }

    this.chunks.forEach((chunk, index) => {
        // Determine section title based on timestamp presence
        const sectionTitle = this.getChunkTitle(chunk, index);

        // Create section with chunk data
        const section = this.createSection({
            id: chunk.chunk_id,
            title: sectionTitle,
            content: chunk.text_content,  // Already cleaned (no [time: X-Y])
            isOpen: false,
            timestamp: chunk.start_time !== null ? {
                start: chunk.start_time,
                end: chunk.end_time
            } : null,
            pageNum: this.getPageFromChunk(chunk),
            actions: [
                {
                    label: '📋 Copy',
                    handler: (btn) => copyToClipboard(chunk.text_content, btn)
                }
            ]
        });

        this.container.appendChild(section);
    });

    console.log(`[Accordion] Created ${this.chunks.length} sections`);
}
```

### getChunkTitle() - Updated

```javascript
getChunkTitle(chunk, index) {
    /**
     * Generate section title with optional timestamp.
     *
     * Examples:
     *   - With timestamps: "Segment 1 (0:00 - 0:04)"
     *   - Without timestamps: "Chunk 1"
     */

    if (chunk.start_time !== null && chunk.end_time !== null) {
        // Format: "Segment N (MM:SS - MM:SS)"
        const startStr = this.formatTime(chunk.start_time);
        const endStr = this.formatTime(chunk.end_time);
        return `Segment ${index + 1} (${startStr} - ${endStr})`;
    } else {
        // No timestamps - simple title
        const pageNum = this.getPageFromChunk(chunk);
        if (pageNum) {
            return `Chunk ${index + 1} (Page ${pageNum})`;
        } else {
            return `Chunk ${index + 1}`;
        }
    }
}
```

---

## Chunk Data Source

### From API Response (IC-004)

```javascript
// GET /documents/{doc_id}
{
    "chunks": [
        {
            "chunk_id": "chunk_5e57bdeb-...-chunk0000",
            "text_content": "Myth 1. Ideas come in a flash.",  // CLEANED
            "start_time": 0.62,  // POPULATED
            "end_time": 3.96,    // POPULATED
            "has_timestamps": true
        }
    ]
}
```

**Key Points**:
- `text_content` no longer contains `[time: X-Y]` markers
- `start_time` and `end_time` are floats, not null
- Chunks from API are ready to use directly

---

## Section Display Format

### With Timestamps

```
┌─────────────────────────────────────────────┐
│ ▼ Segment 1 (0:00 - 0:04)                  │
├─────────────────────────────────────────────┤
│ 📋 Copy                                     │
│                                             │
│ Myth 1. Ideas come in a flash.             │
│                                             │
└─────────────────────────────────────────────┘
```

### Without Timestamps

```
┌─────────────────────────────────────────────┐
│ ▼ Chunk 1                                   │
├─────────────────────────────────────────────┤
│ 📋 Copy                                     │
│                                             │
│ Some text without timestamps.               │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Audio Sync Integration

### openSection() - Updated

**Current Code** (Lines ~317-387):
```javascript
openSection(chunkOrTimestamp) {
    // Complex logic to find section by chunk_id or timestamp
    // Parses timestamp from text if chunk_id not found
    // Matches by comparing timestamps
}
```

**Simplified Logic**:
```javascript
openSection(chunk) {
    /**
     * Open accordion section for given chunk.
     * Called by audio player during playback.
     *
     * @param {Object} chunk - Chunk object with chunk_id
     */

    if (!chunk || !chunk.chunk_id) {
        console.warn('[Accordion] openSection called without valid chunk');
        return;
    }

    // Find section by chunk_id (much simpler now)
    const section = this.container.querySelector(
        `[data-section-id="${chunk.chunk_id}"]`
    );

    if (!section) {
        console.warn(`[Accordion] Section not found: ${chunk.chunk_id}`);
        return;
    }

    const header = section.querySelector('.accordion-header');
    const content = section.querySelector('.accordion-content');

    if (!header || !content) {
        console.error('[Accordion] Section missing header or content');
        return;
    }

    // Close all other sections
    this.closeAllSections();

    // Open this section
    header.classList.add('open', 'active');
    content.classList.add('open');

    // Scroll into view
    section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    console.log(`[Accordion] Opened section: ${chunk.chunk_id}`);
}
```

**Simplification**: No more timestamp parsing or matching logic ✅

---

## Click-to-Seek Integration

### createSection() - Timestamp Handler

**File**: `src/frontend/accordion.js` (Lines ~260-281)

```javascript
// Existing click-to-seek logic (unchanged)
if (timestamp && timestamp.start !== null && timestamp.start >= 0 && this.audioPlayer) {
    header.addEventListener('click', () => {
        try {
            console.log(`[Accordion→Audio] Seeking to ${timestamp.start}s`);
            this.audioPlayer.seekTo(timestamp.start);
        } catch (error) {
            console.error('Failed to seek audio:', error);
        }
    });
}
```

**Status**: This code remains unchanged and works with new chunk timestamps ✅

---

## Removed Code

### Methods to Remove

```javascript
// REMOVE entire method (~40 lines)
parseMarkdownSegments() {
    // Complex regex parsing of markdown
    // Timestamp extraction
    // Text segmentation
}
```

```javascript
// REMOVE from constructor
this.markdownContent = null;
this.segments = [];
```

```javascript
// REMOVE from init()
async fetchMarkdown() {
    // Fetches markdown from API
}

await this.fetchMarkdown();
```

**Total Removal**: ~60 lines ✅

---

## Backward Compatibility

### Chunks Without Timestamps

```javascript
// API returns chunk with null timestamps
{
    "chunk_id": "chunk_...",
    "text_content": "Text without timestamps",
    "start_time": null,
    "end_time": null
}

// Display as simple chunk (no timestamp in title)
// Click-to-seek disabled (no timestamp handler attached)
// Copy button still works
```

**Behavior**: Graceful degradation ✅

---

## Testing

### Manual Test 1: Sections Display

1. Load audio document with timestamps
2. Open accordion
3. **Verify**: All sections present (13 segments)
4. **Verify**: Section titles show timestamps: "Segment 1 (0:00 - 0:04)"
5. **Verify**: Text content clean (no `[time: X-Y]` markers)

### Manual Test 2: Click to Seek

1. Click segment header
2. **Verify**: Audio seeks to segment start time
3. **Verify**: Caption updates immediately
4. **Verify**: No console errors

### Manual Test 3: Audio Sync

1. Play audio
2. **Verify**: Accordion section highlights when audio reaches it
3. **Verify**: Only one section open at a time
4. **Verify**: Section scrolls into view

### Manual Test 4: Copy Functionality

1. Click 📋 Copy button
2. **Verify**: Text copied to clipboard
3. **Verify**: Button shows success state
4. **Verify**: Text is clean (no markers)

### Manual Test 5: No Timestamps

1. Load document without timestamps
2. **Verify**: Sections display as "Chunk 1", "Chunk 2"
3. **Verify**: Click-to-seek disabled
4. **Verify**: Text displays normally

---

## Integration with Audio Player

### Bidirectional Sync

```
Audio Player                    Accordion
     │                              │
     │  handleTimeUpdate()          │
     ├─────────────────────────────>│
     │  calls openSection(chunk)    │
     │                              │
     │                         Section opened
     │                         and highlighted
     │                              │
     │<─────────────────────────────┤
User clicks section header          │
     │                              │
     │  seekTo(timestamp)           │
     │                              │
Audio seeks to time                 │
Caption updates                     │
```

**Status**: This flow continues to work with new implementation ✅

---

## Performance Improvements

### Before: Markdown Parsing

```
Init accordion
    ↓
Fetch markdown (HTTP request)
    ↓
Parse all timestamps with regex (O(n*m))
    ↓
Extract text between markers
    ↓
Create sections
```

**Time**: ~100-200ms for markdown fetch + parse

### After: Direct Chunk Usage

```
Init accordion
    ↓
Use chunks from API (already fetched)
    ↓
Create sections
```

**Time**: ~10ms
**Improvement**: 10-20x faster ✅

---

## Success Criteria

### Display Success
- [ ] All segments display with correct timestamps
- [ ] Section titles formatted correctly
- [ ] Text content clean (no markers)
- [ ] Sections display in correct order

### Interaction Success
- [ ] Click-to-seek works correctly
- [ ] Audio sync highlights correct section
- [ ] Copy button copies clean text
- [ ] Single-section behavior maintained

### Code Quality Success
- [ ] ~60 lines of parsing code removed
- [ ] No markdown fetching
- [ ] Simpler, more direct logic
- [ ] Backward compatible

---

## Dependencies

**Depends On**:
- IC-004 (API Response Contract) - chunks with timestamps
- Existing HTML structure (details.html)
- Existing CSS (details.css)
- Existing audio player integration

**Consumed By**:
- Frontend Implementation Agent (Wave 2)

---

## Review Checklist

- [x] Section creation logic specified
- [x] Title formatting defined
- [x] Audio sync preserved
- [x] Click-to-seek maintained
- [x] Backward compatibility ensured
- [x] Code removal identified
- [x] Performance improvements documented
- [x] Success criteria measurable

---

**Contract Status**: ✅ Ready for Implementation
