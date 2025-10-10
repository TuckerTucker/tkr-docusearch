/**
 * Worker Service - DocuSearch UI
 * Provider: Agent 6 (Services)
 * Consumers: Agent 5 (App)
 * Contract: integration-contracts/api-services-contract.md
 *
 * Wave 1-3: Mock implementation
 * Wave 4: Replace with real worker status API
 */

import type { WorkerStatus } from '../lib/types';
import { getMockWorkerStatus } from '../lib/mockData';
import { delay } from '../lib/utils';

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
  // Simulate network delay
  await delay(150);

  // Mock implementation
  const status = getMockWorkerStatus();

  console.log('[Mock] Worker status:', status);

  // In Wave 4, this will be:
  // const response = await fetch('/health');
  // return await response.json();

  return status;
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

/**
 * Restart the worker (admin operation)
 *
 * @returns Promise resolving to success boolean
 *
 * @example
 * const success = await workerService.restartWorker();
 */
export async function restartWorker(): Promise<boolean> {
  // Simulate network delay
  await delay(1000);

  // Mock implementation
  console.log('[Mock] Restarting worker...');

  // In Wave 4, this will be:
  // const response = await fetch('/admin/restart', { method: 'POST' });
  // return response.ok;

  return true;
}
