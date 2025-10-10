/**
 * ProcessingStages Component - DocuSearch UI
 * Provider: Agent 3 (Feature Components)
 * Contract: integration-contracts/processing-stages-contract.md
 *
 * Wave 1: Stub with correct signature
 * Wave 2: Full implementation with animations
 */

import React from 'react';
import type { ProcessingStage } from '../../lib/types';

/**
 * Props for ProcessingStages component
 */
export interface ProcessingStagesProps {
  /** Array of 4 processing stages */
  stages: ProcessingStage[];
  /** Optional CSS class name */
  className?: string;
}

/**
 * Processing stages indicator component
 *
 * Displays the 4-stage processing pipeline with status indicators.
 * Shows which stages are completed, in-progress, pending, or error.
 *
 * Required stages (in order):
 * 1. "Upload"
 * 2. "Transcribe Audio"
 * 3. "Embeddings"
 * 4. "Finalizing"
 *
 * @param props - Component props
 *
 * @example
 * <ProcessingStages
 *   stages={[
 *     { label: 'Upload', status: 'completed' },
 *     { label: 'Transcribe Audio', status: 'in-progress' },
 *     { label: 'Embeddings', status: 'pending' },
 *     { label: 'Finalizing', status: 'pending' },
 *   ]}
 * />
 */
export function ProcessingStages({
  stages,
  className,
}: ProcessingStagesProps): React.ReactElement {
  // Wave 1 stub - basic rendering
  return (
    <div className={className} data-component="processing-stages">
      <div className="flex gap-2">
        {stages.map((stage) => (
          <div
            key={stage.label}
            className="flex-1 text-xs"
            data-status={stage.status}
          >
            <div
              className={`
                px-2 py-1 rounded text-center
                ${stage.status === 'completed' ? 'bg-green-100 text-green-800' : ''}
                ${stage.status === 'in-progress' ? 'bg-blue-100 text-blue-800' : ''}
                ${stage.status === 'pending' ? 'bg-gray-100 text-gray-600' : ''}
                ${stage.status === 'error' ? 'bg-red-100 text-red-800' : ''}
              `}
            >
              {stage.label}
            </div>
          </div>
        ))}
      </div>
      {/* Wave 2: Add animations, icons, progress indicators */}
    </div>
  );
}
