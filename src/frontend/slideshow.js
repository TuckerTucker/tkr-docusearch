/**
 * Slideshow Component
 *
 * Displays document pages with manual navigation and keyboard support.
 * Supports navigation from accordion (click chunk to jump to page).
 *
 * Wave 3 - Frontend Component
 */

export class Slideshow {
    constructor(containerId, pages) {
        this.container = document.getElementById(containerId);
        this.pages = pages;
        this.currentPage = 1;
        this.totalPages = pages.length;

        this.imageElement = document.getElementById('slideshow-image');
        this.pageInput = document.getElementById('page-input');
        this.pageTotalElement = document.getElementById('page-total');
        this.prevButton = document.getElementById('prev-page');
        this.nextButton = document.getElementById('next-page');

        this.init();
    }

    init() {
        if (this.totalPages === 0) {
            console.warn('No pages available for slideshow');
            return;
        }

        // Set up page total
        this.pageTotalElement.textContent = `/ ${this.totalPages}`;
        this.pageInput.max = this.totalPages;

        // Bind event listeners
        this.prevButton.addEventListener('click', () => this.previousPage());
        this.nextButton.addEventListener('click', () => this.nextPage());
        this.pageInput.addEventListener('change', (e) => this.jumpToPage(parseInt(e.target.value)));
        this.pageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.jumpToPage(parseInt(e.target.value));
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Display first page
        this.goToPage(1);

        console.log(`Slideshow initialized: ${this.totalPages} pages`);
    }

    goToPage(pageNumber) {
        // Validate page number
        if (pageNumber < 1 || pageNumber > this.totalPages) {
            console.warn(`Invalid page number: ${pageNumber}`);
            return;
        }

        this.currentPage = pageNumber;

        // Find page data
        const page = this.pages.find(p => p.page_number === pageNumber);
        if (!page) {
            console.error(`Page ${pageNumber} not found in pages data`);
            return;
        }

        // Update image (prefer full resolution, fallback to thumbnail)
        const imageSrc = page.image_path || page.thumb_path;
        if (imageSrc) {
            this.imageElement.src = imageSrc;
            this.imageElement.alt = `Page ${pageNumber}`;
        } else {
            console.warn(`No image available for page ${pageNumber}`);
        }

        // Update UI
        this.pageInput.value = pageNumber;
        this.updateNavigationButtons();

        console.log(`Navigated to page ${pageNumber}`);
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.goToPage(this.currentPage - 1);
        }
    }

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.goToPage(this.currentPage + 1);
        }
    }

    jumpToPage(pageNumber) {
        if (isNaN(pageNumber)) {
            // Reset to current page if invalid input
            this.pageInput.value = this.currentPage;
            return;
        }

        this.goToPage(pageNumber);
    }

    updateNavigationButtons() {
        this.prevButton.disabled = (this.currentPage === 1);
        this.nextButton.disabled = (this.currentPage === this.totalPages);
    }

    handleKeyboard(event) {
        // Only handle if slideshow is visible and not typing in input
        if (this.container.style.display === 'none') {
            return;
        }

        if (document.activeElement === this.pageInput) {
            return;
        }

        switch (event.key) {
            case 'ArrowLeft':
                event.preventDefault();
                this.previousPage();
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.nextPage();
                break;
            case 'Home':
                event.preventDefault();
                this.goToPage(1);
                break;
            case 'End':
                event.preventDefault();
                this.goToPage(this.totalPages);
                break;
        }
    }

    // Public method for external navigation (from accordion)
    navigateToPage(pageNumber) {
        this.goToPage(pageNumber);
    }

    destroy() {
        // Clean up event listeners
        document.removeEventListener('keydown', this.handleKeyboard);
    }
}
