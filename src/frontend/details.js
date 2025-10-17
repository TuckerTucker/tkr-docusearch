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
import { DocumentsAPIClient } from './api-client.js';
import { applyEarlyTheme, initTheme } from './theme-toggle.js';
import { initStyleSelector } from './style-selector.js';

// Apply theme immediately to avoid flash
applyEarlyTheme();

class DetailsPage {
    constructor() {
        this.docId = null;
        this.documentData = null;
        this.serverConfig = null;
        this.apiClient = null;

        this.slideshow = null;
        this.audioPlayer = null;
        this.accordion = null;

        this.init();
    }

    async init() {
        // Extract doc_id from URL query params
        const params = new URLSearchParams(window.location.search);
        this.docId = params.get('id');

        if (!this.docId) {
            this.showError('No document ID provided');
            return;
        }

        // Initialize API client
        this.apiClient = new DocumentsAPIClient('http://localhost:8002');

        // Fetch server configuration
        try {
            this.serverConfig = await this.apiClient.getSupportedFormats();
            console.log('✅ Server config loaded:', this.serverConfig);
        } catch (error) {
            console.error('⚠️ Failed to load server config, using fallback:', error);
            // Fallback configuration
            this.serverConfig = {
                extensions: ['.pdf', '.docx', '.pptx', '.mp3', '.wav'],
                groups: [
                    { id: 'audio', label: 'Audio', extensions: ['.mp3', '.wav'] }
                ]
            };
        }

        // Load document
        await this.loadDocument();
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

        // Check if document is audio using server config
        const audioGroup = this.serverConfig.groups.find(g => g.id === 'audio');
        const audioExtensions = audioGroup ? audioGroup.extensions : ['.mp3', '.wav'];

        // Extract file extension
        const ext = this.documentData.filename
            ? `.${this.documentData.filename.split('.').pop().toLowerCase()}`
            : '';

        const isAudioFile = this.documentData.metadata.raw_metadata?.format_type === 'audio' ||
                           audioExtensions.includes(ext);
        const hasAudio = isAudioFile || this.documentData.metadata.has_timestamps;
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
            container.innerHTML = '<p>No text content available</p>';
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
        initTheme();
        initStyleSelector();
        new DetailsPage();
    });
} else {
    initTheme();
    initStyleSelector();
    new DetailsPage();
}
