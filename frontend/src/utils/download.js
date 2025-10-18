/**
 * Download Utilities
 *
 * Helper functions for downloading files (markdown, VTT, generic).
 *
 * Wave 1 - Foundation Agent
 */

/**
 * Download markdown file for a document
 * @param {string} docId - Document identifier
 * @param {HTMLElement} buttonElement - Button that triggered the download (for feedback)
 */
export async function downloadMarkdown(docId, buttonElement) {
    try {
        const url = `/documents/${docId}/markdown`;

        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = ''; // Filename from server
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Visual feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✓ Downloaded!';
            buttonElement.classList.add('success');

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
                buttonElement.classList.remove('success');
            }, 2000);
        }

        console.log('Markdown download initiated');
    } catch (err) {
        console.error('Failed to download markdown:', err);

        // Error feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✗ Failed';

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
            }, 2000);
        }
    }
}

/**
 * Download VTT file for an audio document
 * @param {string} docId - Document identifier
 * @param {HTMLElement} buttonElement - Button that triggered the download (for feedback)
 */
export async function downloadVTT(docId, buttonElement) {
    try {
        const url = `/documents/${docId}/vtt`;

        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = ''; // Filename from server
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Visual feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✓ Downloaded!';
            buttonElement.classList.add('success');

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
                buttonElement.classList.remove('success');
            }, 2000);
        }

        console.log('VTT download initiated');
    } catch (err) {
        console.error('Failed to download VTT:', err);

        // Error feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✗ Failed';

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
            }, 2000);
        }
    }
}

/**
 * Download text as a file
 * @param {string} text - Text content to download
 * @param {string} filename - Filename for download
 * @param {string} mimeType - MIME type (default: text/plain)
 */
export function downloadTextAsFile(text, filename, mimeType = 'text/plain') {
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up object URL
    URL.revokeObjectURL(url);

    console.log(`Downloaded: ${filename}`);
}

/**
 * Generic file download function
 * @param {string} url - URL to download from
 * @param {string} filename - Optional filename for download
 */
export function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    if (filename) {
        link.download = filename;
    }
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
