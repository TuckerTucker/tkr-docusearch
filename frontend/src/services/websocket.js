/**
 * WebSocket Service - WebSocket connection manager
 *
 * Manages WebSocket connection with automatic reconnection, exponential backoff,
 * and message handling.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/hooks.contract.md
 */

/**
 * WebSocket connection manager class
 */
export class WebSocketManager {
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      reconnectInterval: options.reconnectInterval || 3000,
      maxReconnectAttempts: options.maxReconnectAttempts || 10,
      onMessage: options.onMessage || null,
      onOpen: options.onOpen || null,
      onClose: options.onClose || null,
      onError: options.onError || null,
    };

    this.ws = null;
    this.reconnectAttempts = 0;
    this.isIntentionallyClosed = false;
    this.reconnectTimeout = null;
    this.messageHandlers = []; // Additional message handlers (for one-time requests)
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    this.isIntentionallyClosed = false;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected');
        this.reconnectAttempts = 0;
        if (this.options.onOpen) {
          this.options.onOpen();
        }
      };

      this.ws.onmessage = (event) => {
        // Call all registered message handlers
        this.messageHandlers.forEach(handler => {
          try {
            handler(event);
          } catch (err) {
            console.error('[WebSocket] Message handler error:', err);
          }
        });

        // Call primary message handler
        if (this.options.onMessage) {
          this.options.onMessage(event);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        if (this.options.onError) {
          this.options.onError(error);
        }
      };

      this.ws.onclose = () => {
        // Only log if not an intentional close (reduces React Strict Mode noise)
        if (!this.isIntentionallyClosed) {
          console.log('[WebSocket] Connection closed unexpectedly');
          this.scheduleReconnect();
        }

        if (this.options.onClose) {
          this.options.onClose();
        }
      };
    } catch (error) {
      console.error('[WebSocket] Failed to create connection:', error);
      if (!this.isIntentionallyClosed) {
        this.scheduleReconnect();
      }
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    this.isIntentionallyClosed = true;

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      // Remove error handlers before closing to avoid "connection closed before established" errors
      // This happens in React Strict Mode when components mount/unmount/remount
      this.ws.onerror = null;
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Send data through WebSocket
   *
   * @param {string|Object} data - Data to send
   */
  send(data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] Cannot send - not connected');
      return;
    }

    const message = typeof data === 'string' ? data : JSON.stringify(data);
    console.log('[WebSocket] Sending message:', message.substring(0, 200));
    this.ws.send(message);
  }

  /**
   * Check if connected
   *
   * @returns {boolean} True if connected
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnect attempts reached');
      return;
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, ..., max 30s
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Get current reconnect attempts
   *
   * @returns {number} Number of reconnect attempts
   */
  getReconnectAttempts() {
    return this.reconnectAttempts;
  }

  /**
   * Add a message handler (for one-time requests like registration)
   *
   * @param {Function} handler - Message handler function
   */
  addMessageHandler(handler) {
    this.messageHandlers.push(handler);
  }

  /**
   * Remove a message handler
   *
   * @param {Function} handler - Message handler to remove
   */
  removeMessageHandler(handler) {
    const index = this.messageHandlers.indexOf(handler);
    if (index > -1) {
      this.messageHandlers.splice(index, 1);
    }
  }
}
