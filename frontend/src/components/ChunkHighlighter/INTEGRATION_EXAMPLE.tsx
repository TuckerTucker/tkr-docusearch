/**
 * ChunkHighlighter Integration Example
 *
 * Agent 7: Chunk Highlighter Component
 * Wave 1 - BBox Overlay React Implementation
 *
 * Example showing how Agent 8 (BoundingBox Overlay) should integrate
 * with this ChunkHighlighter component for bidirectional highlighting.
 */

import React, { useState, useRef } from 'react';
import { ChunkHighlighter } from './ChunkHighlighter';
// import { BoundingBoxOverlay } from '../BoundingBoxOverlay'; // Agent 8 will create this

/**
 * Example Research View with Bidirectional Highlighting
 *
 * This demonstrates the expected integration between:
 * - ChunkHighlighter (Agent 7) - for markdown content
 * - BoundingBoxOverlay (Agent 8) - for document thumbnails
 */
export function ResearchViewExample() {
  // Shared state for bidirectional highlighting
  const [activeChunkId, setActiveChunkId] = useState<string | null>(null);
  const [hoveredChunkId, setHoveredChunkId] = useState<string | null>(null);

  // Refs for the containers
  const markdownContainerRef = useRef<HTMLDivElement>(null);
  const thumbnailContainerRef = useRef<HTMLDivElement>(null);

  /**
   * Handle chunk hover from markdown content
   * This will trigger bbox highlighting in Agent 8's component
   */
  const handleChunkHover = (chunkId: string | null) => {
    setHoveredChunkId(chunkId);
    // Agent 8's BoundingBoxOverlay will react to hoveredChunkId change
    // and highlight the corresponding bbox on the thumbnail
  };

  /**
   * Handle chunk click to make it active
   * Useful for citation navigation
   */
  const handleChunkClick = (chunkId: string) => {
    setActiveChunkId(chunkId);
    // Could also trigger additional actions like:
    // - Scroll to corresponding page in document viewer
    // - Show citation details in sidebar
    // - Highlight all related chunks
  };

  /**
   * Handle bbox hover from document thumbnail
   * Agent 8 will call this when user hovers over a bbox
   */
  const handleBBoxHover = (chunkId: string | null) => {
    setHoveredChunkId(chunkId);
    // ChunkHighlighter will react to hoveredChunkId change
    // and highlight the corresponding text chunk
  };

  /**
   * Handle bbox click from document thumbnail
   * Agent 8 will call this when user clicks a bbox
   */
  const handleBBoxClick = (chunkId: string) => {
    setActiveChunkId(chunkId);
    // ChunkHighlighter will scroll to and highlight the chunk
  };

  return (
    <div className="research-view">
      {/* Left side: Document thumbnail with bounding boxes */}
      <div className="research-view__thumbnail" ref={thumbnailContainerRef}>
        {/* Agent 8 will create this component */}
        {/* <BoundingBoxOverlay
          documentId="doc-123"
          pageNumber={1}
          activeChunkId={activeChunkId}
          hoveredChunkId={hoveredChunkId}
          onBBoxHover={handleBBoxHover}
          onBBoxClick={handleBBoxClick}
          chunks={[
            {
              chunkId: 'chunk-1',
              bbox: { x1: 72, y1: 100, x2: 540, y2: 150 },
              pageNumber: 1
            },
            // ... more chunks
          ]}
        /> */}
      </div>

      {/* Right side: Research results with highlighted chunks */}
      <div className="research-view__content">
        <ChunkHighlighter
          activeChunkId={activeChunkId}
          hoveredChunkId={hoveredChunkId}
          onChunkHover={handleChunkHover}
          onChunkClick={handleChunkClick}
          scrollOffset={80} // Account for fixed header
          scrollBehavior="smooth"
          autoAddChunkIds={true}
          chunkIdPrefix="chunk"
        >
          {/* Markdown content with citations */}
          <div className="research-results">
            <h1>Research Results</h1>

            <p data-chunk-id="chunk-1">
              The study shows significant results in the field of machine
              learning. According to the paper [1], the new approach improves
              accuracy by 15%.
            </p>

            <p data-chunk-id="chunk-2">
              Furthermore, the methodology described in [2] demonstrates how
              this technique can be applied to real-world scenarios with
              minimal computational overhead.
            </p>

            <h2>Methodology</h2>

            <p data-chunk-id="chunk-3">
              The researchers employed a novel architecture that combines
              transformers with convolutional layers [3], resulting in both
              improved performance and reduced training time.
            </p>
          </div>
        </ChunkHighlighter>
      </div>
    </div>
  );
}

/**
 * Simpler example: Just the ChunkHighlighter without BBox
 */
export function SimpleChunkExample() {
  const [activeChunk, setActiveChunk] = useState<string | null>(null);

  return (
    <ChunkHighlighter
      activeChunkId={activeChunk}
      onChunkHover={(chunkId) => console.log('Hovered:', chunkId)}
      onChunkClick={setActiveChunk}
      scrollOffset={60}
    >
      <article>
        <h1>Article Title</h1>
        <p>First paragraph with important information.</p>
        <p>Second paragraph with more details.</p>
        <p>Third paragraph with conclusions.</p>
      </article>
    </ChunkHighlighter>
  );
}

/**
 * Advanced example: Using the hook directly
 */
export function AdvancedChunkExample() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeChunkId, setActiveChunkId] = useState<string | null>(null);

  // Import the hook when needed
  // const { highlightChunk, scrollToChunk, clearHighlight } = useChunkHighlight({
  //   containerRef,
  //   activeChunkId,
  //   onChunkHover: (chunkId) => console.log('Hovered:', chunkId),
  // });

  const handleCitationClick = async (citationNumber: number) => {
    const chunkId = `chunk-${citationNumber}`;
    setActiveChunkId(chunkId);

    // Programmatically scroll to the chunk
    // await scrollToChunk(chunkId, { behavior: 'smooth', offset: 80 });
  };

  return (
    <div>
      <div className="citations-list">
        <button onClick={() => handleCitationClick(1)}>Go to Citation 1</button>
        <button onClick={() => handleCitationClick(2)}>Go to Citation 2</button>
        <button onClick={() => handleCitationClick(3)}>Go to Citation 3</button>
      </div>

      <div ref={containerRef}>
        <p data-chunk-id="chunk-1">Content referenced by citation 1</p>
        <p data-chunk-id="chunk-2">Content referenced by citation 2</p>
        <p data-chunk-id="chunk-3">Content referenced by citation 3</p>
      </div>
    </div>
  );
}

/**
 * Agent 8 Integration Checklist:
 *
 * 1. Create BoundingBoxOverlay component that accepts:
 *    - activeChunkId: string | null
 *    - hoveredChunkId: string | null
 *    - onBBoxHover: (chunkId: string | null) => void
 *    - onBBoxClick: (chunkId: string) => void
 *    - chunks: Array<{ chunkId, bbox, pageNumber }>
 *
 * 2. Implement bidirectional highlighting:
 *    - When hoveredChunkId changes, highlight corresponding bbox
 *    - When bbox is hovered, call onBBoxHover with chunkId
 *
 * 3. Use Agent 3's coordinate scaling utilities:
 *    - Scale bbox coordinates from original to display size
 *    - Position bboxes over thumbnail image
 *
 * 4. Add visual feedback:
 *    - Active bbox: solid border with highlight
 *    - Hovered bbox: subtle border with semi-transparent fill
 *    - Smooth transitions between states
 *
 * 5. Ensure accessibility:
 *    - ARIA labels for bboxes
 *    - Keyboard navigation
 *    - Focus management
 *
 * 6. Test integration:
 *    - Hover chunk → bbox highlights
 *    - Hover bbox → chunk highlights
 *    - Click chunk → bbox becomes active
 *    - Click bbox → scrolls to chunk
 */

export default ResearchViewExample;
