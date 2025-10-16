# IC-008: Deprecation Contract

**Version**: 1.0
**Status**: ✅ Approved
**Author**: Frontend Specification Agent
**Reviewers**: Frontend Implementation Agent
**Date**: 2025-10-16

---

## Overview

Defines what code will be removed, when it will be removed, and how to ensure safe deprecation without breaking existing functionality. Provides a clear migration path from markdown parsing to VTT-based captions.

---

## Deprecation Timeline

### Wave 2: Implementation
- **Action**: Implement new VTT-based code alongside existing code
- **Status**: Dual implementation (new + old coexist)
- **Risk**: Zero (fallback to old code if new fails)

### Wave 3: Validation
- **Action**: Test new implementation thoroughly
- **Status**: Validate VTT approach works correctly
- **Risk**: Low (testing phase, can rollback)

### Wave 3: Removal (After Validation Passes)
- **Action**: Remove deprecated code
- **Status**: Old code deleted
- **Risk**: Minimal (validated in testing)

**Rule**: Do NOT remove old code until Wave 3 validation complete ✅

---

## Code to Deprecate

### File 1: audio-player.js

#### Variables to Remove (Lines ~32-36)
```javascript
// REMOVE
this.lastCaptionTime = -1;
this.segments = [];
this.markdownContent = null;
```

**Reason**: No longer needed with VTT cuechange events

---

#### Methods to Remove

##### Method 1: fetchMarkdown() (Lines ~85-94)
```javascript
// REMOVE entire method
async fetchMarkdown() {
    try {
        const response = await fetch(`/documents/${this.docId}/markdown`);
        if (response.ok) {
            this.markdownContent = await response.text();
        }
    } catch (err) {
        console.error('[AudioPlayer] Error fetching markdown:', err);
    }
}
```

**Reason**: Markdown no longer needed for captions (VTT provides captions)

---

##### Method 2: parseMarkdownSegments() (Lines ~96-135)
```javascript
// REMOVE entire method (~40 lines)
parseMarkdownSegments() {
    if (!this.markdownContent) {
        return [];
    }

    const segments = [];
    const timeRegex = /\[time:\s*([\d.]+)-([\d.]+)\]/g;
    // ... complex regex parsing ...
    return segments;
}
```

**Reason**: Timestamps now come from VTT track, not markdown

---

#### Logic to Remove from init() (Lines ~45-48)
```javascript
// REMOVE these lines
await this.fetchMarkdown();
this.segments = this.parseMarkdownSegments();
```

**Reason**: No longer fetching/parsing markdown

---

#### Logic to Refactor in handleTimeUpdate()

**Before** (Lines ~202-226):
```javascript
handleTimeUpdate() {
    const currentTime = this.audioElement.currentTime;

    // REMOVE: Caption logic using segments
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

    // KEEP: Accordion sync logic (below this)
    // ...
}
```

**After**:
```javascript
handleTimeUpdate() {
    // Caption display moved to handleCueChange()
    // This method now only handles accordion sync

    const currentTime = this.audioElement.currentTime;
    const now = Date.now();

    // Throttle accordion updates
    if (now - this.lastAccordionUpdate < 300) {
        return;
    }
    this.lastAccordionUpdate = now;

    // KEEP: Accordion sync logic
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

**Total Lines Removed from audio-player.js**: ~80 lines

---

### File 2: accordion.js

#### Variables to Remove (Lines ~23-24)
```javascript
// REMOVE
this.markdownContent = null;
```

**Reason**: No longer parsing markdown for full text

---

#### Methods to Remove

##### Method 1: fetchMarkdown() (Lines ~49-60)
```javascript
// REMOVE entire method
async fetchMarkdown() {
    try {
        const response = await fetch(`/documents/${this.docId}/markdown`);
        if (response.ok) {
            this.markdownContent = await response.text();
            console.log('Markdown content fetched');
        } else {
            console.warn('Failed to fetch markdown:', response.status);
        }
    } catch (err) {
        console.error('Error fetching markdown:', err);
    }
}
```

**Reason**: Full text now comes from chunk.text_content via API

---

##### Method 2: parseMarkdownSegments() (Lines ~411-454)
```javascript
// REMOVE entire method (~44 lines)
parseMarkdownSegments() {
    if (!this.markdownContent) {
        return [];
    }

    const segments = [];
    const timeRegex = /\[time:\s*([\d.]+)-([\d.]+)\]/g;
    // ... complex regex parsing ...
    return segments;
}
```

**Reason**: Timestamps and text now from API chunks

---

#### Logic to Remove from init() (Lines ~32-41)
```javascript
// REMOVE markdown fetching
if (this.metadata.markdown_available) {
    await this.fetchMarkdown();
}
```

**Reason**: Markdown no longer needed for accordion sections

---

#### Logic to Refactor in addChunkSections()

**Before** (Lines ~117-164):
```javascript
addChunkSections() {
    // Parse markdown into time-stamped segments
    const segments = this.parseMarkdownSegments();

    if (segments.length > 0) {
        // Use parsed segments from markdown (full text)
        segments.forEach((segment, index) => { /* ... */ });
    } else {
        // Fallback to using chunks
        this.chunks.forEach((chunk, index) => { /* ... */ });
    }
}
```

**After**:
```javascript
addChunkSections() {
    // Use chunks directly from API (text already full and cleaned)
    this.chunks.forEach((chunk, index) => {
        const sectionTitle = this.getChunkTitle(chunk, index);
        const section = this.createSection({
            id: chunk.chunk_id,
            title: sectionTitle,
            content: chunk.text_content,  // Full, cleaned text
            timestamp: chunk.start_time !== null ? {
                start: chunk.start_time,
                end: chunk.end_time
            } : null,
            // ...
        });
        this.container.appendChild(section);
    });
}
```

---

#### Logic to Simplify in openSection()

**Before** (Lines ~317-387):
```javascript
openSection(chunkOrTimestamp) {
    // Complex logic:
    // 1. Try to find by chunk_id
    // 2. If not found, parse timestamp from text
    // 3. Match by comparing timestamps
    // (~70 lines of complex logic)
}
```

**After**:
```javascript
openSection(chunk) {
    // Simple direct lookup by chunk_id
    const section = this.container.querySelector(
        `[data-section-id="${chunk.chunk_id}"]`
    );
    // Open section (~20 lines)
}
```

**Total Lines Removed from accordion.js**: ~100 lines

---

## Deprecation Summary

| File | Lines Removed | Methods Removed | Variables Removed |
|------|---------------|-----------------|-------------------|
| audio-player.js | ~80 | fetchMarkdown(), parseMarkdownSegments() | lastCaptionTime, segments, markdownContent |
| accordion.js | ~100 | fetchMarkdown(), parseMarkdownSegments() | markdownContent |
| **Total** | **~180 lines** | **4 methods** | **4 variables** |

---

## Migration Safety Checklist

### Pre-Removal Validation

Before removing deprecated code, verify:

- [ ] **Wave 2 complete**: New implementation working
- [ ] **Gate 2 passed**: All tests passing
- [ ] **Wave 3 validation**: Integration tests passing
- [ ] **Manual testing**: Browser testing successful
- [ ] **Audio with timestamps**: Captions display correctly via VTT
- [ ] **Audio without timestamps**: Graceful degradation works
- [ ] **Accordion sections**: Display full text without parsing
- [ ] **Click-to-seek**: Works with new chunk timestamps
- [ ] **Backward compatibility**: Old documents still work
- [ ] **No console errors**: Clean browser console
- [ ] **Performance**: Caption sync <50ms
- [ ] **All browsers tested**: Chrome, Firefox, Safari

**Rule**: ALL checkboxes must be checked before removal

---

## Rollback Procedure

If new implementation fails in Wave 3:

### Step 1: Revert Frontend Changes
```bash
# Revert audio-player.js changes
git checkout HEAD -- src/frontend/audio-player.js

# Revert accordion.js changes
git checkout HEAD -- src/frontend/accordion.js
```

### Step 2: Keep Backend Changes
- Backend timestamp extraction can remain
- Improves data structure even if frontend doesn't use yet
- Allows retry of frontend integration later

### Step 3: Document Issues
- Update issues.md with failure details
- Analyze root cause
- Plan fixes before retry

---

## Backward Compatibility Strategy

### Scenario 1: Old Documents (Processed Before Fix)

**Data State**:
- Chunks have `null` timestamps
- Text may contain `[time: X-Y]` markers (if audio)
- No VTT file exists

**Frontend Behavior**:
```javascript
// New code handles null gracefully
if (!this.metadata.vtt_available) {
    // Don't set track source
    this.trackElement.src = '';
    // Captions disabled, audio plays normally
}

if (chunk.start_time !== null) {
    // Use timestamp
} else {
    // Display without timestamp
}
```

**Result**: Old documents continue to work, just without new features

---

### Scenario 2: Mixed Documents

**Data State**: Some documents with timestamps, some without

**Frontend Behavior**:
```javascript
// Check per-document
if (doc.metadata.vtt_available) {
    // Load VTT track
} else {
    // No captions
}

// Check per-chunk
if (chunk.start_time !== null) {
    // Show timestamp in title
} else {
    // Simple title
}
```

**Result**: Each document gets appropriate UI based on data

---

## Documentation Updates

### Files to Update After Deprecation

1. **src/frontend/README.md** (if exists)
   - Update audio player documentation
   - Document VTT-based architecture
   - Remove markdown parsing references

2. **Code Comments**
   - Update JSDoc comments in audio-player.js
   - Update JSDoc comments in accordion.js
   - Document new VTT approach

3. **CHANGELOG.md** (if exists)
   - Document breaking change (markdown parsing removed)
   - Note backward compatibility strategy

---

## External Dependencies

### Check for External Usage

Before removal, verify no external code depends on:

```javascript
// These methods will be removed
audioPlayer.fetchMarkdown()
audioPlayer.parseMarkdownSegments()
accordion.fetchMarkdown()
accordion.parseMarkdownSegments()
```

**Action**: Search codebase for usage:
```bash
grep -r "fetchMarkdown" src/
grep -r "parseMarkdownSegments" src/
```

**Expected**: No results (these are internal methods)

---

## Success Criteria

### Safe Deprecation
- [ ] No code removed until Wave 3 validation complete
- [ ] All pre-removal checklist items verified
- [ ] Backward compatibility tested
- [ ] No external dependencies on deprecated code

### Clean Codebase
- [ ] ~180 lines of code removed
- [ ] 4 deprecated methods removed
- [ ] 4 deprecated variables removed
- [ ] No orphaned comments or imports

### Documentation Updated
- [ ] Comments reflect new architecture
- [ ] CHANGELOG updated (if exists)
- [ ] README updated (if exists)

---

## Timeline

```
Wave 2: Implementation (3-4 hours)
    ├─→ New code added
    └─→ Old code remains (dual implementation)

Wave 3: Validation (3-4 hours)
    ├─→ Integration tests
    ├─→ Manual testing
    ├─→ Performance validation
    └─→ Gate 3 approval

Wave 3: Removal (30 minutes)
    ├─→ Remove deprecated methods
    ├─→ Remove deprecated variables
    ├─→ Update comments
    └─→ Final validation
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking old documents | Low | Medium | Backward compatibility checks |
| Breaking external code | Very Low | High | Grep for usage |
| VTT fails to load | Low | Medium | Error handling + graceful degradation |
| Caption sync issues | Low | Medium | Wave 3 validation |
| Rollback needed | Very Low | Medium | Git revert procedure ready |

**Overall Risk**: Low ✅

---

## Dependencies

**Depends On**:
- All other contracts (IC-001 through IC-007)
- Wave 2 implementation complete
- Wave 3 validation passing

**Consumed By**:
- Frontend Implementation Agent (Wave 2)
- Integration Testing Agent (Wave 3)

---

## Review Checklist

- [x] Deprecated code clearly identified
- [x] Removal timeline defined
- [x] Safety checklist comprehensive
- [x] Rollback procedure documented
- [x] Backward compatibility strategy clear
- [x] External dependency check included
- [x] Documentation updates specified
- [x] Risk assessment complete

---

**Contract Status**: ✅ Ready for Implementation

**IMPORTANT**: Do NOT remove any code until Gate 3 passes! ⚠️
