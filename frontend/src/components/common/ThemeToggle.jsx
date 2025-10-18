import { useThemeStore } from '../../stores/useThemeStore';
import './ThemeToggle.css';

/**
 * ThemeToggle Component
 *
 * Toggle between light and dark themes with icon indication
 *
 * Icons:
 * - Light theme: ☀ (sun)
 * - Dark theme: ☾ (moon)
 *
 * Behavior:
 * - Click to toggle between light/dark
 * - If theme is 'system', first click sets to opposite of current system theme
 * - Subsequent clicks toggle between light/dark
 */
export default function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);
  const getEffectiveTheme = useThemeStore((state) => state.getEffectiveTheme);

  const effectiveTheme = getEffectiveTheme();
  const isDark = effectiveTheme === 'dark';

  const handleToggle = () => {
    const newTheme = isDark ? 'light' : 'dark';
    setTheme(newTheme);
  };

  return (
    <button
      type="button"
      className={`theme-toggle ${isDark ? 'theme-toggle--dark' : 'theme-toggle--light'}`}
      onClick={handleToggle}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
      title={`Switch to ${isDark ? 'light' : 'dark'} theme`}
    >
      <span className="theme-toggle__icon" aria-hidden="true">
        {isDark ? '☾' : '☀'}
      </span>
    </button>
  );
}
