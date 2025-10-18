/**
 * Clipboard Utilities
 *
 * Helper functions for copying text to clipboard with visual feedback.
 *
 * Wave 1 - Foundation Agent
 */

/**
 * Copy text to clipboard and provide visual feedback
 * @param {string} text - Text to copy
 * @param {HTMLElement} buttonElement - Button that triggered the copy (for feedback)
 * @returns {Promise<boolean>} - True if successful
 */
export async function copyToClipboard(text, buttonElement) {
    try {
        await navigator.clipboard.writeText(text);

        // Visual feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✓ Copied!';
            buttonElement.classList.add('success');

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
                buttonElement.classList.remove('success');
            }, 2000);
        }

        console.log('Text copied to clipboard');
        return true;
    } catch (err) {
        console.error('Failed to copy to clipboard:', err);

        // Fallback visual feedback
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '✗ Failed';

            setTimeout(() => {
                buttonElement.innerHTML = originalText;
            }, 2000);
        }

        return false;
    }
}

/**
 * Strip YAML frontmatter from markdown content
 * @param {string} markdown - Markdown content with frontmatter
 * @returns {string} - Markdown without frontmatter
 */
export function stripFrontmatter(markdown) {
    const lines = markdown.split('\n');

    // Check if starts with frontmatter delimiter
    if (lines[0] === '---') {
        // Find ending delimiter
        const endIndex = lines.findIndex((line, index) => index > 0 && line === '---');

        if (endIndex !== -1) {
            // Return everything after the frontmatter
            return lines.slice(endIndex + 1).join('\n').trim();
        }
    }

    // No frontmatter found, return as-is
    return markdown;
}
