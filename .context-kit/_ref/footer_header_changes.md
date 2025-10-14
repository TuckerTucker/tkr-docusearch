 Based on my analysis of the codebase, here's the optimally
  ordered task list:

  Current Structure Analysis

  Header (src/frontend/index.html:12-57):
  - Title "DocuSearch" + subtitle "Document Library"
  - Navigation buttons: "Library" and "Search"
  - Theme toggle button (with sun/moon icons)
  - WebSocket connection status indicator

  Footer (src/frontend/index.html:76-85):
  - Basic text and placeholder status

  Implementation Tasks (Ordered by Dependencies)

  1. Remove navigation buttons from header
    - Delete the <nav class="header__nav"> section (lines 19-26)
    - This is independent and can be done first
  2. Remove 'Document Library' subtitle from header
    - Delete the <span class="header__subtitle"> (line 16)
    - Simplifies header to just "DocuSearch" title
  3. Move theme toggle button to footer
    - Extract <button id="theme-toggle"> from header (lines 29-48)
    - Insert into footer structure
    - No JS changes needed (theme-toggle.js uses ID selector)
  4. Move websocket connection status to footer
    - Extract <div class="header__status"> section (lines 51-55)
    - Insert into footer alongside theme toggle
    - Verify library-manager.js still updates connection status by
  ID
  5. Update footer structure
    - Create new footer layout with theme toggle + websocket status
    - Maintain semantic HTML and accessibility attributes
  6. Update CSS styles
    - Read src/frontend/styles.css
    - Adjust header styles (simpler layout without
  nav/actions/status)
    - Add footer styles for new control placement
    - Ensure responsive design and proper spacing
  7. Test UI changes
    - Start services (./scripts/start-all.sh)
    - Verify header appearance (title only)
    - Verify footer controls (theme toggle works, status updates)
    - Check accessibility and responsive behavior

  Key Benefits of This Order

  - Risk reduction: Remove elements before restructuring (simpler
  rollback)
  - Minimal context switching: All header work, then footer work,
  then styling
  - Testability: Each step has clear visual confirmation
  - No breaking changes: Theme toggle and websocket client use ID
  selectors, so moving elements won't break functionality