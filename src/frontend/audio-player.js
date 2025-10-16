/**
 * Audio Player Component
 *
 * HTML5 audio player with VTT caption support and sync with accordion.
 * Auto-opens accordion sections based on current playback time.
 *
 * Wave 3 - Frontend Component
 * Wave 5 - Album Art Support
 */

// Default album art SVG (gray microphone icon) as data URI
const DEFAULT_ALBUM_ART_SVG = 'data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB2aWV3Qm94PSIwIDAgNTEyIDUxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KIDxyZWN0IHg9Ii01MS4yIiB5PSItNTEuMiIgd2lkdGg9IjYxNC40IiBoZWlnaHQ9IjYxNC40IiBmaWxsPSIjNjc2NzY3Ii8+CiA8cGF0aCBkPSJtMjMyLjgyIDIwNi4xNWMtMS44MDA4IDAtMy40Mzc1LTAuNzQyMTktNC42MzY3LTEuOTI1OC0xLjE4MzYtMS4xODM2LTEuOTI1OC0yLjgyMDMtMS45MjU4LTQuNjM2N3YtMzEuMjczYzAtMS44MDA4IDAuNzQyMTktMy40Mzc1IDEuOTI1OC00LjYzNjcgMS4xODM2LTEuMTgzNiAyLjgyMDMtMS45MjU4IDQuNjM2Ny0xLjkyNTggMS44MDA4IDAgMy40Mzc1IDAuNzQyMTkgNC42MzY3IDEuOTI1OCAxLjE4MzYgMS4xODM2IDEuOTI1OCAyLjgyMDMgMS45MjU4IDQuNjM2N3YzMS4yNzNjMCAxLjgwMDgtMC43NDIxOSAzLjQzNzUtMS45MjU4IDQuNjM2Ny0xLjE4MzYgMS4xODM2LTIuODIwMyAxLjkyNTgtNC42MzY3IDEuOTI1OHptLTUyLjM4MyA4NC4yMTFjMCAxLjE0NDUtMC45MzM1OSAyLjA3ODEtMi4wNzgxIDIuMDc4MWgtMjkuNTM1YzAuNjI4OTEgNy4xMDU1IDMuODA0NyAxMy41MTYgOC41ODk4IDE4LjMwMSA1LjM3ODkgNS4zNzg5IDEyLjc4NSA4LjcwMzEgMjAuOTM0IDguNzAzMSA4LjE0ODQgMCAxNS41NjYtMy4zMzU5IDIwLjkzNC04LjcwMzEgNS4zNzg5LTUuMzc4OSA4LjcwMzEtMTIuNzg1IDguNzAzMS0yMC45MzR2LTQxLjMzNmMwLTguMTQ4NC0zLjMzNTktMTUuNTY2LTguNzAzMS0yMC45MzQtNS4zNzg5LTUuMzc4OS0xMi43ODUtOC43MDMxLTIwLjkzNC04LjcwMzEtOC4xNDg0IDAtMTUuNTY2IDMuMzM1OS0yMC45MzQgOC43MDMxLTQuNzczNCA0Ljc3MzQtNy45MzM2IDExLjE0OC04LjU3ODEgMTguMjExaDI5LjUzNWMxLjE0NDUgMCAyLjA3ODEgMC45MzM1OSAyLjA3ODEgMi4wNzgxczAtMC45MzM1OS0yLjA3ODEgMi4wNzgxaC0yOS42NDh2MTAuMDM5aDI5LjY0OGMxLjE0NDUgMCAyLjA3ODEgMC45MzM1OSAyLjA3ODEgMi4wNzgxcy0wLjkzMzU5IDIuMDc4MS0yLjA3ODEgMi4wNzgxaC0yOS42NDh2MTAuMDM5aDI5LjY0OGMxLjE0NDUgMCAyLjA3ODEgMC45MzM1OSAyLjA3ODEgMi4wNzgxIDAgMS4xNDQ1LTAuOTMzNTkgMi4wNzgxLTIuMDc4MSAyLjA3ODFoLTI5LjY0OHYxMC4wMzloMjkuNjQ4YzEuMTQ0NSAwIDIuMDc4MSAwLjkzMzU5IDIuMDc4MSAyLjA3ODF6bTE5NC4xMS0xNTguMjVjLTIuMzc4OS0yLjM3ODktNS42NTYyLTMuODU1NS05LjI2OTUtMy44NTU1aC0xOTIuODljLTMuNjEzMyAwLTYuODkwNiAxLjQ3MjctOS4yNjk1IDMuODU1NS0yLjM3ODkgMi4zNzg5LTMuODU1NSA1LjY1NjItMy44NTU1IDkuMjY5NXY2OC43NDJjMCAxLjE0NDUgMC45MzM1OSAyLjA3ODEgMi4wNzgxIDIuMDc4MSAxLjE0NDUgMCAyLjA3ODEtMC45MzM1OSAyLjA3ODEtMi4wNzgxbC0wLjAxMTcxOC02OC43NDJjMC0yLjQ2ODggMS4wMDc4LTQuNzEwOSAyLjY0NDUtNi4zNDc3IDEuNjI1LTEuNjI1IDMuODc4OS0yLjY0NDUgNi4zNDc3LTIuNjQ0NWgxOTIuODhjMi40Njg4IDAgNC43MTA5IDEuMDA3OCA2LjM0NzcgMi42NDQ1IDEuNjI1IDEuNjI1IDIuNjQ0NSAzLjg3ODkgMi42NDQ1IDYuMzQ3N3Y4NC41MjdjMCAyLjQ2ODgtMS4wMDc4IDQuNzEwOS0yLjY0NDUgNi4zNDc3LTEuNjI1IDEuNjI1LTMuODc4OSAyLjY0NDUtNi4zNDc3IDIuNjQ0NWgtMTQ4LjIxYy0xLjE0NDUgMC0yLjA3ODEgMC45MzM1OS0yLjA3ODEgMi4wNzgxczAuOTMzNTkgMi4wNzgxIDIuMDc4MSAyLjA3ODFoMTQ4LjIxYzMuNjEzMyAwIDYuODkwNi0xLjQ3MjcgOS4yNjk1LTMuODU1NSAyLjM3ODktMi4zNzg5IDMuODU1NS01LjY1NjIgMy44NTU1LTkuMjY5NXYtODQuNTU1YzAtMy42MTMzLTEuNDcyNy02Ljg5MDYtMy44NTU1LTkuMjY5NXptLTE5MC4xOSA2Ny4yODFjMS44MDA4IDAgMy40Mzc1LTAuNzQyMTkgNC42MzY3LTEuOTI1OCAxLjE4MzYtMS4xODM2IDEuOTI1OC0yLjgyMDMgMS45MjU4LTQuNjM2N3YtMTcuNzQ2YzAtMS44MDA4LTAuNzQyMTktMy40Mzc1LTEuOTI1OC00LjYzNjctMS4xODM2LTEuMTgzNi0yLjgyMDMtMS45MjU4LTQuNjM2Ny0xLjkyNTgtMS44MDA4IDAtMy40Mzc1IDAuNzQyMTktNC42MzY3IDEuOTI1OC0xLjE4MzYgMS4xODM2LTEuOTI1OCAyLjgyMDMtMS45MjU4IDQuNjM2N3YxNy43NDZjMCAxLjgwMDggMC43NDIxOSAzLjQzNzUgMS45MjU4IDQuNjM2NyAxLjE4MzYgMS4xODM2IDIuODIwMyAxLjkyNTggNC42MzY3IDEuOTI1OHptMjkuMDIgMTAuMjI3YzEuMTgzNi0xLjE4MzYgMS45MjU4LTIuODIwMyAxLjkyNTgtNC42MzY3di00Mi4wODJjMC0xLjgwMDgtMC43NDIxOS0zLjQzNzUtMS45MjU4LTQuNjM2Ny0xLjE4MzYtMS4xODM2LTIuODIwMy0xLjkyNTgtNC42MzY3LTEuOTI1OC0xLjgwMDggMC0zLjQzNzUgMC43NDIxOS00LjYzNjcgMS45MjU4LTEuMTgzNiAxLjE4MzYtMS45MjU4IDIuODIwMy0xLjkyNTggNC42MzY3djQyLjA4MmMwIDEuODAwOCAwLjc0MjE5IDMuNDM3NSAxLjkyNTggNC42MzY3IDEuMTgzNiAxLjE4MzYgMi44MjAzIDEuOTI1OCA0LjYzNjcgMS45MjU4IDEuODAwOCAwIDMuNDM3NS0wLjc0MjE5IDQuNjM2Ny0xLjkyNTh6bTQ3Ljk4OCAwYzEuMTgzNi0xLjE4MzYgMS45MjU4LTIuODIwMyAxLjkyNTgtNC42MzY3di00Mi4wODJjMC0xLjgwMDgtMC43NDIxOS0zLjQzNzUtMS45MjU4LTQuNjM2Ny0xLjE4MzYtMS4xODM2LTIuODIwMy0xLjkyNTgtNC42MzY3LTEuOTI1OC0xLjgwMDggMC0zLjQzNzUgMC43NDIxOS00LjYzNjcgMS45MjU4LTEuMTgzNiAxLjE4MzYtMS45MjU4IDIuODIwMy0xLjkyNTggNC42MzY3djQyLjA4MmMwIDEuODAwOCAwLjc0MjE5IDMuNDM3NSAxLjkyNTggNC42MzY3IDEuMTgzNiAxLjE4MzYgMi44MjAzIDEuOTI1OCA0LjYzNjcgMS45MjU4IDEuODAwOCAwIDMuNDM3NS0wLjc0MjE5IDQuNjM2Ny0xLjkyNTh6bTcyLjc3My0xMS41MzljMS4xODM2LTEuMTgzNiAxLjkyNTgtMi44MjAzIDEuOTI1OC00LjYzNjd2LTE4Ljk4YzAtMS44MDA4LTAuNzQyMTktMy40Mzc1LTEuOTI1OC00LjYzNjctMS4xODM2LTEuMTgzNi0yLjgyMDMtMS45MjU4LTQuNjM2Ny0xLjkyNTgtMS44MDA4IDAtMy40Mzc1IDAuNzQyMTktNC42MzY3IDEuOTI1OC0xLjE4MzYgMS4xODM2LTEuOTI1OCAyLjgyMDMtMS45MjU4IDQuNjM2N3YxOC45OGMwIDEuODAwOCAwLjc0MjE5IDMuNDM3NSAxLjkyNTggNC42MzY3IDEuMTgzNiAxLjE4MzYgMi44MjAzIDEuOTI1OCA0LjYzNjcgMS45MjU4IDEuODAwOCAwIDMuNDM3NS0wLjc0MjE5IDQuNjM2Ny0xLjkyNTh6bS0yNC45MjYgMTIuMDI3YzEuMTgzNi0xLjE4MzYgMS45MjU4LTIuODIwMyAxLjkyNTgtNC42MzY3di00My4wNjJjMC0xLjgwMDgtMC43NDIxOS0zLjQzNzUtMS45MjU4LTQuNjM2Ny0xLjE4MzYtMS4xODM2LTIuODIwMy0xLjkyNTgtNC42MzY3LTEuOTI1OC0xLjgwMDggMC0zLjQzNzUgMC43NDIxOS00LjYzNjcgMS45MjU4LTEuMTgzNiAxLjE4MzYtMS45MjU4IDIuODIwMy0xLjkyNTggNC42MzY3djQzLjA2MmMwIDEuODAwOCAwLjc0MjE5IDMuNDM3NSAxLjkyNTggNC42MzY3IDEuMTgzNiAxLjE4MzYgMi44MjAzIDEuOTI1OCA0LjYzNjcgMS45MjU4IDEuODAwOCAwIDMuNDM3NS0wLjc0MjE5IDQuNjM2Ny0xLjkyNTh6bS0yMy45MTggMTUuOTY5YzEuMTgzNi0xLjE4MzYgMS45MjU4LTIuODIwMyAxLjkyNTgtNC42MzY3di03NC45OGMwLTEuODAwOC0wLjc0MjE5LTMuNDM3NS0xLjkyNTgtNC42MzY3LTEuMTgzNi0xLjE4MzYtMi44MjAzLTEuOTI1OC00LjYzNjctMS45MjU4LTEuODAwOCAwLTMuNDM3NSAwLjc0MjE5LTQuNjM2NyAxLjkyNTgtMS4xODM2IDEuMTgzNi0xLjkyNTggMi44MjAzLTEuOTI1OCA0LjYzNjd2NzQuOThjMCAxLjgwMDggMC43NDIxOSAzLjQzNzUgMS45MjU4IDQuNjM2NyAxLjE4MzYgMS4xODM2IDIuODIwMyAxLjkyNTggNC42MzY3IDEuOTI1OCAxLjgwMDggMCAzLjQzNzUtMC43NDIxOSA0LjYzNjctMS45MjU4em03My4wMDQtMjEuMTIxYzEuMTgzNi0xLjE4MzYgMS45MjU4LTIuODIwMyAxLjkyNTgtNC42MzY3di0zMi43NThjMC0xLjgwMDgtMC43NDIxOS0zLjQzNzUtMS45MjU4LTQuNjM2Ny0xLjE4MzYtMS4xODM2LTIuODIwMy0xLjkyNTgtNC42MzY3LTEuOTI1OC0xLjgwMDggMC0zLjQzNzUgMC43NDIxOS00LjYzNjcgMS45MjU4LTEuMTgzNiAxLjE4MzYtMS45MjU4IDIuODIwMy0xLjkyNTggNC42MzY3djMyLjc1OGMwIDEuODAwOCAwLjc0MjE5IDMuNDM3NSAxLjkyNTggNC42MzY3IDEuMTgzNiAxLjE4MzYgMi44MjAzIDEuOTI1OCA0LjYzNjcgMS45MjU4IDEuODAwOCAwIDMuNDM3NS0wLjc0MjE5IDQuNjM2Ny0xLjkyNTh6bS0xMzcuMjcgODAuODU5Yy0xLjE0NDUgMC0yLjA4OTggMC45MzM1OS0yLjA4OTggMi4wODk4djQuNjk5MmMwIDIyLjM4My0xOC4xOTkgNDAuNTgyLTQwLjU4MiA0MC41ODItMjIuMzgzIDAtNDAuNTgyLTE4LjE5OS00MC41ODItNDAuNTgydi00LjY5OTJjMC0xLjE0NDUtMC45MzM1OS0yLjA4OTgtMi4wODk4LTIuMDg5OC0xLjE0NDUgMC0yLjA4OTggMC45MzM1OS0yLjA4OTggMi4wODk4djQuNjk5MmMwIDIyLjc1OCAxNy4wNzggNDEuNTY2IDM5LjA5NCA0NC4zNTktMC4wMTE3MTkgMC4xMzY3Mi0wLjA1MDc4MSAwLjI2NTYyLTAuMDUwNzgxIDAuNDAyMzR2MzQuNDM4YzAgMC4yODkwNi0wLjIyNjU2IDAuNTE1NjItMC41MTU2MiAwLjUxNTYyaC0xNC4xMDVjLTEuNTc0MiAwLTIuOTk2MSAwLjY0MDYzLTQuMDMxMiAxLjY3NTgtMS4wMzEyIDEuMDMxMi0xLjY3NTggMi40Njg4LTEuNjc1OCA0LjAzMTIgMCAxLjU3NDIgMC42NDA2MiAyLjk5NjEgMS42NzU4IDQuMDMxMiAxLjAzMTIgMS4wMzEyIDIuNDY4OCAxLjY3NTggNC4wMzEyIDEuNjc1OGg0MC42NjhjMS41NzQyIDAgMi45OTYxLTAuNjQwNjIgNC4wMzEyLTEuNjc1OCAxLjAzMTItMS4wMzEyIDEuNjc1OC0yLjQ2ODggMS42NzU4LTQuMDMxMiAwLTEuNTc0Mi0wLjY0MDYyLTIuOTk2MS0xLjY3NTgtNC4wMzEyLTEuMDMxMi0xLjAzMTItMi40Njg4LTEuNjc1OC00LjAzMTItMS42NzU4aC0xNC4xMDVjLTAuMjg5MDYgMC0wLjUxNTYyLTAuMjI2NTYtMC41MTU2Mi0wLjUxNTYydi0zNC40MzhjMC0wLjEzNjcyLTAuMDM5MDYyLTAuMjY1NjMtMC4wNTA3ODEtMC40MDIzNCAyMi4wMDQtMi43OTY5IDM5LjA5NC0yMS42MDIgMzkuMDk0LTQ0LjM1OXYtNC42OTkyYzAtMS4xNDQ1LTAuOTMzNTktMi4wODk4LTIuMDg5OC0yLjA4OTh6IiBmaWxsPSIjZDJkMmQyIi8+Cjwvc3ZnPgo=';

export class AudioPlayer {
    constructor(containerId, docId, metadata, chunks) {
        this.container = document.getElementById(containerId);
        this.docId = docId;
        this.metadata = metadata;
        this.chunks = chunks; // Chunks with timestamps for sync
        this.onTimeUpdate = null; // Callback for accordion sync

        this.audioElement = document.getElementById('audio-player');
        this.sourceElement = document.getElementById('audio-source');
        this.trackElement = document.getElementById('audio-track');
        this.metadataElement = document.getElementById('audio-metadata');
        this.captionElement = document.getElementById('current-caption');

        // Throttling for accordion sync (prevent excessive updates)
        this.lastSyncTime = 0;
        this.syncThrottleMs = 300; // Update accordion at most every 300ms
        this.lastActiveChunkId = null; // Track which chunk was last synced
        this.lastCaptionTime = -1; // Track last caption update

        // Parsed segments from markdown for captions
        this.segments = [];
        this.markdownContent = null;

        this.init();
    }

    async init() {
        // Set audio source (from worker API endpoint)
        // Use /documents/{doc_id}/audio endpoint to avoid CORS issues
        this.sourceElement.src = `/documents/${this.docId}/audio`;
        console.log(`[AudioPlayer] Audio source set to: ${this.sourceElement.src}`);

        // Set VTT track if available
        if (this.metadata.vtt_available) {
            this.trackElement.src = `/documents/${this.docId}/vtt`;
        } else {
            this.trackElement.remove();
        }

        // Fetch markdown for caption segments
        if (this.metadata.markdown_available) {
            await this.fetchMarkdown();
            this.segments = this.parseMarkdownSegments();
            console.log(`[AudioPlayer] Loaded ${this.segments.length} caption segments`);
        }

        // Display metadata
        this.displayMetadata();

        // Display album art (Wave 5)
        this.displayAlbumArt();

        // Bind event listeners
        this.audioElement.addEventListener('timeupdate', () => this.handleTimeUpdate());
        this.audioElement.addEventListener('loadedmetadata', () => this.handleLoaded());
        this.audioElement.addEventListener('error', (e) => {
            console.error('[AudioPlayer] Audio load error:', e);
            console.error('[AudioPlayer] Error details:', this.audioElement.error);
        });

        // Handle cue changes (VTT)
        if (this.trackElement.track) {
            this.trackElement.track.addEventListener('cuechange', () => this.handleCueChange());
        }

        // Force the audio element to load the source
        this.audioElement.load();
        console.log('[AudioPlayer] Audio player initialized, loading audio...');
    }

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

    parseMarkdownSegments() {
        if (!this.markdownContent) {
            return [];
        }

        const segments = [];
        const timeRegex = /\[time:\s*([\d.]+)-([\d.]+)\]/g;
        const matches = [];
        let match;

        // Collect all timestamp positions and values
        while ((match = timeRegex.exec(this.markdownContent)) !== null) {
            matches.push({
                index: match.index,
                startTime: parseFloat(match[1]),
                endTime: parseFloat(match[2]),
                fullMatch: match[0]
            });
        }

        // Extract text between each timestamp and the next
        for (let i = 0; i < matches.length; i++) {
            const currentMatch = matches[i];
            const nextMatch = matches[i + 1];

            const textStart = currentMatch.index + currentMatch.fullMatch.length;
            const textEnd = nextMatch ? nextMatch.index : this.markdownContent.length;
            const text = this.markdownContent.substring(textStart, textEnd).trim();

            if (text) {
                segments.push({
                    startTime: currentMatch.startTime,
                    endTime: currentMatch.endTime,
                    text: text
                });
            }
        }

        return segments;
    }

    displayMetadata() {
        const raw = this.metadata.raw_metadata || {};
        const metadata = [];

        if (raw.title) {
            metadata.push(`<div class="metadata-item"><strong>Title:</strong> ${this.escapeHtml(raw.title)}</div>`);
        }
        if (raw.artist) {
            metadata.push(`<div class="metadata-item"><strong>Artist:</strong> ${this.escapeHtml(raw.artist)}</div>`);
        }
        if (raw.album) {
            metadata.push(`<div class="metadata-item"><strong>Album:</strong> ${this.escapeHtml(raw.album)}</div>`);
        }
        if (raw.duration_seconds) {
            const duration = this.formatTime(raw.duration_seconds);
            metadata.push(`<div class="metadata-item"><strong>Duration:</strong> ${duration}</div>`);
        }

        if (metadata.length > 0) {
            this.metadataElement.innerHTML = metadata.join('');
        }
    }

    displayAlbumArt() {
        const albumArtElement = document.getElementById('album-art');
        if (!albumArtElement) {
            console.warn('[AudioPlayer] Album art element not found');
            return;
        }

        // Set alt text based on metadata
        const raw = this.metadata.raw_metadata || {};
        const altText = raw.title
            ? `Album art for ${this.escapeHtml(raw.title)}`
            : 'Album art';
        albumArtElement.alt = altText;

        // Check if album art is available
        if (this.metadata.has_album_art && this.metadata.album_art_url) {
            // Load album art from API endpoint
            albumArtElement.classList.add('loading');
            albumArtElement.src = this.metadata.album_art_url;

            // Handle successful load
            albumArtElement.addEventListener('load', () => {
                albumArtElement.classList.remove('loading');
                albumArtElement.classList.add('loaded');
                console.log('[AudioPlayer] Album art loaded successfully');
            }, { once: true });

            // Handle load error (fallback to default SVG)
            albumArtElement.addEventListener('error', () => {
                console.warn('[AudioPlayer] Album art failed to load, using default SVG');
                albumArtElement.src = DEFAULT_ALBUM_ART_SVG;
                albumArtElement.classList.remove('loading');
                albumArtElement.classList.add('loaded');
            }, { once: true });
        } else {
            // No album art available, use default SVG
            albumArtElement.src = DEFAULT_ALBUM_ART_SVG;
            albumArtElement.classList.add('loaded');
            console.log('[AudioPlayer] No album art available, using default SVG');
        }
    }

    handleTimeUpdate() {
        try {
            const currentTime = this.audioElement.currentTime;
            const now = Date.now();

            // Find and update caption from parsed segments
            if (this.segments && this.segments.length > 0) {
                const activeSegment = this.segments.find(seg =>
                    currentTime >= seg.startTime && currentTime < seg.endTime
                );

                if (activeSegment) {
                    // Only update if changed (avoid unnecessary DOM updates)
                    if (Math.floor(activeSegment.startTime) !== this.lastCaptionTime) {
                        this.captionElement.textContent = activeSegment.text;
                        this.lastCaptionTime = Math.floor(activeSegment.startTime);
                    }
                } else {
                    // Clear caption when no active segment
                    if (this.captionElement.textContent !== '') {
                        this.captionElement.textContent = '';
                        this.lastCaptionTime = -1;
                    }
                }
            }

            // Throttle accordion sync updates
            if (now - this.lastSyncTime < this.syncThrottleMs) {
                return;
            }

            // Find active chunk for accordion sync
            if (this.chunks && this.chunks.length > 0) {
                let activeChunk = null;

                // Try to find chunk with proper start_time/end_time fields
                activeChunk = this.chunks.find(chunk =>
                    chunk.has_timestamps &&
                    chunk.start_time !== null &&
                    chunk.end_time !== null &&
                    currentTime >= chunk.start_time &&
                    currentTime < chunk.end_time
                );

                // Fallback: Parse timestamps from text content
                if (!activeChunk) {
                    for (const chunk of this.chunks) {
                        const match = chunk.text_content?.match(/^\[time:\s*([\d.]+)-([\d.]+)\]/);
                        if (match) {
                            const startTime = parseFloat(match[1]);
                            const endTime = parseFloat(match[2]);

                            if (currentTime >= startTime && currentTime < endTime) {
                                activeChunk = chunk;
                                break;
                            }
                        }
                    }
                }

                // Only notify accordion if chunk has changed (prevent redundant updates)
                if (activeChunk &&
                    activeChunk.chunk_id !== this.lastActiveChunkId &&
                    this.onTimeUpdate) {

                    console.log(`[Audio→Accordion] Active chunk: ${activeChunk.chunk_id} at ${currentTime.toFixed(2)}s`);
                    this.onTimeUpdate(activeChunk);
                    this.lastActiveChunkId = activeChunk.chunk_id;
                    this.lastSyncTime = now;
                }
            }
        } catch (error) {
            console.error('[AudioPlayer] Error in handleTimeUpdate:', error);
        }
    }

    handleCueChange() {
        const track = this.trackElement.track;
        if (track && track.activeCues && track.activeCues.length > 0) {
            const activeCue = track.activeCues[0];
            this.captionElement.textContent = activeCue.text;
        } else {
            this.captionElement.textContent = '';
        }
    }

    handleLoaded() {
        console.log(`Audio loaded: ${this.audioElement.duration}s`);
    }

    // Public method for external seek (from accordion)
    seekTo(timeInSeconds) {
        try {
            if (typeof timeInSeconds !== 'number' || isNaN(timeInSeconds)) {
                console.error(`[AudioPlayer] Invalid seek time (not a number): ${timeInSeconds}`);
                return;
            }

            if (timeInSeconds < 0) {
                console.warn(`[AudioPlayer] Seek time cannot be negative: ${timeInSeconds}, clamping to 0`);
                timeInSeconds = 0;
            }

            // Check duration is available (metadata loaded)
            if (!this.audioElement.duration || isNaN(this.audioElement.duration)) {
                console.warn('[AudioPlayer] Audio duration not yet available, deferring seek');
                // Defer seek until metadata is loaded
                this.audioElement.addEventListener('loadedmetadata', () => {
                    this.seekTo(timeInSeconds);
                }, { once: true });
                return;
            }

            if (timeInSeconds > this.audioElement.duration) {
                console.warn(`[AudioPlayer] Seek time ${timeInSeconds}s exceeds duration ${this.audioElement.duration}s, clamping`);
                timeInSeconds = this.audioElement.duration - 0.1;
            }

            this.audioElement.currentTime = timeInSeconds;

            // Auto-play after seek (optional)
            if (this.audioElement.paused) {
                this.audioElement.play().catch(err => {
                    console.warn('[AudioPlayer] Auto-play prevented:', err);
                });
            }

            console.log(`[AudioPlayer] Seeked to ${timeInSeconds.toFixed(2)}s`);
        } catch (error) {
            console.error('[AudioPlayer] Error in seekTo:', error);
        }
    }

    // Register callback for time updates (accordion sync)
    registerTimeUpdateCallback(callback) {
        if (typeof callback !== 'function') {
            console.error('[AudioPlayer] registerTimeUpdateCallback requires a function');
            return;
        }
        this.onTimeUpdate = callback;
        console.log('[AudioPlayer] Time update callback registered');
    }

    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        } else {
            return `${minutes}:${String(secs).padStart(2, '0')}`;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    destroy() {
        // Clean up event listeners
        this.audioElement.removeEventListener('timeupdate', this.handleTimeUpdate);
        this.audioElement.removeEventListener('loadedmetadata', this.handleLoaded);
    }
}
