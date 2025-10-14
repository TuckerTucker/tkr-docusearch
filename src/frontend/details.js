/**
 * Details Page Main Controller
 *
 * Orchestrates all components (slideshow, audio player, accordion) and
 * handles document loading and initialization.
 *
 * Wave 3 - Frontend Integration
 */

import { Slideshow } from './slideshow.js';
import { AudioPlayer } from './audio-player.js';
import { Accordion } from './accordion.js';

class DetailsPage {
    constructor() {
        this.docId = null;
        this.documentData = null;

        this.slideshow = null;
        this.audioPlayer = null;
        this.accordion = null;

        this.init();
    }

    init() {
        // Extract doc_id from URL query params
        const params = new URLSearchParams(window.location.search);
        this.docId = params.get('id');

        if (!this.docId) {
            this.showError('No document ID provided');
            return;
        }

        // Load document
        this.loadDocument();
    }

    async loadDocument() {
        try {
            this.showLoading();

            // Fetch document details from API
            const response = await fetch(`/documents/${this.docId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    this.showError('Document not found');
                } else {
                    this.showError('Failed to load document');
                }
                return;
            }

            this.documentData = await response.json();

            // Set page title
            document.getElementById('doc-title').textContent = this.documentData.filename;
            document.title = `${this.documentData.filename} - DocuSearch`;

            // Initialize components
            this.initializeComponents();

            // Show main content
            this.showContent();

            console.log('Document loaded:', this.documentData);
        } catch (err) {
            console.error('Error loading document:', err);
            this.showError('An error occurred while loading the document');
        }
    }

    initializeComponents() {
        const hasPages = this.documentData.pages && this.documentData.pages.length > 0;
        const hasAudio = this.documentData.metadata.has_timestamps;
        const hasChunks = this.documentData.chunks && this.documentData.chunks.length > 0;

        // Initialize Slideshow (documents with pages)
        if (hasPages && !hasAudio) {
            document.getElementById('slideshow-container').style.display = 'block';
            this.slideshow = new Slideshow('slideshow-container', this.documentData.pages);
        }
        // Initialize Audio Player (audio files)
        else if (hasAudio) {
            document.getElementById('audio-container').style.display = 'block';
            this.audioPlayer = new AudioPlayer(
                'audio-container',
                this.docId,
                this.documentData.metadata,
                this.documentData.chunks
            );
        }
        // No visual content
        else {
            document.getElementById('no-visual-content').style.display = 'block';
        }

        // Initialize Accordion (always, for text content)
        if (hasChunks || this.documentData.metadata.markdown_available) {
            this.accordion = new Accordion(
                'accordion-container',
                this.docId,
                this.documentData.chunks,
                this.documentData.metadata
            );

            // Wire up bidirectional sync
            if (this.slideshow) {
                this.accordion.registerSlideshow(this.slideshow);
            }

            if (this.audioPlayer) {
                this.accordion.registerAudioPlayer(this.audioPlayer);
            }
        } else {
            // No text content available
            const container = document.getElementById('accordion-container');
            container.innerHTML = '<div class="no-visual-placeholder"><div class="placeholder-content"><p>No text content available</p></div></div>';
        }
    }

    showLoading() {
        document.getElementById('loading-state').style.display = 'flex';
        document.getElementById('error-state').style.display = 'none';
        document.getElementById('main-content').style.display = 'none';
    }

    showError(message) {
        document.getElementById('error-message').textContent = message;
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('error-state').style.display = 'flex';
        document.getElementById('main-content').style.display = 'none';
    }

    showContent() {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('error-state').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new DetailsPage();
    });
} else {
    new DetailsPage();
}
