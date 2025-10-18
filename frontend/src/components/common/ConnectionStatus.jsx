import { useConnectionStore } from '../../stores/useConnectionStore';
import './ConnectionStatus.css';

/**
 * ConnectionStatus Component
 *
 * Displays WebSocket connection status with visual indicator
 *
 * States:
 * - Connected: Green dot "● Connected"
 * - Disconnected: Gray dot "○ Disconnected"
 * - Reconnecting: Orange dot with pulse "◐ Reconnecting..."
 */
export default function ConnectionStatus() {
  const status = useConnectionStore((state) => state.status);

  const statusConfig = {
    connected: {
      symbol: '●',
      text: 'Connected',
      className: 'connection-status--connected'
    },
    disconnected: {
      symbol: '○',
      text: 'Disconnected',
      className: 'connection-status--disconnected'
    },
    reconnecting: {
      symbol: '◐',
      text: 'Reconnecting...',
      className: 'connection-status--reconnecting'
    }
  };

  const config = statusConfig[status] || statusConfig.disconnected;

  return (
    <div
      className={`connection-status ${config.className}`}
      role="status"
      aria-live="polite"
      aria-label={`Connection status: ${config.text}`}
    >
      <span className="connection-status__indicator" aria-hidden="true">
        {config.symbol}
      </span>
      <span className="connection-status__text">{config.text}</span>
    </div>
  );
}
