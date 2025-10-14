/**
 * Audio Player Component
 *
 * HTML5 audio player with VTT caption support and sync with accordion.
 * Auto-opens accordion sections based on current playback time.
 *
 * Wave 3 - Frontend Component
 */

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

        this.init();
    }

    init() {
        // Set audio source (from uploads directory)
        const audioPath = this.metadata.raw_metadata?.source_path || '';
        if (audioPath) {
            // Extract filename from path
            const filename = audioPath.split('/').pop();
            this.sourceElement.src = `/uploads/${filename}`;
        }

        // Set VTT track if available
        if (this.metadata.vtt_available) {
            this.trackElement.src = `/documents/${this.docId}/vtt`;
        } else {
            this.trackElement.remove();
        }

        // Display metadata
        this.displayMetadata();

        // Bind event listeners
        this.audioElement.addEventListener('timeupdate', () => this.handleTimeUpdate());
        this.audioElement.addEventListener('loadedmetadata', () => this.handleLoaded());

        // Handle cue changes (VTT)
        if (this.trackElement.track) {
            this.trackElement.track.addEventListener('cuechange', () => this.handleCueChange());
        }

        console.log('Audio player initialized');
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

    handleTimeUpdate() {
        try {
            const currentTime = this.audioElement.currentTime;
            const now = Date.now();

            // Throttle updates to prevent excessive DOM manipulation
            if (now - this.lastSyncTime < this.syncThrottleMs) {
                return;
            }

            // Find active chunk based on current time
            if (this.chunks && this.chunks.length > 0) {
                const activeChunk = this.chunks.find(chunk =>
                    chunk.has_timestamps &&
                    chunk.start_time !== null &&
                    chunk.end_time !== null &&
                    currentTime >= chunk.start_time &&
                    currentTime < chunk.end_time
                );

                // Only notify if chunk has changed (prevent redundant updates)
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
