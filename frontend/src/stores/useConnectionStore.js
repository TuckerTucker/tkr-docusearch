/**
 * Connection Store - WebSocket connection state
 *
 * Tracks WebSocket connection status with Zustand.
 * No persistence - connection state should not persist across sessions.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/stores.contract.md
 */

import { create } from 'zustand';

/**
 * Connection store for WebSocket status
 */
export const useConnectionStore = create((set) => ({
  // State
  status: 'disconnected', // 'connected' | 'disconnected' | 'reconnecting'
  lastConnected: null,
  reconnectAttempts: 0,

  // Actions
  setConnected: () =>
    set({
      status: 'connected',
      lastConnected: new Date(),
      reconnectAttempts: 0,
    }),

  setDisconnected: () =>
    set({
      status: 'disconnected',
    }),

  setReconnecting: (attempts) =>
    set({
      status: 'reconnecting',
      reconnectAttempts: attempts,
    }),

  reset: () =>
    set({
      status: 'disconnected',
      lastConnected: null,
      reconnectAttempts: 0,
    }),
}));
