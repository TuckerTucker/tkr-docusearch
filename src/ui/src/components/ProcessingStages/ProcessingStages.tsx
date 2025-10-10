/**
 * ProcessingStages Component - DocuSearch UI
 * Provider: Agent 3 (Feature Components)
 * Contract: integration-contracts/processing-stages-contract.md
 *
 * Wave 2: Full implementation with animations and icons
 */

import React from 'react';
import type { ProcessingStage } from '../../lib/types';
import { cn } from '../../lib/utils';

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
 * Status icon components
 */
const StatusIcons = {
  completed: (
    <svg
      className="w-4 h-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2.5}
        d="M5 13l4 4L19 7"
      />
    </svg>
  ),
  'in-progress': (
    <svg
      className="w-4 h-4 animate-spin"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  ),
  pending: (
    <svg
      className="w-4 h-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" strokeWidth="2" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6l4 2" />
    </svg>
  ),
  error: (
    <svg
      className="w-4 h-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2.5}
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  ),
};

/**
 * Processing stages indicator component
 *
 * Displays the 4-stage processing pipeline with status indicators.
 * Shows which stages are completed, in-progress, pending, or error.
 *
 * Features:
 * - Animated status transitions
 * - Icon indicators for each status
 * - Progress connectors between stages
 * - Accessible with ARIA labels
 * - Responsive text sizing
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
  // Find current stage for screen reader announcement
  const currentStage = stages.find(s => s.status === 'in-progress');
  const completedCount = stages.filter(s => s.status === 'completed').length;
  const hasError = stages.some(s => s.status === 'error');

  return (
    <div
      className={cn('relative', className)}
      data-component="processing-stages"
      role="status"
      aria-live="polite"
      aria-atomic="true"
      aria-label={
        hasError
          ? `Processing error at ${stages.find(s => s.status === 'error')?.label}`
          : currentStage
          ? `Processing: ${currentStage.label}, ${completedCount} of ${stages.length} stages complete`
          : `Processing complete, all ${stages.length} stages finished`
      }
    >
      <div className="flex items-center gap-1">
        {stages.map((stage, index) => {
          const isLast = index === stages.length - 1;

          return (
            <React.Fragment key={stage.label}>
              {/* Stage item */}
              <div
                className="flex-1 min-w-0"
                role="listitem"
                aria-label={`${stage.label}: ${stage.status}`}
              >
                <div
                  className={cn(
                    'relative flex items-center gap-2 px-3 py-2 rounded-md',
                    'transition-all duration-200',
                    'border',
                    // Completed state
                    stage.status === 'completed' &&
                      'bg-green-50 border-green-200 text-green-800',
                    // In-progress state
                    stage.status === 'in-progress' &&
                      'bg-blue-50 border-blue-200 text-blue-800',
                    // Pending state
                    stage.status === 'pending' &&
                      'bg-gray-50 border-gray-200 text-gray-600',
                    // Error state
                    stage.status === 'error' &&
                      'bg-red-50 border-red-200 text-red-800'
                  )}
                >
                  {/* Icon */}
                  <div className="flex-shrink-0">
                    {StatusIcons[stage.status]}
                  </div>

                  {/* Label */}
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium truncate">
                      {stage.label}
                    </div>
                  </div>
                </div>
              </div>

              {/* Connector line */}
              {!isLast && (
                <div
                  className={cn(
                    'flex-shrink-0 h-0.5 w-2',
                    'transition-colors duration-300',
                    stage.status === 'completed'
                      ? 'bg-green-300'
                      : 'bg-gray-200'
                  )}
                  aria-hidden="true"
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
