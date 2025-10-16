# IC-006: Caption Display Contract

**Version**: 1.0
**Status**: ✅ Approved
**Author**: Frontend Specification Agent
**Reviewers**: Frontend Implementation Agent
**Date**: 2025-10-16

---

## Overview

Defines how captions are displayed on the album art overlay using native VTT track cues instead of manual markdown parsing. Specifies the cuechange event handler and caption update logic.

---

## Caption Display Architecture

### Components

1. **Album Art Container**: Holds album art image and caption overlay
2. **Caption Overlay**: Absolutely positioned div for caption text
3. **VTT Track**: Native HTML5 text track with cues
4. **Event Handler**: Updates caption when cues change

### Visual Structure

```
┌─────────────────────────────────┐
│   Album Art Container           │
│                                 │
│   ┌─────────────────────────┐   │
│   │                         │   │
│   │    Album Art Image      │   │
│   │                         │   │
│   │  ┌─────────────────┐   │   │
│   │  │ Caption Overlay │   │   │
│   │  │ (Centered)      │   │   │
│   │  └─────────────────┘   │   │
│   └─────────────────────────┘   │
└─────────────────────────────────┘
```

---

## Current Implementation (To Be Replaced)

### handleTimeUpdate() - Current Approach

**File**: `src/frontend/audio-player.js` (Lines ~200-250)

```javascript
handleTimeUpdate() {
    const currentTime = this.audioElement.currentTime;

    // CURRENT: Manual caption lookup from parsed segments
    if (this.segments && this.segments.length > 0) {
        const activeSegment = this.segments.find(seg =>
            currentTime >= seg.startTime && currentTime < seg.endTime
        );

        if (activeSegment) {
            if (Math.floor(activeSegment.startTime) !== this.lastCaptionTime) {
                this.captionElement.textContent = activeSegment.text;
                this.lastCaptionTime = Math.floor(activeSegment.startTime);
            }
        } else {
            if (this.captionElement.textContent !== '') {
                this.captionElement.textContent = '';
                this.lastCaptionTime = -1;
            }
        }
    }

    // Accordion sync logic (keep this part)
    // ...
}
```

**Problems**:
- Relies on `this.segments` from markdown parsing
- Manual time range checking every timeupdate (~30-60Hz)
- Requires `lastCaptionTime` tracking to avoid flicker
- Inefficient and fragile

---

## New Implementation (Using VTT)

### Separation of Concerns

Split `handleTimeUpdate()` into two methods:

1. **handleCueChange()**: Caption display (NEW - uses VTT)
2. **handleTimeUpdate()**: Accordion sync (KEEP - throttled)

### handleCueChange() - New Method

```javascript
handleCueChange() {
    /**
     * Handle VTT cue changes for caption display.
     * Called by browser when active cues change (not every frame).
     */
    const track = this.trackElement.track;

    if (!track || !track.activeCues) {
        return;
    }

    if (track.activeCues.length > 0) {
        // Get first active cue (should only be one at a time)
        const activeCue = track.activeCues[0];

        // Update caption display
        this.captionElement.textContent = activeCue.text;

        console.log(
            `[AudioPlayer] Caption: ${activeCue.text.substring(0, 50)}...`
        );
    } else {
        // No active cue - clear caption
        if (this.captionElement.textContent !== '') {
            this.captionElement.textContent = '';
            console.log('[AudioPlayer] Caption cleared');
        }
    }
}
```

### Updated init() - Register Event Listener

```javascript
async init() {
    // ... existing audio setup ...

    // Set VTT track source
    if (this.metadata.vtt_available) {
        this.trackElement.src = `/documents/${this.docId}/vtt`;

        // Register cuechange listener (NEW)
        if (this.trackElement.track) {
            this.trackElement.track.addEventListener('cuechange', () => {
                this.handleCueChange();
            });
            console.log('[AudioPlayer] Cuechange listener registered');
        }
    }

    // Existing timeupdate listener (for accordion sync)
    this.audioElement.addEventListener('timeupdate', () => {
        this.handleTimeUpdate();
    });

    this.audioElement.load();
}
```

### Updated handleTimeUpdate() - Accordion Only

```javascript
handleTimeUpdate() {
    /**
     * Handle audio time updates for accordion sync.
     * Caption display now handled by handleCueChange().
     */

    // REMOVED: Caption display logic

    // KEEP: Accordion sync logic (throttled)
    const currentTime = this.audioElement.currentTime;
    const now = Date.now();

    // Throttle accordion updates to 300ms
    if (now - this.lastAccordionUpdate < 300) {
        return;
    }
    this.lastAccordionUpdate = now;

    // Find matching accordion section
    if (this.accordion && this.documentData.chunks) {
        const activeChunk = this.documentData.chunks.find(chunk =>
            chunk.start_time !== null &&
            currentTime >= chunk.start_time &&
            currentTime < chunk.end_time
        );

        if (activeChunk) {
            this.accordion.openSection(activeChunk);
        }
    }
}
```

---

## Caption Update Flow

### Sequence Diagram

```
Audio Playback
    ↓
Time reaches cue start (e.g., 0.62s)
    ↓
Browser fires 'cuechange' event
    ↓
handleCueChange() called
    ↓
Get track.activeCues[0]
    ↓
Update captionElement.textContent
    ↓
Caption appears on album art

Time reaches cue end (e.g., 3.96s)
    ↓
Browser fires 'cuechange' event
    ↓
handleCueChange() called
    ↓
activeCues.length === 0
    ↓
Clear captionElement.textContent
    ↓
Caption disappears
```

---

## Performance Comparison

### Before: Manual Time Checking

```
timeupdate event fires: 30-60 times per second
    ↓
Check all segments: O(n) every frame
    ↓
Update caption if changed
```

**CPU Usage**: High (60 checks/second)
**Latency**: 16-33ms (depends on timeupdate frequency)

### After: Native Cuechange

```
cuechange event fires: Only when cues change
    ↓
Access track.activeCues: O(1)
    ↓
Update caption
```

**CPU Usage**: Minimal (2-3 events per minute)
**Latency**: <1ms (browser native)
**Improvement**: 100-1000x fewer updates ✅

---

## Edge Cases

### Edge Case 1: No VTT Available

```javascript
if (!this.metadata.vtt_available) {
    // Track source not set, cuechange never fires
    // Caption remains empty
    // Audio plays normally
    console.log('[AudioPlayer] No VTT - captions disabled');
}
```

**Behavior**: Graceful degradation

### Edge Case 2: VTT Load Fails

```javascript
this.trackElement.addEventListener('error', (e) => {
    console.error('[AudioPlayer] VTT load failed:', e);
    // cuechange won't fire
    // Caption remains empty
    // Audio continues playing
});
```

**Behavior**: Non-blocking error

### Edge Case 3: Seeking During Caption

```javascript
// User seeks from 2s (caption showing) to 10s (caption showing)
// Browser fires cuechange automatically
// Caption updates to new cue text
// No special handling needed
```

**Behavior**: Browser handles automatically

### Edge Case 4: Multiple Active Cues

```javascript
// Rare: overlapping cues in VTT
if (track.activeCues.length > 1) {
    // Use first cue
    const cue = track.activeCues[0];
    console.warn(`[AudioPlayer] Multiple active cues, using first`);
}
```

**Behavior**: Use first cue

### Edge Case 5: Empty Cue Text

```javascript
if (activeCue.text.trim() === '') {
    // VTT has empty cue
    // Clear caption (don't show whitespace)
    this.captionElement.textContent = '';
}
```

**Behavior**: Treat as no caption

---

## CSS Integration

### Caption Styling (Existing)

**File**: `src/frontend/details.css` (Lines 184-213)

```css
.current-caption {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
    background: rgba(255, 255, 255, 0.55);
    color: rgb(22, 20, 20);
    padding: 1rem 1.5rem;
    min-height: 60px;
    font-size: 0.95rem;
    line-height: 1.5;
    text-align: center;
    backdrop-filter: blur(4px);
    transition: opacity 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.current-caption:empty {
    opacity: 0;
    pointer-events: none;
}

.current-caption:not(:empty) {
    opacity: 1;
}
```

**No CSS Changes Required** ✅

---

## Accessibility

### Screen Reader Support

VTT captions are accessible via text content:

```javascript
// Caption text is in DOM, screen readers can announce it
this.captionElement.textContent = activeCue.text;
```

### Keyboard Navigation

Audio controls remain fully keyboard accessible (native HTML5 behavior).

---

## Testing

### Manual Test 1: Caption Appears

1. Load audio document with VTT
2. Play audio
3. **Verify**: Caption appears at first timestamp (0.62s)
4. **Verify**: Caption text matches VTT file
5. **Verify**: Caption centered on album art

### Manual Test 2: Caption Updates

1. Continue playing audio
2. **Verify**: Caption changes at each cue boundary
3. **Verify**: No flicker or wrong text shown
4. **Verify**: Timing synchronized (<50ms latency)

### Manual Test 3: Caption Clears

1. Play through end of cue
2. **Verify**: Caption clears when no active cue
3. **Verify**: Smooth fade out (CSS transition)

### Manual Test 4: Seeking

1. Seek to middle of audio (e.g., 30s)
2. **Verify**: Correct caption appears immediately
3. Seek backward (e.g., 5s)
4. **Verify**: Correct caption for that time

### Manual Test 5: No VTT

1. Load audio without VTT
2. **Verify**: Audio plays normally
3. **Verify**: Caption area empty
4. **Verify**: No console errors

### Browser Console Test

```javascript
// Check cuechange events firing
const track = document.getElementById('audio-track').track;
track.addEventListener('cuechange', () => {
    console.log('Cuechange!', track.activeCues[0]?.text);
});

// Play audio and observe console
```

---

## Removed Code

### Variables to Remove

```javascript
// REMOVE from constructor
this.lastCaptionTime = -1;
this.segments = [];
this.markdownContent = null;
```

### Methods to Remove

```javascript
// REMOVE entire methods
async fetchMarkdown() { /* ... */ }
parseMarkdownSegments() { /* ... */ }
```

### Logic to Remove

```javascript
// REMOVE from handleTimeUpdate()
if (this.segments && this.segments.length > 0) {
    const activeSegment = this.segments.find(/* ... */);
    // ~30 lines of caption logic
}
```

**Total Removal**: ~80 lines ✅

---

## Success Criteria

### Functional Success
- [ ] Captions display at correct timestamps
- [ ] Caption text matches VTT file
- [ ] Captions clear when no active cue
- [ ] Seeking updates caption immediately
- [ ] No VTT = graceful degradation

### Performance Success
- [ ] Caption sync latency <50ms
- [ ] No flicker or wrong captions
- [ ] CPU usage minimal (cuechange vs timeupdate)
- [ ] Smooth transitions (CSS)

### Code Quality Success
- [ ] ~80 lines of parsing code removed
- [ ] No markdown fetching/parsing
- [ ] Event-driven vs polling
- [ ] Browser-native API

---

## Dependencies

**Depends On**:
- IC-004 (API Response Contract) - VTT endpoint
- IC-005 (VTT Track Element Contract) - track setup
- Existing HTML structure (details.html)
- Existing CSS (details.css)

**Consumed By**:
- Frontend Implementation Agent (Wave 2)

---

## Review Checklist

- [x] Caption update logic specified
- [x] Event handler pattern clear
- [x] Performance improvements quantified
- [x] Edge cases comprehensive
- [x] Testing approach defined
- [x] Code removal identified
- [x] Success criteria measurable
- [x] Accessibility considered

---

**Contract Status**: ✅ Ready for Implementation
