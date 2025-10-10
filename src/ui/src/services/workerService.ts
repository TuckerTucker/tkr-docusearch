/**
 * Worker Service - DocuSearch UI
 * Provider: Agent 6 (Services)
 * Consumers: Agent 5 (App)
 * Contract: integration-contracts/api-services-contract.md
 *
 * Wave 4: Real worker status API implementation
 */

import type { WorkerStatus } from '../lib/types';
import { API_CONFIG } from '../lib/constants';

/**
 * Fetch worker health and status
 *
 * @returns Promise resolving to worker status
 *
 * @example
 * const status = await workerService.getWorkerStatus();
 * console.log('Worker device:', status.device);
 */
export async function getWorkerStatus(): Promise<WorkerStatus> {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(API_CONFIG.timeout),
    });

    if (!response.ok) {
      throw new Error(`Worker status failed: ${response.status}`);
    }

    const data = await response.json();
    return data as WorkerStatus;
  } catch (error) {
    console.error('Failed to fetch worker status:', error);
    // Return offline status on error
    return {
      healthy: false,
      status: 'error',
      device: 'Unknown',
      last_error: error instanceof Error ? error.message : 'Connection failed',
    };
  }
}

/**
 * Check if worker is healthy and ready
 *
 * @returns Promise resolving to health check result
 *
 * @example
 * const isHealthy = await workerService.checkHealth();
 * if (!isHealthy) {
 *   console.warn('Worker is not healthy!');
 * }
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const status = await getWorkerStatus();
    return status.healthy && status.status === 'running';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
}
