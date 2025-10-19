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

  /**
   * Register upload batch and wait for response
   *
   * @param {Array<{filename: string, size: number}>} files - Files to register
   * @returns {Promise<Array<{filename: string, doc_id: string, expected_size: number}>>} Registrations
   */
  const registerUploadBatch = (files) => {
    return new Promise((resolve, reject) => {
      if (!wsRef.current || !isConnected) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      console.log('📤 Sending registration request for', files.length, 'files');

      let timeoutId;

      // Create one-time message handler for registration response
      const handleRegistrationResponse = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Registration handler received:', data.type);

          if (data.type === 'upload_batch_registered') {
            console.log('✅ Registration response received:', data.registrations.length, 'doc_ids');
            // Remove this temporary handler
            wsRef.current.removeMessageHandler(handleRegistrationResponse);
            clearTimeout(timeoutId);
            resolve(data.registrations);
          } else if (data.type === 'error') {
            console.error('❌ Registration error:', data.message);
            wsRef.current.removeMessageHandler(handleRegistrationResponse);
            clearTimeout(timeoutId);
            reject(new Error(data.message || 'Registration failed'));
          }
        } catch (err) {
          console.error('Error parsing registration response:', err);
          // Not a registration response, ignore
        }
      };

      // Add temporary message handler
      wsRef.current.addMessageHandler(handleRegistrationResponse);

      // Send registration request
      wsRef.current.send({
        type: 'register_upload_batch',
        files: files.map(f => ({ filename: f.name, size: f.size }))
      });

      // Timeout after 10 seconds
      timeoutId = setTimeout(() => {
        console.error('⏱️ Registration request timeout after 10s');
        wsRef.current.removeMessageHandler(handleRegistrationResponse);
        reject(new Error('Registration request timeout'));
      }, 10000);
    });
  };

  return {
    send,
    registerUploadBatch,
    isConnected,
    reconnectAttempts,
  };
}
