/**
 * AlbumArt Component
 *
 * Displays album art for audio files with fallback to default SVG.
 * Supports caption overlay for VTT subtitles.
 *
 * Wave 2 - Details Agent
 */

import { useState } from 'react';
import { DEFAULT_ALBUM_ART_SVG } from '../../utils/assets.js';

/**
 * Album art display with caption overlay
 *
 * @param {Object} props - Component props
 * @param {string} [props.coverArtUrl] - URL to album art image
 * @param {string} [props.altText='Album art'] - Alt text for image
 * @param {string} [props.currentCaption] - Current VTT caption to overlay
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

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    console.warn('[AlbumArt] Failed to load album art, using default SVG');
    setIsLoading(false);
    setHasError(true);
  };

  // Determine which image to display
  const imageSrc = (coverArtUrl && !hasError) ? coverArtUrl : DEFAULT_ALBUM_ART_SVG;
  const imageClass = `album-art-image ${isLoading ? 'loading' : 'loaded'} ${className}`;

  return (
    <div className="album-art-container">
      <img
        src={imageSrc}
        alt={altText}
        className={imageClass}
        onLoad={handleLoad}
        onError={handleError}
      />

      {currentCaption && (
        <div className="album-art-caption" aria-live="polite">
          {currentCaption}
        </div>
      )}
    </div>
  );
}
