# IC-005: VTT Track Element Contract

**Version**: 1.0
**Status**: ✅ Approved
**Author**: Frontend Specification Agent
**Reviewers**: Frontend Implementation Agent
**Date**: 2025-10-16

---

## Overview

Defines how to use the native HTML5 `<track>` element to load and display VTT captions in the audio player. Replaces manual markdown parsing with browser-native caption handling.

---

## HTML Structure

### Current HTML (details.html Lines ~50-60)
```html
<audio id="audio-player" class="audio-player" controls>
    <source id="audio-source" src="" type="audio/mpeg">
    <track
        id="audio-track"
        kind="captions"
        srclang="en"
        label="English"
        src=""
        default>
    Your browser does not support the audio element.
</audio>
```

**Status**: HTML structure already exists and is correct ✅

---

## Track Element Configuration

### Required Attributes

```html
<track
    id="audio-track"
    kind="captions"          <!-- Type of track -->
    srclang="en"             <!-- Language code -->
    label="English"          <!-- Human-readable label -->
    src="/documents/{doc_id}/vtt"  <!-- VTT source URL -->
    default                  <!-- Show by default -->
>
```

### Attribute Specification

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `id` | `"audio-track"` | JavaScript reference |
| `kind` | `"captions"` | Track type (captions vs subtitles vs metadata) |
| `srclang` | `"en"` | ISO 639-1 language code |
| `label` | `"English"` | Display name in browser controls |
| `src` | `/documents/{doc_id}/vtt` | URL to VTT file |
| `default` | (boolean) | Load and show by default |

---

## JavaScript Integration

### AudioPlayer Class Initialization

**File**: `src/frontend/audio-player.js`
**Method**: `constructor()` and `init()`

### Setting Track Source

```javascript
class AudioPlayer {
    constructor(audioElementId, docId, metadata) {
        this.audioElement = document.getElementById(audioElementId);
        this.trackElement = document.getElementById('audio-track');
        this.docId = docId;
        this.metadata = metadata;

        this.init();
    }

    async init() {
        // Set audio source
        const audioSource = document.getElementById('audio-source');
        audioSource.src = `/documents/${this.docId}/audio`;

        // Set track source (NEW)
        if (this.metadata.vtt_available) {
            this.trackElement.src = `/documents/${this.docId}/vtt`;
            console.log('[AudioPlayer] VTT track loaded');
        } else {
            // No VTT available - graceful degradation
            this.trackElement.src = '';
            console.log('[AudioPlayer] No VTT available');
        }

        // Bind event listeners
        this.audioElement.addEventListener('timeupdate', () => this.handleTimeUpdate());

        // Listen to cuechange events (NEW)
        if (this.trackElement.track) {
            this.trackElement.track.addEventListener('cuechange', () => this.handleCueChange());
        }

        // Force load
        this.audioElement.load();
    }
}
```

---

## Track Loading States

### State 1: Track Not Loaded
```javascript
// Check if track has loaded
if (this.trackElement.readyState === HTMLTrackElement.NONE) {
    console.log('[AudioPlayer] Track not loaded yet');
}
```

### State 2: Track Loading
```javascript
if (this.trackElement.readyState === HTMLTrackElement.LOADING) {
    console.log('[AudioPlayer] Track loading...');
}
```

### State 3: Track Loaded
```javascript
if (this.trackElement.readyState === HTMLTrackElement.LOADED) {
    console.log('[AudioPlayer] Track loaded successfully');
    // Can now access track.cues
}
```

### State 4: Track Error
```javascript
if (this.trackElement.readyState === HTMLTrackElement.ERROR) {
    console.error('[AudioPlayer] Track failed to load');
    // Fallback: no captions
}
```

---

## Accessing Track Data

### Track Object Hierarchy

```javascript
// HTML Element
const trackElement = document.getElementById('audio-track');

// TextTrack Object (browser API)
const track = trackElement.track;

// TextTrackCueList (all cues in VTT file)
const allCues = track.cues;
console.log(`Total cues: ${allCues.length}`);

// TextTrackCueList (currently active cues)
const activeCues = track.activeCues;
if (activeCues.length > 0) {
    const currentCue = activeCues[0];
    console.log(`Current caption: ${currentCue.text}`);
}
```

### TextTrackCue Interface

```javascript
// Access cue properties
const cue = track.activeCues[0];

console.log(cue.startTime);  // Float: 0.62
console.log(cue.endTime);    // Float: 3.96
console.log(cue.text);       // String: "Myth 1. Ideas come in a flash."
console.log(cue.id);         // String: "1" (cue number from VTT)
```

---

## Event Handling

### cuechange Event

**Trigger**: Fires when active cues change (caption should update)

```javascript
trackElement.track.addEventListener('cuechange', () => {
    const track = trackElement.track;

    if (track.activeCues && track.activeCues.length > 0) {
        const activeCue = track.activeCues[0];
        console.log(`[Cuechange] ${activeCue.text}`);

        // Update caption display
        this.captionElement.textContent = activeCue.text;
    } else {
        // No active cue - clear caption
        this.captionElement.textContent = '';
    }
});
```

**Frequency**: Fires only when cues change, not on every timeupdate
**Performance**: Much more efficient than manual time checking

---

## Error Handling

### Scenario 1: VTT Not Available

```javascript
if (!this.metadata.vtt_available) {
    // Don't set track source
    this.trackElement.src = '';
    console.log('[AudioPlayer] No VTT available - captions disabled');
    // Audio still plays, just no captions
}
```

### Scenario 2: VTT Load Fails

```javascript
this.trackElement.addEventListener('error', (e) => {
    console.error('[AudioPlayer] Failed to load VTT track:', e);
    // Graceful degradation - audio plays without captions
    this.captionElement.textContent = '';
});
```

### Scenario 3: Track Not Supported

```javascript
if (!this.trackElement || !this.trackElement.track) {
    console.warn('[AudioPlayer] Browser does not support text tracks');
    // Fallback to manual caption handling (if needed)
}
```

---

## Browser Compatibility

### Support Status
- ✅ Chrome/Edge (Chromium): Full support
- ✅ Firefox: Full support
- ✅ Safari: Full support
- ✅ Mobile browsers: Full support

**Source**: https://caniuse.com/webvtt

### Polyfill Not Required
Native `<track>` element has >95% browser support. No polyfill needed.

---

## Testing

### Test 1: VTT Loads Successfully

```javascript
// Manual test in browser console
const track = document.getElementById('audio-track').track;
console.log('Track state:', track.readyState);
console.log('Total cues:', track.cues.length);
console.log('First cue:', track.cues[0].text);

// Expected:
// Track state: 2 (LOADED)
// Total cues: 13
// First cue: "Myth 1. Ideas come in a flash."
```

### Test 2: Active Cues Update

```javascript
// Play audio and check active cues at different times
audio.currentTime = 1.0;  // Should activate first cue
console.log('Active:', track.activeCues[0].text);

audio.currentTime = 6.0;  // Should activate second cue
console.log('Active:', track.activeCues[0].text);
```

### Test 3: No VTT Available

```javascript
// Document without VTT
// Expected: trackElement.src === ''
// Audio plays without captions
// No console errors
```

---

## Comparison: Before vs After

### Before (Manual Parsing)
```javascript
// Fetch markdown
const markdown = await fetch(`/documents/${docId}/markdown`);
const text = await markdown.text();

// Parse with regex
const segments = this.parseMarkdownSegments(text);

// Manual time checking in timeupdate
const activeSegment = segments.find(seg =>
    currentTime >= seg.startTime && currentTime < seg.endTime
);

// ~50 lines of parsing code
```

### After (Native Track)
```javascript
// Set track source
trackElement.src = `/documents/${docId}/vtt`;

// Browser handles everything
trackElement.track.addEventListener('cuechange', () => {
    if (track.activeCues.length > 0) {
        captionElement.textContent = track.activeCues[0].text;
    }
});

// ~5 lines of code
```

**Code Reduction**: ~45 lines removed ✅

---

## Integration with Caption Display

### Caption Overlay Element

**HTML** (details.html):
```html
<div id="album-art-container" class="album-art-container">
    <img id="album-art" class="album-art" src="" alt="Album art">
    <div id="current-caption" class="current-caption"></div>
</div>
```

### Caption Update via cuechange

**JavaScript**:
```javascript
handleCueChange() {
    const track = this.trackElement.track;

    if (track.activeCues && track.activeCues.length > 0) {
        const cue = track.activeCues[0];
        this.captionElement.textContent = cue.text;
    } else {
        this.captionElement.textContent = '';
    }
}
```

**CSS** (details.css - already exists):
```css
.current-caption {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.55);
    color: rgb(22, 20, 20);
    /* ... existing styles */
}
```

---

## Success Criteria

### Implementation Success
- [ ] Track element src set to `/documents/{doc_id}/vtt`
- [ ] Track loads when VTT available
- [ ] cuechange event listener registered
- [ ] Caption updates via activeCues
- [ ] Graceful fallback when VTT unavailable

### User Experience Success
- [ ] Captions appear synchronized with audio
- [ ] Caption text matches VTT file
- [ ] No lag or flash of wrong caption
- [ ] Captions clear when no active cue
- [ ] Audio plays normally when no VTT

### Code Quality Success
- [ ] ~45 lines of parsing code removed
- [ ] No regex markdown parsing
- [ ] Browser-native API used
- [ ] Error handling comprehensive

---

## Dependencies

**Depends On**:
- IC-004 (API Response Contract) - VTT endpoint available
- Existing HTML structure (details.html)
- Existing CSS (details.css)

**Consumed By**:
- IC-006 (Caption Display Contract) - cuechange handling
- Frontend Implementation Agent (Wave 2)

---

## Review Checklist

- [x] HTML structure documented
- [x] JavaScript integration pattern clear
- [x] Event handling specified
- [x] Error scenarios covered
- [x] Browser compatibility confirmed
- [x] Testing approach defined
- [x] Code reduction quantified
- [x] Success criteria measurable

---

**Contract Status**: ✅ Ready for Implementation
