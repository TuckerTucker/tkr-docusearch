/**
 * ToastContainer Component - DocuSearch UI
 * Provider: Wave 3 (Polish & Refinement)
 *
 * Container for managing and displaying multiple toast notifications
 */

import React from 'react';
import { Toast, type ToastProps } from './Toast';
import { Z_INDEX } from '../../lib/constants';

export interface ToastData {
  id: string;
  message: string;
  type: ToastProps['type'];
  duration?: number;
}

interface ToastContainerProps {
  toasts: ToastData[];
  onDismiss: (id: string) => void;
}

/**
 * Toast container component
 *
 * Displays toasts in a fixed position (top-right)
 * Manages z-index layering
 * Stacks multiple toasts vertically
 */
export function ToastContainer({
  toasts,
  onDismiss,
}: ToastContainerProps): React.ReactElement {
  return (
    <div
      className="fixed top-4 right-4 flex flex-col gap-2 pointer-events-none"
      style={{ zIndex: Z_INDEX.toast }}
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast
            id={toast.id}
            message={toast.message}
            type={toast.type}
            duration={toast.duration}
            onDismiss={onDismiss}
          />
        </div>
      ))}
    </div>
  );
}
