import ThemeToggle from '../common/ThemeToggle';
import StyleSelector from '../common/StyleSelector';
import ConnectionStatus from '../common/ConnectionStatus';
import './Footer.css';

/**
 * Footer Component
 *
 * Application footer with theme controls and connection status
 *
 * @param {Object} props
 * @param {boolean} props.showConnectionStatus - Whether to show connection status (default: true)
 */
export default function Footer({ showConnectionStatus = true }) {
  return (
    <footer className="footer" role="contentinfo">
      <div className="footer__container">
        <div className="footer__actions">
          <ThemeToggle />
          <StyleSelector />
        </div>

        {showConnectionStatus && (
          <div className="footer__status">
            <ConnectionStatus />
          </div>
        )}
      </div>
    </footer>
  );
}
