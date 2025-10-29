/**
 * BBoxController Module Exports
 *
 * Agent 8: BBoxController Integration Layer
 * Wave 1 - BBox Overlay React Implementation
 *
 * Barrel export for BBoxController orchestration layer.
 */

export { BBoxController } from './BBoxController';
export type { BBoxControllerProps } from './BBoxController';
export {
  transformStructureToBboxes,
  getOriginalDimensions,
  hasAnyBboxes,
} from './structureTransform';
