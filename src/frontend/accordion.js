/**
 * Accordion Component
 *
 * Displays document text content in expandable sections:
 * - Full markdown (default open) with download/copy
 * - Per-chunk sections with download/copy
 * - VTT transcript section (audio only)
 *
 * Supports bidirectional sync with slideshow and audio player.
 *
 * Wave 3 - Frontend Component
 */

import { copyToClipboard, stripFrontmatter } from './clipboard-utils.js';
import { downloadMarkdown, downloadVTT, downloadTextAsFile } from './download-utils.js';

export class Accordion {
    constructor(containerId, docId, chunks, metadata) {
        this.container = document.getElementById(containerId);
        this.docId = docId;
        this.chunks = chunks;
        this.metadata = metadata;
        this.markdownContent = null;
        this.vttContent = null;

        this.slideshow = null; // Will be set for slideshow sync
        this.audioPlayer = null; // Will be set for audio sync

        this.init();
    }

    async init() {
        // Fetch full markdown if available
        if (this.metadata.markdown_available) {
            await this.fetchMarkdown();
        }

        // Fetch VTT if available
        if (this.metadata.vtt_available) {
            await this.fetchVTT();
        }

        // Build accordion sections
        this.buildAccordion();

        console.log('Accordion initialized');
    }

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

    async fetchVTT() {
        try {
            const response = await fetch(`/documents/${this.docId}/vtt`);
            if (response.ok) {
                this.vttContent = await response.text();
                console.log('VTT content fetched');
            } else {
                console.warn('Failed to fetch VTT:', response.status);
            }
        } catch (err) {
            console.error('Error fetching VTT:', err);
        }
    }

    buildAccordion() {
        this.container.innerHTML = '';

        // Section 1: Full Markdown (default open)
        if (this.markdownContent) {
            this.addMarkdownSection();
        }

        // Section 2: Per-Chunk Sections (collapsed by default)
        if (this.chunks && this.chunks.length > 0) {
            this.addChunkSections();
        }

        // Section 3: VTT Transcript (audio only, collapsed by default)
        if (this.vttContent && this.metadata.has_timestamps) {
            this.addVTTSection();
        }
    }

    addMarkdownSection() {
        const section = this.createSection({
            id: 'markdown-full',
            title: 'Full Document',
            content: stripFrontmatter(this.markdownContent),
            isOpen: false,
            actions: [
                {
                    label: '📥 Download',
                    handler: (btn) => downloadMarkdown(this.docId, btn)
                },
                {
                    label: '📋 Copy',
                    handler: (btn) => copyToClipboard(stripFrontmatter(this.markdownContent), btn)
                }
            ]
        });

        this.container.appendChild(section);
    }

    addChunkSections() {
        /**
         * Display chunk sections with timestamps.
         * Uses chunk.start_time/end_time directly from API.
         * Text comes from chunk.text_content (already cleaned of [time: X-Y] markers).
         */

        if (!this.chunks || this.chunks.length === 0) {
            console.warn('[Accordion] No chunks available');
            return;
        }

        this.chunks.forEach((chunk, index) => {
            // Determine section title based on timestamp presence
            const sectionTitle = this.getChunkTitle(chunk, index);

            // Create section with chunk data
            const section = this.createSection({
                id: chunk.chunk_id,
                title: sectionTitle,
                content: chunk.text_content,  // Already cleaned (no [time: X-Y])
                isOpen: false,
                timestamp: chunk.start_time !== null ? {
                    start: chunk.start_time,
                    end: chunk.end_time
                } : null,
                pageNum: this.getPageFromChunk(chunk),
                actions: [
                    {
                        label: '📋 Copy',
                        handler: (btn) => copyToClipboard(chunk.text_content, btn)
                    }
                ]
            });

            this.container.appendChild(section);
        });

        console.log(`[Accordion] Created ${this.chunks.length} sections`);
    }

    addVTTSection() {
        const section = this.createSection({
            id: 'vtt-transcript',
            title: 'VTT Transcript',
            content: this.vttContent,
            isOpen: false,
            actions: [
                {
                    label: '📥 Download VTT',
                    handler: (btn) => downloadVTT(this.docId, btn)
                },
                {
                    label: '📋 Copy',
                    handler: (btn) => copyToClipboard(this.vttContent, btn)
                }
            ]
        });

        this.container.appendChild(section);
    }

    createSection({ id, title, content, isOpen, timestamp, pageNum, actions }) {
        const section = document.createElement('div');
        section.className = 'accordion-section';
        section.dataset.sectionId = id;

        // Header
        const header = document.createElement('div');
        header.className = `accordion-header ${isOpen ? 'open' : ''}`;

        const titleDiv = document.createElement('div');
        titleDiv.className = 'accordion-title';
        titleDiv.textContent = title;

        // Add timestamp badge if available
        if (timestamp) {
            const timestampSpan = document.createElement('span');
            timestampSpan.className = 'accordion-timestamp';
            timestampSpan.textContent = `(${this.formatTime(timestamp.start)} - ${this.formatTime(timestamp.end)})`;
            titleDiv.appendChild(timestampSpan);
        }

        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'accordion-actions';

        const toggle = document.createElement('span');
        toggle.className = 'accordion-toggle';
        toggle.textContent = '▼';
        actionsDiv.appendChild(toggle);

        header.appendChild(titleDiv);
        header.appendChild(actionsDiv);

        // Content
        const contentDiv = document.createElement('div');
        contentDiv.className = `accordion-content ${isOpen ? 'open' : ''}`;

        const body = document.createElement('div');
        body.className = 'accordion-body';

        // Actions (download/copy buttons)
        if (actions && actions.length > 0) {
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'accordion-body-actions';

            actions.forEach(action => {
                const btn = document.createElement('button');
                btn.className = 'btn-icon';
                btn.innerHTML = action.label;
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    action.handler(btn);
                });
                actionsContainer.appendChild(btn);
            });

            body.appendChild(actionsContainer);
        }

        // Text content
        const textDiv = document.createElement('div');
        textDiv.className = 'accordion-body-text';
        textDiv.textContent = content;
        body.appendChild(textDiv);

        contentDiv.appendChild(body);

        // Assemble section
        section.appendChild(header);
        section.appendChild(contentDiv);

        // Toggle event
        header.addEventListener('click', () => this.toggleSection(header, contentDiv));

        // Click-to-navigate events with error handling
        if (timestamp && timestamp.start !== null && timestamp.start >= 0 && this.audioPlayer) {
            header.addEventListener('click', () => {
                try {
                    console.log(`[Accordion→Audio] Seeking to ${timestamp.start}s`);
                    this.audioPlayer.seekTo(timestamp.start);
                } catch (error) {
                    console.error('Failed to seek audio:', error);
                }
            });
        }

        if (pageNum && pageNum > 0 && this.slideshow) {
            header.addEventListener('click', () => {
                try {
                    console.log(`[Accordion→Slideshow] Navigating to page ${pageNum}`);
                    this.slideshow.navigateToPage(pageNum);
                } catch (error) {
                    console.error('Failed to navigate slideshow:', error);
                }
            });
        }

        return section;
    }

    toggleSection(header, content) {
        const isOpen = header.classList.contains('open');

        if (isOpen) {
            // Close this section
            header.classList.remove('open');
            content.classList.remove('open');
        } else {
            // Close all other sections first
            const allHeaders = this.container.querySelectorAll('.accordion-header');
            const allContents = this.container.querySelectorAll('.accordion-content');

            allHeaders.forEach(h => {
                if (h !== header) {
                    h.classList.remove('open', 'active');
                }
            });

            allContents.forEach(c => {
                if (c !== content) {
                    c.classList.remove('open');
                }
            });

            // Open this section
            header.classList.add('open');
            content.classList.add('open');
        }
    }

    // Open specific section by chunk (for audio sync)
    openSection(chunk) {
        /**
         * Open accordion section for given chunk.
         * Called by audio player during playback.
         *
         * @param {Object} chunk - Chunk object with chunk_id
         */

        try {
            if (!chunk || !chunk.chunk_id) {
                console.warn('[Accordion] openSection called without valid chunk');
                return;
            }

            // Find section by chunk_id (simplified - no timestamp matching needed)
            const section = this.container.querySelector(
                `[data-section-id="${chunk.chunk_id}"]`
            );

            if (!section) {
                console.warn(`[Accordion] Section not found: ${chunk.chunk_id}`);
                return;
            }

            const header = section.querySelector('.accordion-header');
            const content = section.querySelector('.accordion-content');

            if (!header || !content) {
                console.error('[Accordion] Section missing header or content');
                return;
            }

            // Close all other sections
            this.closeAllSections();

            // Open this section
            header.classList.add('open', 'active');
            content.classList.add('open');

            // Scroll into view
            section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            console.log(`[Accordion] Opened section: ${chunk.chunk_id}`);
        } catch (error) {
            console.error('[Accordion] Error in openSection:', error);
        }
    }

    closeAllSections() {
        const headers = this.container.querySelectorAll('.accordion-header');
        const contents = this.container.querySelectorAll('.accordion-content');

        headers.forEach(header => {
            header.classList.remove('active', 'open');
        });

        contents.forEach(content => {
            content.classList.remove('open');
        });
    }


    getChunkTitle(chunk, index) {
        /**
         * Generate section title with optional timestamp.
         *
         * Examples:
         *   - With timestamps: "Segment 1 (0:00 - 0:04)"
         *   - Without timestamps: "Chunk 1" or "Chunk 1 (Page 2)"
         */

        if (chunk.start_time !== null && chunk.end_time !== null) {
            // Format: "Segment N (MM:SS - MM:SS)"
            const startStr = this.formatTime(chunk.start_time);
            const endStr = this.formatTime(chunk.end_time);
            return `Segment ${index + 1} (${startStr} - ${endStr})`;
        } else {
            // No timestamps - simple title
            const pageNum = this.getPageFromChunk(chunk);
            if (pageNum) {
                return `Chunk ${index + 1} (Page ${pageNum})`;
            } else {
                return `Chunk ${index + 1}`;
            }
        }
    }

    getPageFromChunk(chunk) {
        // Chunks may have page info in raw metadata
        // For now, we'll extract from embedding_id or metadata
        // This is a simplified approach - adjust based on actual data structure
        return null; // TODO: Extract page number from chunk metadata
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${String(secs).padStart(2, '0')}`;
    }

    // Register slideshow for click-to-navigate
    registerSlideshow(slideshow) {
        this.slideshow = slideshow;
    }

    // Register audio player for click-to-seek and auto-open sync
    registerAudioPlayer(audioPlayer) {
        if (!audioPlayer) {
            console.warn('[Accordion] registerAudioPlayer called with null audioPlayer');
            return;
        }

        this.audioPlayer = audioPlayer;

        // Set up callback for audio time updates with error handling
        try {
            audioPlayer.registerTimeUpdateCallback((activeChunk) => {
                if (activeChunk && activeChunk.chunk_id) {
                    // Pass the full chunk object to openSection
                    this.openSection(activeChunk);
                }
            });
            console.log('[Accordion] Audio player registered for sync');
        } catch (error) {
            console.error('[Accordion] Failed to register audio player:', error);
        }
    }
}
