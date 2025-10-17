/**
 * Audio Player Component
 *
 * HTML5 audio player with VTT caption support and sync with accordion.
 * Auto-opens accordion sections based on current playback time.
 *
 * Wave 3 - Frontend Component
 * Wave 5 - Album Art Support
 */

import { DEFAULT_ALBUM_ART_SVG } from './assets.js';

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

            // Caption display: Prefer VTT (via handleCueChange), fallback to markdown
            // Only use markdown parsing if VTT is not available
            if (!this.metadata.vtt_available && this.segments && this.segments.length > 0) {
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
            // Note: When VTT is available, captions are handled by handleCueChange()

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
