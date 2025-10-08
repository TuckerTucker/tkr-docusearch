/**
 * File Validator Module
 *
 * Validates file format, size, and provides processing time estimates.
 *
 * Provider: upload-logic-agent
 * Contract: ui-html.contract.md
 */

// Dynamic supported formats (loaded from worker /config endpoint)
let SUPPORTED_FORMATS = new Set([
    // Fallback formats (if fetch fails)
    'pdf', 'docx', 'pptx', 'xlsx', 'md', 'html', 'htm', 'xhtml', 'asciidoc',
    'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'webp',
    'csv', 'json',
    'vtt', 'wav', 'mp3',
    'xml'
]);

// Dynamic config from worker
let workerConfig = {
    maxFileSizeMB: 100,
    device: 'unknown',
    modelPrecision: 'unknown'
};

// Format types for processing estimation
const FORMAT_TYPES = {
    VISUAL: new Set(['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'webp']),
    TEXT: new Set(['docx', 'pptx', 'xlsx', 'md', 'html', 'htm', 'xhtml', 'asciidoc', 'csv', 'json', 'xml']),
    AUDIO: new Set(['vtt', 'wav', 'mp3'])
};

// File size limits (in bytes) - will be updated from worker config
let MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB (default)
const WARN_FILE_SIZE = 10 * 1024 * 1024;  // 10 MB

/**
 * Initialize file validator by fetching config from worker.
 * Should be called on page load.
 *
 * @param {string} workerUrl - Worker base URL (default: http://localhost:8002)
 * @returns {Promise<Object>} Worker configuration
 */
export async function initializeValidator(workerUrl = 'http://localhost:8002') {
    try {
        const response = await fetch(`${workerUrl}/config`);
        if (!response.ok) {
            throw new Error(`Failed to fetch config: ${response.status}`);
        }

        const config = await response.json();

        // Update supported formats (remove leading dots from extensions)
        SUPPORTED_FORMATS = new Set(
            config.supported_formats.map(ext => ext.startsWith('.') ? ext.substring(1) : ext)
        );

        // Update max file size
        MAX_FILE_SIZE = config.max_file_size_mb * 1024 * 1024;

        // Store worker config
        workerConfig = {
            maxFileSizeMB: config.max_file_size_mb,
            device: config.device,
            modelPrecision: config.model_precision
        };

        console.log('File validator initialized with worker config:', {
            supportedFormats: Array.from(SUPPORTED_FORMATS).sort(),
            maxFileSizeMB: workerConfig.maxFileSizeMB,
            device: workerConfig.device
        });

        return workerConfig;
    } catch (error) {
        console.error('Failed to load worker config, using fallback:', error);
        return workerConfig;
    }
}

/**
 * Get current worker configuration.
 *
 * @returns {Object} Worker config {maxFileSizeMB, device, modelPrecision}
 */
export function getWorkerConfig() {
    return { ...workerConfig };
}

/**
 * Get current supported formats.
 *
 * @returns {Array<string>} Array of supported extensions
 */
export function getSupportedFormats() {
    return Array.from(SUPPORTED_FORMATS).sort();
}

/**
 * Validate a file before upload.
 *
 * @param {File} file - File object to validate
 * @returns {Object} Validation result {valid: boolean, error?: string, warning?: string}
 */
export function validateFile(file) {
    // Check file exists
    if (!file) {
        return { valid: false, error: 'No file selected' };
    }

    // Extract extension
    const filename = file.name;
    const lastDot = filename.lastIndexOf('.');
    if (lastDot === -1) {
        return { valid: false, error: 'File has no extension' };
    }

    const extension = filename.substring(lastDot + 1).toLowerCase();

    // Check if format is supported
    if (!SUPPORTED_FORMATS.has(extension)) {
        return {
            valid: false,
            error: `Unsupported format: .${extension}`,
            supportedFormats: Array.from(SUPPORTED_FORMATS).sort()
        };
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const maxMB = (MAX_FILE_SIZE / (1024 * 1024)).toFixed(0);
        return {
            valid: false,
            error: `File too large: ${sizeMB} MB (max ${maxMB} MB)`
        };
    }

    // Warning for large files
    let warning = null;
    if (file.size > WARN_FILE_SIZE) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        warning = `Large file (${sizeMB} MB) - processing may take longer`;
    }

    return { valid: true, warning };
}

/**
 * Get format type for a file.
 *
 * @param {File} file - File object
 * @returns {string} Format type ('visual', 'text', 'audio', or 'unknown')
 */
export function getFormatType(file) {
    const extension = file.name.split('.').pop().toLowerCase();

    if (FORMAT_TYPES.VISUAL.has(extension)) return 'visual';
    if (FORMAT_TYPES.TEXT.has(extension)) return 'text';
    if (FORMAT_TYPES.AUDIO.has(extension)) return 'audio';

    return 'unknown';
}

/**
 * Estimate processing time for a file.
 *
 * @param {File} file - File object
 * @returns {number} Estimated processing time in seconds
 */
export function estimateProcessingTime(file) {
    const formatType = getFormatType(file);
    const fileSizeMB = file.size / (1024 * 1024);

    // Rough estimates based on format type
    // Visual formats: ~2.3s per page (assuming 1 page per MB for PDFs)
    // Text formats: ~0.24s per chunk (very fast)
    // Audio formats: depends on length, assume 1s per MB

    switch (formatType) {
        case 'visual':
            // Estimate pages: PDFs ~1 page/MB, images 1 page
            const extension = file.name.split('.').pop().toLowerCase();
            if (extension === 'pdf') {
                const estimatedPages = Math.max(1, Math.ceil(fileSizeMB));
                return estimatedPages * 2.3; // 2.3s per page
            } else {
                return 2.3; // Single image
            }

        case 'text':
            // Text-only is very fast
            const estimatedChunks = Math.max(1, Math.ceil(fileSizeMB * 10));
            return estimatedChunks * 0.24;

        case 'audio':
            // Rough estimate: 1s processing per MB
            return Math.max(1, fileSizeMB);

        default:
            return 5; // Unknown format, conservative estimate
    }
}

/**
 * Format file size for display.
 *
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size (e.g., "1.5 MB")
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const units = ['B', 'KB', 'MB', 'GB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`;
}

/**
 * Get human-readable format name.
 *
 * @param {File} file - File object
 * @returns {string} Format name (e.g., "PDF Document", "Markdown File")
 */
export function getFormatName(file) {
    const extension = file.name.split('.').pop().toLowerCase();

    const formatNames = {
        // Documents
        'pdf': 'PDF Document',
        'docx': 'Word Document',
        'pptx': 'PowerPoint Presentation',
        'xlsx': 'Excel Spreadsheet',
        'md': 'Markdown File',
        'html': 'HTML Document',
        'htm': 'HTML Document',
        'xhtml': 'XHTML Document',
        'asciidoc': 'AsciiDoc Document',
        // Images
        'png': 'PNG Image',
        'jpg': 'JPEG Image',
        'jpeg': 'JPEG Image',
        'tiff': 'TIFF Image',
        'bmp': 'BMP Image',
        'webp': 'WebP Image',
        // Data
        'csv': 'CSV Data',
        'json': 'JSON Data',
        // Audio
        'vtt': 'WebVTT Subtitles',
        'wav': 'WAV Audio',
        'mp3': 'MP3 Audio',
        // Specialized
        'xml': 'XML Document'
    };

    return formatNames[extension] || `${extension.toUpperCase()} File`;
}
