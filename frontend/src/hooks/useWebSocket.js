/**
 * useWebSocket Hook - React hook for WebSocket connection
 *
 * Manages WebSocket connection with automatic reconnection and integration
 * with connection store.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/hooks.contract.md
 */

import { useEffect, useRef, useState } from 'react';
import { WebSocketManager } from '../services/websocket.js';
import { useConnectionStore } from '../stores/useConnectionStore.js';

/**
 * Custom hook for WebSocket connection
 *
 * @param {string} url - WebSocket URL
 * @param {Object} options - Connection options
 * @param {Function} [options.onMessage] - Message handler
 * @param {Function} [options.onOpen] - Open handler
 * @param {Function} [options.onClose] - Close handler
 * @param {Function} [options.onError] - Error handler
 * @param {number} [options.reconnectInterval] - Reconnect interval in ms
 * @param {number} [options.maxReconnectAttempts] - Max reconnect attempts
 * @returns {Object} WebSocket interface
 */
export function useWebSocket(url, options = {}) {
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Get connection store actions
  const setConnected = useConnectionStore((state) => state.setConnected);
  const setDisconnected = useConnectionStore((state) => state.setDisconnected);
  const setReconnecting = useConnectionStore((state) => state.setReconnecting);

  useEffect(() => {
    // Create WebSocket manager
    wsRef.current = new WebSocketManager(url, {
      reconnectInterval: options.reconnectInterval || 3000,
      maxReconnectAttempts: options.maxReconnectAttempts || 10,
      onMessage: options.onMessage,
      onOpen: () => {
        setIsConnected(true);
        setReconnectAttempts(0);
        setConnected();
        if (options.onOpen) {
          options.onOpen();
        }
      },
      onClose: () => {
        setIsConnected(false);
        setDisconnected();
        if (options.onClose) {
          options.onClose();
        }
      },
      onError: options.onError,
    });

    // Connect on mount
    wsRef.current.connect();

    // Track reconnect attempts
    const checkReconnectInterval = setInterval(() => {
      if (wsRef.current) {
        const attempts = wsRef.current.getReconnectAttempts();
        if (attempts > 0) {
          setReconnectAttempts(attempts);
          setReconnecting(attempts);
        }
      }
    }, 1000);

    // Cleanup on unmount
    return () => {
      clearInterval(checkReconnectInterval);
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, [url]); // Only recreate if URL changes

  /**
   * Send data through WebSocket
   *
   * @param {string|Object} data - Data to send
   */
  const send = (data) => {
    if (wsRef.current) {
      wsRef.current.send(data);
    }
  };

  return {
    send,
    isConnected,
    reconnectAttempts,
  };
}
