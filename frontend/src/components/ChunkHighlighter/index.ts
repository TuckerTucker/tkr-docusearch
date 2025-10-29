/**
 * ChunkHighlighter Module
 *
 * Agent 7: Chunk Highlighter Component
 * Wave 1 - BBox Overlay React Implementation
 *
 * Barrel export for the ChunkHighlighter component and related utilities.
 * Provides chunk highlighting, hover detection, and smooth scrolling for markdown content.
 *
 * @example
 * ```typescript
 * import { ChunkHighlighter, useChunkHighlight, scrollToChunk } from '@/components/ChunkHighlighter';
 * ```
 */

// Component exports
export { ChunkHighlighter } from './ChunkHighlighter';
export type { ChunkHighlighterProps } from './ChunkHighlighter';

// Hook exports
export { useChunkHighlight } from './useChunkHighlight';
export type {
  UseChunkHighlightOptions,
  UseChunkHighlightResult,
} from './useChunkHighlight';

// Utility exports
export {
  scrollToChunk,
  getChunkRect,
  isChunkVisible,
} from './scrollToChunk';
export type {
  ScrollToChunkOptions,
  ScrollResult,
} from './scrollToChunk';

// Default export
export { ChunkHighlighter as default } from './ChunkHighlighter';
