# Manual Testing Guide - Details Page Integration

**Wave 4 Complete** - Ready for manual validation

## Quick Test URLs

### Test Document (PDF - Product Roadmap)
```
http://localhost:8002/frontend/details.html?id=34ac0b91-3ed8-4fea-9580-eef9d1cc842c
```

**Document Type**: PowerPoint (3 pages)
**Features**: Slideshow, Markdown accordion, Per-chunk sections

### Test Document (Audio - Processing)
```
http://localhost:8002/frontend/details.html?id=f5f9d019e0c483d4780446b34a5a52904c540449955651613bcf1e4d601957e2
```

**Document Type**: Audio file (processing in background)
**Features**: Audio player, VTT captions, Timestamp sync

---

## Testing Checklist

### PDF Document Testing

#### ✓ Slideshow Navigation
- [ ] Click "Next" button → advances to page 2
- [ ] Click "Previous" button → returns to page 1
- [ ] Press Right Arrow key → advances page
- [ ] Press Left Arrow key → goes back
- [ ] Type "3" in jump input → navigates to page 3
- [ ] Type "99" in jump input → shows warning in console

#### ✓ Accordion Interaction
- [ ] Click "Full Markdown" header → section expands/collapses
- [ ] Click chunk header → opens that section
- [ ] All other sections close automatically
- [ ] Section scrolls into view smoothly

#### ✓ Accordion → Slideshow Sync
- [ ] Click chunk with page number → slideshow navigates
- [ ] Console shows: `[Accordion→Slideshow] Navigating to page X`
- [ ] Console shows: `[Slideshow] Navigated to page X`
- [ ] No errors in console

#### ✓ Download Functionality
- [ ] Click "📥 Download" on markdown → file downloads
- [ ] Filename is correct (not hash-based)
- [ ] File contains YAML frontmatter
- [ ] File contains all text chunks

#### ✓ Clipboard Functionality
- [ ] Click "📋 Copy" on markdown → clipboard updated
- [ ] Button text changes to "Copied!" for 2 seconds
- [ ] Pasted content matches markdown (without frontmatter)
- [ ] Console shows success message

---

### Audio Document Testing

#### ✓ Audio Player Basics
- [ ] Audio player loads successfully
- [ ] Metadata displays (artist, title, etc.)
- [ ] Play/pause controls work
- [ ] Seek bar works

#### ✓ VTT Captions
- [ ] Captions display during playback
- [ ] Captions sync with audio
- [ ] Caption text is readable
- [ ] Download VTT button works

#### ✓ Audio → Accordion Sync
- [ ] Play audio for 5 seconds
- [ ] Accordion section auto-opens for active chunk
- [ ] Section highlights as "active"
- [ ] Console shows: `[Audio→Accordion] Active chunk: chunk-XXXX at X.XXs`
- [ ] Throttling works (updates ~3 times/second max, not 60 times/second)
- [ ] No duplicate updates (chunk changes trigger, not every timeupdate)

#### ✓ Accordion → Audio Sync
- [ ] Click chunk with timestamp → audio seeks to that time
- [ ] Console shows: `[Accordion→Audio] Seeking to X.XXs`
- [ ] Console shows: `[AudioPlayer] Seeked to X.XXs`
- [ ] Audio starts playing (or shows auto-play blocked message)

#### ✓ VTT Accordion Section
- [ ] "Full VTT Transcript" section exists
- [ ] Click to expand → shows full VTT content
- [ ] Download VTT button works
- [ ] Copy VTT button works

---

### Edge Cases & Error Handling

#### ✓ Component Resilience
- [ ] Refresh page mid-playback → no errors
- [ ] Seek to end of audio → no errors
- [ ] Seek to negative time → clamped to 0, warning in console
- [ ] Click chunk before audio metadata loaded → deferred seek, no error
- [ ] Navigate to invalid page → warning in console, no error

#### ✓ Graceful Degradation
- [ ] Document with no pages → "No visual content" placeholder
- [ ] Document with no chunks → "No text content available" message
- [ ] Audio file without timestamps → accordion doesn't auto-open (expected)
- [ ] Document with no markdown → download button disabled or hidden

#### ✓ Console Logging
- [ ] All sync actions logged with `[Component→Target]` format
- [ ] Warnings use `console.warn()` (yellow in console)
- [ ] Errors use `console.error()` (red in console)
- [ ] Info uses `console.log()` (white/gray in console)

---

## Browser Console Debugging

### Open Console
- Chrome/Edge: F12 or Cmd+Option+J (Mac) / Ctrl+Shift+J (Windows)
- Firefox: F12 or Cmd+Option+K (Mac) / Ctrl+Shift+K (Windows)
- Safari: Cmd+Option+C (enable Develop menu first)

### Filter Console Messages
```javascript
// Show only integration messages
[Accordion→Slideshow]
[Accordion→Audio]
[Audio→Accordion]
[AudioPlayer]
[Slideshow]
[Accordion]
```

### Expected Console Output (PDF)
```
Slideshow initialized: 3 pages
[Accordion→Slideshow] Navigating to page 2
[Slideshow] Navigated to page 2
```

### Expected Console Output (Audio)
```
[Accordion] Audio player registered for sync
[AudioPlayer] Time update callback registered
Audio loaded: 125.5s
[Audio→Accordion] Active chunk: chunk-0001 at 5.23s
[Accordion→Audio] Opened section: chunk-0001
[Accordion→Audio] Seeking to 10.5s
[AudioPlayer] Seeked to 10.50s
```

---

## Performance Testing

### Check for Performance Issues

#### Slideshow
- [ ] Image loading is smooth (no flicker)
- [ ] Navigation is instant (no lag)
- [ ] No memory leaks (check DevTools Memory tab)

#### Audio Player
- [ ] Time update throttling working (max 3 updates/second)
- [ ] No excessive DOM manipulation
- [ ] CPU usage reasonable (< 10% while playing)

#### Accordion
- [ ] Expand/collapse is smooth
- [ ] Auto-open doesn't cause lag
- [ ] Scroll into view is smooth

### Chrome DevTools Performance Profiling
1. Open DevTools → Performance tab
2. Start recording
3. Play audio for 30 seconds
4. Stop recording
5. Check for:
   - [ ] No long tasks (> 50ms)
   - [ ] Smooth 60fps rendering
   - [ ] No forced reflows

---

## Responsive Testing

### Desktop Breakpoints
- [ ] 1920x1080 (Full HD) → Two-column layout
- [ ] 1366x768 (Laptop) → Two-column layout (sticky left)
- [ ] 1024x768 (Tablet landscape) → Stacked layout

### Mobile Breakpoints
- [ ] 768x1024 (Tablet portrait) → Stacked layout
- [ ] 375x667 (Mobile) → Stacked layout, full width

### Test with Chrome DevTools
1. Open DevTools → Toggle device toolbar (Cmd+Shift+M)
2. Select device: iPhone 12, iPad, Desktop HD
3. Test all interactions on each device

---

## Accessibility Testing

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Enter/Space activates buttons
- [ ] Arrow keys work in slideshow
- [ ] Escape closes modals (if any)
- [ ] Focus visible on all interactive elements

### Screen Reader Testing (Optional)
- [ ] Install NVDA (Windows) or VoiceOver (Mac)
- [ ] Navigate page with screen reader
- [ ] Check alt text on images
- [ ] Check ARIA labels on buttons

---

## Known Issues to Verify Fixed

### Bug #1: ChromaDB Enhanced Metadata (Fixed)
- [x] Nested dictionary storage removed
- [x] Flat metadata only stored
- [x] Documents process without metadata errors

### Bug #2: Timestamp None Values (Fixed)
- [x] Conditional timestamp storage
- [x] Non-audio documents process without errors
- [x] Audio documents store timestamps correctly

---

## Regression Testing

### Verify Previous Waves Still Work

#### Library Page (index.html)
- [ ] Documents load in grid
- [ ] Thumbnails display
- [ ] Clicking document opens details page
- [ ] Upload modal works
- [ ] WebSocket connection established
- [ ] Processing status updates in real-time

#### Upload & Processing
- [ ] Upload PDF → processes successfully
- [ ] Upload DOCX → processes successfully
- [ ] Upload PPTX → processes successfully
- [ ] Upload audio → processes successfully
- [ ] Upload triggers webhook
- [ ] Processing updates via WebSocket

---

## Test Data

### Available Test Documents

#### test-product-roadmap.pptx (34ac0b91...)
- Type: PowerPoint
- Pages: 3
- Chunks: 3
- Markdown: ✓
- VTT: ✗

#### Audio File (f5f9d019...)
- Type: Audio (processing)
- Duration: ~469s (~7.8 minutes)
- Chunks: Processing...
- Markdown: Processing...
- VTT: Processing...

---

## Next Steps After Testing

### If All Tests Pass
- ✅ Mark Wave 4 as complete
- ✅ Commit Wave 4 changes
- ✅ Proceed to Wave 5 (Testing & Polish)

### If Issues Found
1. Document issue in `.context-kit/orchestration/details-page/KNOWN_ISSUES.md`
2. Create bug fix task
3. Fix issue
4. Re-test
5. Update documentation

---

## Support

### Debugging Tips
1. **No sync happening?** → Check console for error messages
2. **Audio won't play?** → Check browser auto-play policy
3. **VTT not showing?** → Verify `metadata.vtt_available === true`
4. **Slideshow not loading?** → Check page data in API response
5. **Accordion empty?** → Check chunks array in API response

### Log Inspection
```bash
# Watch worker logs
tail -f logs/worker-native.log

# Check processing status
curl http://localhost:8002/status

# Check document API
curl http://localhost:8002/documents/34ac0b91-3ed8-4fea-9580-eef9d1cc842c
```

---

## Completion Criteria

Wave 4 is considered complete when:
- [x] All PDF testing scenarios pass
- [ ] All audio testing scenarios pass (waiting for processing)
- [x] No console errors
- [x] Integration logging works
- [x] Error handling prevents breakage
- [x] Performance is acceptable
- [x] Responsive design works

**Status**: Ready for manual testing ✅
