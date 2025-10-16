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
        // Parse markdown into time-stamped segments for full text display
        const segments = this.parseMarkdownSegments();

        if (segments.length > 0) {
            // Use parsed segments from markdown (full text)
            segments.forEach((segment, index) => {
                const section = this.createSection({
                    id: `segment-${index}`,
                    title: `Segment ${index + 1} (${this.formatTime(segment.startTime)} - ${this.formatTime(segment.endTime)})`,
                    content: segment.text,
                    isOpen: false,
                    timestamp: { start: segment.startTime, end: segment.endTime },
                    pageNum: null,
                    actions: [
                        {
                            label: '📋 Copy',
                            handler: (btn) => copyToClipboard(segment.text, btn)
                        }
                    ]
                });

                this.container.appendChild(section);
            });
        } else {
            // Fallback to using chunks if markdown parsing fails
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

    // Open specific section by chunk ID or timestamp (for audio sync)
    openSection(chunkOrTimestamp) {
        try {
            if (!chunkOrTimestamp) {
                console.warn('[Accordion] openSection called with null/undefined');
                return;
            }

            let section = null;

            // Try to find by chunk_id first (backward compatibility)
            if (chunkOrTimestamp.chunk_id) {
                section = this.container.querySelector(`[data-section-id="${chunkOrTimestamp.chunk_id}"]`);
            }

            // If not found, find by matching timestamp
            if (!section) {
                // Parse timestamp from text_content if available
                const textContent = chunkOrTimestamp.text_content || '';
                const match = textContent.match(/^\[time:\s*([\d.]+)-([\d.]+)\]/);

                if (match) {
                    const startTime = parseFloat(match[1]);
                    const allSections = this.container.querySelectorAll('.accordion-section');

                    // Find section with matching timestamp
                    for (const sec of allSections) {
                        const sectionId = sec.dataset.sectionId;
                        if (sectionId && sectionId.startsWith('segment-')) {
                            const header = sec.querySelector('.accordion-header');
                            const titleText = header?.textContent || '';
                            const timeMatch = titleText.match(/([\d:]+)\s*-\s*([\d:]+)/);

                            if (timeMatch) {
                                const sectionStart = this.parseTimeString(timeMatch[1]);
                                if (Math.abs(sectionStart - startTime) < 0.1) {
                                    section = sec;
                                    break;
                                }
                            }
                        }
                    }
                }
            }

            if (!section) {
                console.warn(`[Accordion] Section not found for chunk/timestamp`);
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
            console.log(`[Audio→Accordion] Opened section`);
        } catch (error) {
            console.error('[Accordion] Error in openSection:', error);
        }
    }

    parseTimeString(timeStr) {
        // Convert "MM:SS" to seconds
        const parts = timeStr.split(':');
        if (parts.length === 2) {
            return parseInt(parts[0]) * 60 + parseFloat(parts[1]);
        }
        return parseFloat(timeStr);
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

    parseMarkdownSegments() {
        if (!this.markdownContent) {
            return [];
        }

        const segments = [];

        // Split content by timestamp markers
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

            // Get text after current timestamp until next timestamp (or end of string)
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

        console.log(`[Accordion] Parsed ${segments.length} segments from markdown`);
        return segments;
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
        if (!audioPlayer) {
            console.warn('[Accordion] registerAudioPlayer called with null audioPlayer');
            return;
        }

        this.audioPlayer = audioPlayer;

        // Set up callback for audio time updates with error handling
        try {
            audioPlayer.registerTimeUpdateCallback((activeChunk) => {
                if (activeChunk && activeChunk.chunk_id) {
                    this.openSection(activeChunk.chunk_id);
                }
            });
            console.log('[Accordion] Audio player registered for sync');
        } catch (error) {
            console.error('[Accordion] Failed to register audio player:', error);
        }
    }
}
