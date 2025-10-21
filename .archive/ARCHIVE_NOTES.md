# Archive Notes

## Purpose

This directory contains archived code that has been superseded but is preserved for historical reference and potential rollback.

## Archived Components

### legacy-frontend-2025-10-20

**Original Location**: `src/frontend/`

**Reason for Archival**: Replaced by React 19 frontend

**Date Archived**: 2025-10-20

**Description**:
Legacy static HTML/vanilla JavaScript UI that was served from the Worker API at port 8002. This UI has been completely replaced by the modern React 19 frontend located in `frontend/` and served on port 3000.

**What was in this directory**:
- Static HTML files: `index.html`, `details.html`, `research.html`
- Vanilla JavaScript modules: `library-manager.js`, `document-card.js`, `filter-bar.js`, etc.
- CSS stylesheets: `styles.css`
- Accessibility and performance subdirectories

**Migration Path**:
All user-facing functionality has been migrated to the React frontend:
- Document library view → React `LibraryView` component
- Document details → React `DocumentDetailView` component
- Research interface → React `ResearchView` component
- File uploads → React integration with Copyparty API

**Backend Changes**:
The Worker API no longer serves static files. Lines 138-144 in `src/processing/worker_webhook.py` that mounted `/frontend` static files were removed.

**Rollback Instructions** (if needed):
```bash
# Restore legacy frontend
cp -r .archive/legacy-frontend-2025-10-20/frontend src/

# Re-enable static file serving in worker_webhook.py
# Uncomment lines 138-144:
# FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
# if FRONTEND_DIR.exists():
#     app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
```

**Migration Completion**:
- ✅ React frontend fully functional on port 3000
- ✅ All legacy UI features migrated
- ✅ Documentation updated to reflect React-only architecture
- ✅ Worker API static file serving removed

**Safe to Delete**: After 6 months (June 2025) if no rollback needed
