/**
 * AudioPlayer Component
 *
 * HTML5 audio player with VTT caption support, markdown fallback, and chunk sync.
 * Complete reimplementation ported from src/frontend/audio-player.js
 *
 * Features:
 * - Dual caption system: VTT (priority) + Markdown segments (fallback)
 * - Album art with progressive loading
 * - Bidirectional sync with accordion
 * - Throttled updates for performance
 * - Responsive design
 *
 * Wave 3 - Complete Audio Player Reimplementation
 */

import { useState, useRef, useEffect, useCallback, useImperativeHandle, forwardRef } from 'react';
import AlbumArt from './AlbumArt.jsx';

/**
 * Audio player with album art and dual caption system
 *
 * Exposes seekTo method via ref for accordion click-to-seek integration.
 *
 * @param {Object} props - Component props
 * @param {Object} props.document - Document with audio metadata
 * @param {Array} [props.chunks=[]] - Text chunks with timestamps for sync
 * @param {Function} [props.onTimeUpdate] - Callback for time updates (for accordion sync)
 * @param {React.Ref} ref - Forwarded ref to expose seekTo method
 */
const AudioPlayer = forwardRef(function AudioPlayer({ document, chunks = [], onTimeUpdate }, ref) {
  const audioRef = useRef(null);
  const trackRef = useRef(null);
  const [currentCaption, setCurrentCaption] = useState('');
  const [isLoaded, setIsLoaded] = useState(false);
  const [markdownSegments, setMarkdownSegments] = useState([]);

  // Throttle accordion sync updates
  const lastSyncTimeRef = useRef(0);
  const lastActiveChunkIdRef = useRef(null);
  const lastCaptionTimeRef = useRef(-1);
  const SYNC_THROTTLE_MS = 300;

  const docId = document?.doc_id;
  const metadata = document?.metadata || {};
  const rawMetadata = metadata.raw_metadata || {};

  // Audio and VTT URLs
  const audioUrl = `/documents/${docId}/audio`;
  const vttUrl = metadata.vtt_available ? `/documents/${docId}/vtt` : null;
  const coverArtUrl = metadata.has_album_art ? metadata.album_art_url : null;

  // Fetch and parse markdown for caption fallback
  useEffect(() => {
    if (!metadata.markdown_available || metadata.vtt_available) {
      return; // Skip if no markdown or VTT is available
    }

    const fetchMarkdown = async () => {
      try {
        const response = await fetch(`/documents/${docId}/markdown`);
        if (response.ok) {
          const markdown = await response.text();
          const segments = parseMarkdownSegments(markdown);
          setMarkdownSegments(segments);
          console.log(`[AudioPlayer] Loaded ${segments.length} markdown caption segments`);
        }
      } catch (err) {
        console.error('[AudioPlayer] Error fetching markdown:', err);
      }
    };

    fetchMarkdown();
  }, [docId, metadata.markdown_available, metadata.vtt_available]);

  /**
   * Parse markdown for [time: X-Y] segments
   * Returns array of {startTime, endTime, text}
   */
  const parseMarkdownSegments = (markdown) => {
    if (!markdown) return [];

    const segments = [];
    const timeRegex = /\[time:\s*([\d.]+)-([\d.]+)\]/g;
    const matches = [];
    let match;

    // Collect all timestamp positions
    while ((match = timeRegex.exec(markdown)) !== null) {
      matches.push({
        index: match.index,
        startTime: parseFloat(match[1]),
        endTime: parseFloat(match[2]),
        fullMatch: match[0]
      });
    }

    // Extract text between timestamps
    for (let i = 0; i < matches.length; i++) {
      const currentMatch = matches[i];
      const nextMatch = matches[i + 1];

      const textStart = currentMatch.index + currentMatch.fullMatch.length;
      const textEnd = nextMatch ? nextMatch.index : markdown.length;
      const text = markdown.substring(textStart, textEnd).trim();

      if (text) {
        segments.push({
          startTime: currentMatch.startTime,
          endTime: currentMatch.endTime,
          text
        });
      }
    }

    return segments;
  };

  // Handle audio loaded
  const handleLoaded = useCallback(() => {
    console.log('[AudioPlayer] Audio loaded:', audioRef.current?.duration);
    setIsLoaded(true);
  }, []);

  // Handle audio error
  const handleError = useCallback((e) => {
    console.error('[AudioPlayer] Audio load error:', e);
    console.error('[AudioPlayer] Error details:', audioRef.current?.error);
  }, []);

  // Handle VTT cue changes
  const handleCueChange = useCallback(() => {
    const track = trackRef.current?.track;
    console.log('[AudioPlayer] Cue change event fired, track:', track);
    if (track && track.activeCues && track.activeCues.length > 0) {
      const activeCue = track.activeCues[0];
      console.log('[AudioPlayer] Active cue:', activeCue.text);
      setCurrentCaption(activeCue.text);
    } else {
      console.log('[AudioPlayer] No active cues');
      setCurrentCaption('');
    }
  }, []);

  // Set up VTT track cuechange event listener
  useEffect(() => {
    const trackElement = trackRef.current;
    if (!trackElement) return;

    const track = trackElement.track;
    if (!track) return;

    // Handle track load event to ensure track is ready before setting mode
    const handleTrackLoad = () => {
      console.log('[AudioPlayer] Track loaded, readyState:', track.readyState);
      // Explicitly set track mode to 'showing' to enable cuechange events
      // Without this, the track defaults to 'disabled' and cues won't fire
      track.mode = 'showing';
      console.log('[AudioPlayer] Track mode set to:', track.mode);
    };

    // Check if track is already loaded
    if (track.readyState === 2) { // LOADED = 2
      handleTrackLoad();
    } else {
      // Wait for track to load
      trackElement.addEventListener('load', handleTrackLoad);
    }

    // Set up cuechange listener
    track.addEventListener('cuechange', handleCueChange);

    return () => {
      trackElement.removeEventListener('load', handleTrackLoad);
      track.removeEventListener('cuechange', handleCueChange);
    };
  }, [handleCueChange, vttUrl]);

  // Handle time updates (for accordion sync and markdown captions)
  const handleTimeUpdate = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const currentTime = audio.currentTime;
    const now = Date.now();

    // Caption display: Prefer VTT (via handleCueChange), fallback to markdown
    // Only use markdown parsing if VTT is not available
    if (!metadata.vtt_available && markdownSegments.length > 0) {
      const activeSegment = markdownSegments.find(seg =>
        currentTime >= seg.startTime && currentTime < seg.endTime
      );

      if (activeSegment) {
        // Only update if changed (avoid unnecessary re-renders)
        if (Math.floor(activeSegment.startTime) !== lastCaptionTimeRef.current) {
          setCurrentCaption(activeSegment.text);
          lastCaptionTimeRef.current = Math.floor(activeSegment.startTime);
        }
      } else {
        // Clear caption when no active segment
        if (currentCaption !== '') {
          setCurrentCaption('');
          lastCaptionTimeRef.current = -1;
        }
      }
    }
    // Note: When VTT is available, captions are handled by handleCueChange()

    // Throttle accordion sync
    if (now - lastSyncTimeRef.current < SYNC_THROTTLE_MS) {
      return;
    }

    // Find active chunk for accordion sync
    if (chunks && chunks.length > 0 && onTimeUpdate) {
      let activeChunk = null;

      // Try to find chunk with start_time/end_time fields
      activeChunk = chunks.find(chunk =>
        chunk.has_timestamps &&
        chunk.start_time !== null &&
        chunk.end_time !== null &&
        currentTime >= chunk.start_time &&
        currentTime < chunk.end_time
      );

      // Fallback: Parse timestamps from text content
      if (!activeChunk) {
        for (const chunk of chunks) {
          const match = chunk.text_content?.match(/^\[time:\s*([\d.]+)-([\d.]+)\]/);
          if (match) {
            const startTime = parseFloat(match[1]);
            const endTime = parseFloat(match[2]);

            if (currentTime >= startTime && currentTime < endTime) {
              activeChunk = chunk;
              break;
            }
          }
        }
      }

      // Notify accordion if chunk changed
      if (activeChunk &&
          activeChunk.chunk_id !== lastActiveChunkIdRef.current) {
        console.log(`[Audio→Accordion] Active chunk: ${activeChunk.chunk_id} at ${currentTime.toFixed(2)}s`);
        onTimeUpdate(activeChunk);
        lastActiveChunkIdRef.current = activeChunk.chunk_id;
        lastSyncTimeRef.current = now;
      }
    }
  }, [chunks, onTimeUpdate, metadata.vtt_available, markdownSegments, currentCaption]);

  // Seek to specific time (for accordion click-to-seek)
  const seekTo = useCallback((timeInSeconds) => {
    const audio = audioRef.current;
    if (!audio) return;

    // Validation
    if (typeof timeInSeconds !== 'number' || isNaN(timeInSeconds)) {
      console.error(`[AudioPlayer] Invalid seek time: ${timeInSeconds}`);
      return;
    }

    if (timeInSeconds < 0) {
      console.warn(`[AudioPlayer] Seek time cannot be negative: ${timeInSeconds}, clamping to 0`);
      timeInSeconds = 0;
    }

    // Check if duration is available
    if (!audio.duration || isNaN(audio.duration)) {
      console.warn('[AudioPlayer] Audio duration not yet available, deferring seek');
      // Defer seek until metadata is loaded
      const handleLoadedMetadata = () => {
        seekTo(timeInSeconds);
        audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      };
      audio.addEventListener('loadedmetadata', handleLoadedMetadata);
      return;
    }

    if (timeInSeconds > audio.duration) {
      console.warn(`[AudioPlayer] Seek time ${timeInSeconds}s exceeds duration ${audio.duration}s, clamping`);
      timeInSeconds = audio.duration - 0.1;
    }

    audio.currentTime = timeInSeconds;

    // Auto-play after seek (optional)
    if (audio.paused) {
      audio.play().catch(err => {
        console.warn('[AudioPlayer] Auto-play prevented:', err);
      });
    }

    console.log(`[AudioPlayer] Seeked to ${timeInSeconds.toFixed(2)}s`);
  }, []);

  // Expose seekTo method via ref for parent components (React-idiomatic)
  useImperativeHandle(ref, () => ({
    seekTo
  }), [seekTo]);

  // Format time display
  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '--:--';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${minutes}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div className="audio-container">
      <div className="audio-header">
        <h2>Audio Playback</h2>
        <div className="audio-metadata">
          {rawMetadata.title && (
            <div className="metadata-item">
              <strong>Title:</strong> {rawMetadata.title}
            </div>
          )}
          {rawMetadata.artist && (
            <div className="metadata-item">
              <strong>Artist:</strong> {rawMetadata.artist}
            </div>
          )}
          {rawMetadata.album && (
            <div className="metadata-item">
              <strong>Album:</strong> {rawMetadata.album}
            </div>
          )}
          {rawMetadata.duration_seconds && (
            <div className="metadata-item">
              <strong>Duration:</strong> {formatTime(rawMetadata.duration_seconds)}
            </div>
          )}
        </div>
      </div>

      <AlbumArt
        coverArtUrl={coverArtUrl}
        altText={rawMetadata.title ? `Album art for ${rawMetadata.title}` : 'Album art'}
        currentCaption={currentCaption}
      />

      <div className="audio-player-wrapper">
        <audio
          ref={audioRef}
          controls
          className="audio-element"
          preload="metadata"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoaded}
          onError={handleError}
        >
          <source src={audioUrl} type="audio/mpeg" />
          {vttUrl && (
            <track
              ref={trackRef}
              kind="captions"
              src={vttUrl}
              srcLang="en"
              label="English"
              default
            />
          )}
          Your browser does not support the audio element.
        </audio>
      </div>
    </div>
  );
});

export default AudioPlayer;
