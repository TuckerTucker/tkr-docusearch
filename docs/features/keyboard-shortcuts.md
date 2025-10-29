# Keyboard Shortcuts Reference

**Agent 14: Testing & Documentation**
**Wave 3 - BBox Overlay React Implementation**

## BoundingBox Overlay Keyboard Navigation

### Basic Navigation

| Key | Action | Description |
|-----|--------|-------------|
| `Tab` | Focus Next | Move focus to next bounding box in document order |
| `Shift + Tab` | Focus Previous | Move focus to previous bounding box |
| `Enter` | Activate | Activate focused bbox and scroll to content |
| `Space` | Activate | Alternative activation key (same as Enter) |
| `Esc` | Clear | Clear active selection and return to default state |

### Advanced Navigation

| Key Combination | Action | Description |
|----------------|--------|-------------|
| `Tab` (multiple) | Traverse All | Cycle through all interactive elements including bboxes |
| `Home` | First Element | Jump to first bbox on page (if implemented) |
| `End` | Last Element | Jump to last bbox on page (if implemented) |

## Document Navigation

### Page Controls

| Key | Action | Description |
|-----|--------|-------------|
| `←` | Previous Page | Navigate to previous document page |
| `→` | Next Page | Navigate to next document page |
| `↑` | Scroll Up | Scroll content area up |
| `↓` | Scroll Down | Scroll content area down |
| `Page Up` | Page Up | Scroll one viewport up |
| `Page Down` | Page Down | Scroll one viewport down |

## Screen Reader Shortcuts

### JAWS

| Key | Action |
|-----|--------|
| `Insert + F3` | Elements List |
| `Tab` | Next Interactive Element |
| `B` | Next Button (bboxes have button role) |

### NVDA

| Key | Action |
|-----|--------|
| `Insert + F7` | Elements List |
| `Tab` | Next Interactive Element |
| `B` | Next Button |

### VoiceOver (macOS)

| Key | Action |
|-----|--------|
| `VO + U` | Rotor (navigate by element type) |
| `Tab` | Next Interactive Element |
| `VO + Space` | Activate Element |

### VoiceOver (iOS)

| Gesture | Action |
|---------|--------|
| Swipe Right | Next Element |
| Swipe Left | Previous Element |
| Double Tap | Activate Element |
| Two-finger Swipe Up | Read from Top |

## Browser Navigation

| Key | Action | Description |
|-----|--------|-------------|
| `Ctrl/Cmd + L` | Address Bar | Focus URL bar for direct chunk navigation |
| `Alt + ←` | Back | Browser back (works with history) |
| `Alt + →` | Forward | Browser forward |
| `Ctrl/Cmd + R` | Reload | Refresh page (preserves chunk parameter) |

## Tips for Keyboard Users

### Efficient Navigation

1. **Use Tab Wisely**: Tab through bboxes, but use mouse/trackpad for distant jumps
2. **Bookmark Shortcuts**: Use browser bookmarks with chunk URLs for frequently accessed sections
3. **Learn Your Screen Reader**: Master your screen reader's navigation shortcuts
4. **Use Enter/Space Interchangeably**: Both work the same for activation

### Accessibility Features

✅ **Visible Focus**: All focused elements have clear outlines
✅ **Logical Order**: Tab order follows document structure
✅ **Skip Links**: Use heading navigation to skip to main content
✅ **Escape Hatches**: Esc key always clears selections

## Keyboard-Only Workflow Example

**Goal**: Navigate to a specific section in a multi-page document

1. `Ctrl/Cmd + L` - Focus address bar
2. Type: `/details/doc-123?chunk=heading-5`
3. `Enter` - Navigate to document
4. `Tab` (multiple times) - Focus desired bbox
5. `Enter` - Activate and scroll to content
6. `↓` or `Page Down` - Read content
7. `Esc` - Clear selection when done

## Touch Gestures (Mobile)

| Gesture | Action | Description |
|---------|--------|-------------|
| Tap | Activate | Tap bbox to activate and scroll |
| Long Press | Context Menu | Long press for additional options |
| Swipe Up/Down | Scroll | Scroll content area |
| Pinch | Zoom | Zoom document image |

## Customization

### Browser Extensions

Some keyboard shortcuts may conflict with browser extensions:
- Vimium: May override arrow keys
- Tab Manager Plus: May override Tab behavior
- Screen readers: May override multiple keys

**Solution**: Temporarily disable extensions or customize their shortcuts.

### Operating System

Operating system shortcuts take precedence:
- Windows: Win key combinations
- macOS: Cmd key combinations
- Linux: Super key combinations

## Accessibility Settings

### Reduced Motion

Users with `prefers-reduced-motion` enabled experience:
- Instant scrolling (no animation)
- All keyboard shortcuts work identically
- No functional differences

### High Contrast Mode

In high contrast mode:
- Focus indicators are enhanced
- Bbox strokes are more prominent
- All shortcuts work the same

## Troubleshooting

### Shortcuts Not Working

**Problem**: Keyboard shortcuts don't respond

**Solutions**:
1. Ensure bbox overlay has focus (click on it first)
2. Check for browser extension conflicts
3. Verify JavaScript is enabled
4. Try refreshing the page

### Focus Not Visible

**Problem**: Can't see which element is focused

**Solutions**:
1. Check browser zoom level (100% recommended)
2. Verify CSS is loaded correctly
3. Try increasing browser contrast settings

### Screen Reader Not Announcing

**Problem**: Screen reader doesn't announce bbox information

**Solutions**:
1. Verify ARIA attributes in DOM (inspect element)
2. Update screen reader to latest version
3. Try different screen reader mode (virtual/focus)

## Related Documentation

- [User Guide](./bbox-overlay-user-guide.md)
- [Accessibility Features](../api/bbox-overlay-api.md#accessibility)
- [Troubleshooting Guide](./troubleshooting.md)

## Feedback

Have suggestions for keyboard shortcuts? File an issue on GitHub with:
- Your use case
- Current workflow pain points
- Proposed shortcut combinations
- Potential conflicts with existing shortcuts
