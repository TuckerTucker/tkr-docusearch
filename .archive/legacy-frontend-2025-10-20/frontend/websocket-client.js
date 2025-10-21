/**
 * WebSocketClient - WebSocket connection manager
 *
 * Manages WebSocket connection to worker with auto-reconnect,
 * message parsing, and event emission.
 *
 * Provider: library-agent (Wave 1)
 * Contract: integration-contracts/websocket.contract.md
 */

/**
 * WebSocket Client with auto-reconnect
 */
export class WebSocketClient {
  /**
   * Create WebSocket client
   * @param {string} url - WebSocket URL (e.g., ws://localhost:8002/ws)
   */
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 32000; // 32 seconds max
    this.reconnectTimer = null;
    this.isManualClose = false;

    // Event handlers
    this.handlers = {
      connected: [],
      disconnected: [],
      reconnecting: [],
      status_update: [],
      log: [],
      stats: [],
      connection: []
    };
  }

  /**
   * Connect to WebSocket
   */
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.isManualClose = false;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this.emit('disconnected');

        // Auto-reconnect unless manually closed
        if (!this.isManualClose) {
          this.reconnect();
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.reconnect();
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    this.isManualClose = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Reconnect with exponential backoff
   */
  reconnect() {
    if (this.isManualClose) {
      return;
    }

    // Calculate delay: 1s, 2s, 4s, 8s, 16s, 32s (max)
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
    this.emit('reconnecting', { attempt: this.reconnectAttempts, delay });

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Check if connected
   * @returns {boolean} True if connected
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Handle incoming message
   * @param {Object} message - Parsed message
   */
  handleMessage(message) {
    const { type } = message;

    switch (type) {
      case 'connection':
        this.emit('connection', message);
        break;

      case 'status_update':
        this.emit('status_update', message);
        break;

      case 'log':
        this.emit('log', message);
        break;

      case 'stats':
        this.emit('stats', message);
        break;

      default:
        console.warn('Unknown message type:', type, message);
    }
  }

  /**
   * Register event handler
   * @param {string} eventType - Event type
   * @param {Function} callback - Callback function
   */
  on(eventType, callback) {
    if (!this.handlers[eventType]) {
      console.warn(`Unknown event type: ${eventType}`);
      return;
    }

    this.handlers[eventType].push(callback);
  }

  /**
   * Unregister event handler
   * @param {string} eventType - Event type
   * @param {Function} callback - Callback function
   */
  off(eventType, callback) {
    if (!this.handlers[eventType]) {
      return;
    }

    const index = this.handlers[eventType].indexOf(callback);
    if (index > -1) {
      this.handlers[eventType].splice(index, 1);
    }
  }

  /**
   * Emit event to registered handlers
   * @param {string} eventType - Event type
   * @param {any} data - Event data
   */
  emit(eventType, data = null) {
    if (!this.handlers[eventType]) {
      return;
    }

    this.handlers[eventType].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in ${eventType} handler:`, error);
      }
    });
  }
}
