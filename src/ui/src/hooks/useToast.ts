/**
 * Toast Hook - DocuSearch UI
 * Provider: Wave 3 (Polish & Refinement)
 *
 * Custom hook for managing toast notifications
 */

import { useState, useCallback } from 'react';
import type { ToastType, ToastAction } from '../components/Toast/Toast';
import type { ToastData } from '../components/Toast/ToastContainer';

/**
 * Options for toast notifications
 */
export interface ToastOptions {
  /** Duration in milliseconds (default: 5000) */
  duration?: number;
  /** Optional action button */
  action?: ToastAction;
}

/**
 * Toast management hook
 *
 * Provides methods to show and dismiss toast notifications
 *
 * @returns Toast state and control methods
 *
 * @example
 * const { toasts, showToast, dismissToast } = useToast();
 *
 * showToast('File uploaded successfully!', 'success');
 * showToast('Failed to process document', 'error');
 */
export function useToast() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  /**
   * Show a new toast notification
   */
  const showToast = useCallback(
    (message: string, type: ToastType = 'info', options?: ToastOptions) => {
      const id = `toast-${Date.now()}-${Math.random()}`;

      const newToast: ToastData = {
        id,
        message,
        type,
        duration: options?.duration ?? 5000,
        action: options?.action,
      };

      setToasts((prev) => [...prev, newToast]);
    },
    []
  );

  /**
   * Dismiss a specific toast by ID
   */
  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  /**
   * Dismiss all toasts
   */
  const dismissAll = useCallback(() => {
    setToasts([]);
  }, []);

  /**
   * Convenience methods for specific toast types
   */
  const success = useCallback(
    (message: string, options?: ToastOptions) => {
      showToast(message, 'success', options);
    },
    [showToast]
  );

  const error = useCallback(
    (message: string, options?: ToastOptions) => {
      showToast(message, 'error', options);
    },
    [showToast]
  );

  const warning = useCallback(
    (message: string, options?: ToastOptions) => {
      showToast(message, 'warning', options);
    },
    [showToast]
  );

  const info = useCallback(
    (message: string, options?: ToastOptions) => {
      showToast(message, 'info', options);
    },
    [showToast]
  );

  return {
    toasts,
    showToast,
    dismissToast,
    dismissAll,
    success,
    error,
    warning,
    info,
  };
}
