/**
 * WorkerStatus Component - DocuSearch UI
 * Provider: Wave 3 (Polish & Refinement)
 *
 * Displays processing worker health status
 */

import React, { useState, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { getWorkerStatus } from '../../services/workerService';
import type { WorkerStatus as WorkerStatusType } from '../../lib/types';

export interface WorkerStatusProps {
  /** CSS class name */
  className?: string;
}

/**
 * Worker status indicator component
 *
 * Shows worker health, device type, and status
 * Polls worker status every 5 seconds
 */
export function WorkerStatus({
  className,
}: WorkerStatusProps): React.ReactElement {
  const [status, setStatus] = useState<WorkerStatusType | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const workerStatus = await getWorkerStatus();
        setStatus(workerStatus);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to fetch worker status:', error);
        setStatus(null);
        setIsLoading(false);
      }
    };

    fetchStatus();

    // Poll every 5 seconds
    const interval = setInterval(fetchStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className={cn('flex items-center gap-2 px-3 py-1 rounded-full bg-muted', className)}>
        <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse" />
        <span className="text-xs text-muted-foreground">Loading...</span>
      </div>
    );
  }

  if (!status) {
    return (
      <div className={cn('flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 border border-red-200', className)}>
        <div className="w-2 h-2 rounded-full bg-red-500" />
        <span className="text-xs text-red-700 font-medium">Worker Offline</span>
      </div>
    );
  }

  const isHealthy = status.healthy && status.status === 'running';

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-1 rounded-full border',
        isHealthy
          ? 'bg-green-50 border-green-200'
          : 'bg-yellow-50 border-yellow-200',
        className
      )}
      title={`Device: ${status.device}${status.uptime_seconds ? ` • Uptime: ${Math.floor(status.uptime_seconds / 60)}m` : ''}`}
    >
      {/* Status indicator */}
      <div
        className={cn(
          'w-2 h-2 rounded-full',
          isHealthy ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
        )}
      />

      {/* Status text */}
      <div className="flex items-center gap-1.5">
        <span
          className={cn(
            'text-xs font-medium',
            isHealthy ? 'text-green-700' : 'text-yellow-700'
          )}
        >
          Worker
        </span>
        <span
          className={cn(
            'text-xs',
            isHealthy ? 'text-green-600' : 'text-yellow-600'
          )}
        >
          {isHealthy ? 'Online' : status.status}
        </span>
      </div>

      {/* Device badge */}
      {status.device && (
        <span
          className={cn(
            'text-xs px-1.5 py-0.5 rounded',
            isHealthy
              ? 'bg-green-100 text-green-700'
              : 'bg-yellow-100 text-yellow-700'
          )}
        >
          {status.device}
        </span>
      )}
    </div>
  );
}
