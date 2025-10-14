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
            isOpen: true,
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
        this.chunks.forEach((chunk, index) => {
            const chunkTitle = this.getChunkTitle(chunk, index);

            const section = this.createSection({
                id: chunk.chunk_id,
                title: chunkTitle,
                content: chunk.text_content,
                isOpen: false,
                timestamp: chunk.has_timestamps ? { start: chunk.start_time, end: chunk.end_time } : null,
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

        // Click-to-navigate events
        if (timestamp && this.audioPlayer) {
            header.addEventListener('click', () => {
                this.audioPlayer.seekTo(timestamp.start);
            });
        }

        if (pageNum && this.slideshow) {
            header.addEventListener('click', () => {
                this.slideshow.navigateToPage(pageNum);
            });
        }

        return section;
    }

    toggleSection(header, content) {
        const isOpen = header.classList.contains('open');

        if (isOpen) {
            header.classList.remove('open');
            content.classList.remove('open');
        } else {
            header.classList.add('open');
            content.classList.add('open');
        }
    }

    // Open specific section by chunk ID (for audio sync)
    openSection(chunkId) {
        const section = this.container.querySelector(`[data-section-id="${chunkId}"]`);
        if (section) {
            const header = section.querySelector('.accordion-header');
            const content = section.querySelector('.accordion-content');

            // Close all other sections
            this.closeAllSections();

            // Open this section
            header.classList.add('open', 'active');
            content.classList.add('open');

            // Scroll into view
            section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    closeAllSections() {
        const headers = this.container.querySelectorAll('.accordion-header');
        const contents = this.container.querySelectorAll('.accordion-content');

        headers.forEach(header => {
            header.classList.remove('active');
            // Don't close markdown section
            if (header.parentElement.dataset.sectionId !== 'markdown-full') {
                header.classList.remove('open');
            }
        });

        contents.forEach(content => {
            if (content.parentElement.dataset.sectionId !== 'markdown-full') {
                content.classList.remove('open');
            }
        });
    }

    getChunkTitle(chunk, index) {
        let title = `Chunk ${index + 1}`;

        // Add page reference if available
        const pageNum = this.getPageFromChunk(chunk);
        if (pageNum) {
            title = `Chunk ${index + 1} (Page ${pageNum})`;
        }

        return title;
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
        this.audioPlayer = audioPlayer;

        // Set up callback for audio time updates
        audioPlayer.registerTimeUpdateCallback((activeChunk) => {
            this.openSection(activeChunk.chunk_id);
        });
    }
}
