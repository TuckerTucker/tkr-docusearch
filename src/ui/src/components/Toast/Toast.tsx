/**
 * Toast Component - DocuSearch UI
 * Provider: Wave 3 (Polish & Refinement)
 *
 * Displays temporary notification messages for user feedback
 */

import React, { useEffect } from 'react';
import { cn } from '../../lib/utils';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  /** Unique toast ID */
  id: string;
  /** Toast message */
  message: string;
  /** Toast type/severity */
  type: ToastType;
  /** Duration in milliseconds (0 = never auto-dismiss) */
  duration?: number;
  /** Callback when toast is dismissed */
  onDismiss: (id: string) => void;
}

/**
 * Toast icons
 */
const ToastIcons = {
  success: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clipRule="evenodd"
      />
    </svg>
  ),
  error: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
        clipRule="evenodd"
      />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path
        fillRule="evenodd"
        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
        clipRule="evenodd"
      />
    </svg>
  ),
  info: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path
        fillRule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
        clipRule="evenodd"
      />
    </svg>
  ),
};

/**
 * Toast notification component
 *
 * Features:
 * - Auto-dismiss after duration
 * - Manual dismiss button
 * - Animated enter/exit
 * - Type-based styling
 * - Accessible with ARIA
 */
export function Toast({
  id,
  message,
  type,
  duration = 5000,
  onDismiss,
}: ToastProps): React.ReactElement {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onDismiss(id);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration, onDismiss]);

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg shadow-lg',
        'border backdrop-blur-sm',
        'animate-in slide-in-from-right duration-300',
        'max-w-md w-full',
        // Type-based styling
        type === 'success' &&
          'bg-green-50/95 border-green-200 text-green-800',
        type === 'error' &&
          'bg-red-50/95 border-red-200 text-red-800',
        type === 'warning' &&
          'bg-amber-50/95 border-amber-200 text-amber-800',
        type === 'info' &&
          'bg-blue-50/95 border-blue-200 text-blue-800'
      )}
      role="alert"
      aria-live="polite"
    >
      {/* Icon */}
      <div className="flex-shrink-0">{ToastIcons[type]}</div>

      {/* Message */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{message}</p>
      </div>

      {/* Dismiss button */}
      <button
        onClick={() => onDismiss(id)}
        className={cn(
          'flex-shrink-0 p-0.5 rounded transition-colors',
          'hover:bg-black/10 focus:outline-none focus:ring-2',
          type === 'success' && 'focus:ring-green-500',
          type === 'error' && 'focus:ring-red-500',
          type === 'warning' && 'focus:ring-amber-500',
          type === 'info' && 'focus:ring-blue-500'
        )}
        aria-label="Dismiss notification"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}
