/**
 * AlbumArt Component
 *
 * Displays album art for audio files with fallback to default SVG.
 * Supports caption overlay for VTT/markdown subtitles.
 *
 * Features:
 * - Progressive loading with opacity transition
 * - Error fallback to default SVG
 * - Responsive sizing (300px desktop / 200px mobile)
 * - Caption overlay with backdrop blur
 *
 * Wave 3 - Complete Audio Player Reimplementation
 */

import { useState, useEffect } from 'react';
import { DEFAULT_ALBUM_ART_SVG } from '../../utils/assets.js';

/**
 * Album art display with caption overlay
 *
 * @param {Object} props - Component props
 * @param {string} [props.coverArtUrl] - URL to album art image
 * @param {string} [props.altText='Album art'] - Alt text for image
 * @param {string} [props.currentCaption] - Current caption to overlay (from VTT or markdown)
 * @param {string} [props.className=''] - Additional CSS classes
 */
export default function AlbumArt({
  coverArtUrl,
  altText = 'Album art',
  currentCaption,
  className = ''
}) {
  const [isLoading, setIsLoading] = useState(!!coverArtUrl);
  const [hasError, setHasError] = useState(false);

  // Reset loading state when coverArtUrl changes
  useEffect(() => {
    if (coverArtUrl) {
      setIsLoading(true);
      setHasError(false);
    }
  }, [coverArtUrl]);

  const handleLoad = () => {
    console.log('[AlbumArt] Album art loaded successfully');
    setIsLoading(false);
  };

  const handleError = () => {
    console.warn('[AlbumArt] Failed to load album art, using default SVG');
    setIsLoading(false);
    setHasError(true);
  };

  // Determine which image to display
  const imageSrc = (coverArtUrl && !hasError) ? coverArtUrl : DEFAULT_ALBUM_ART_SVG;
  const imageClass = `album-art ${isLoading ? 'loading' : 'loaded'} ${className}`;

  return (
    <div className="album-art-container">
      <img
        src={imageSrc}
        alt={altText}
        className={imageClass}
        loading="lazy"
        onLoad={handleLoad}
        onError={handleError}
      />

      {/* Caption overlay - shown only when caption text exists */}
      <div className={`current-caption ${currentCaption ? 'active' : ''}`} aria-live="polite">
        {currentCaption}
      </div>
    </div>
  );
}
