import { useState, useCallback, useRef } from 'react';

export interface ToastData {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

let toastIdCounter = 0;

/**
 * Hook customizado para gerenciar notificações toast
 */
export function useToast() {
  const [toasts, setToasts] = useState<ToastData[]>([]);
  const [stackCount, setStackCount] = useState(0);
  const counterRef = useRef(0);
  const activeIdRef = useRef<string>('');

  const showToast = useCallback((
    message: string,
    type: 'success' | 'error' | 'warning' | 'info' = 'info',
    duration = 3000
  ) => {
    setToasts((prev) => {
      const hasActive = prev.length > 0;
      if (!activeIdRef.current) {
        counterRef.current += 1;
        activeIdRef.current = `${Date.now()}-${counterRef.current}`;
      }

      if (!hasActive) {
        setStackCount(1);
      } else {
        setStackCount((count) => Math.min(count + 1, 2));
      }

      const updatedToast: ToastData = {
        id: activeIdRef.current,
        message,
        type,
        duration,
      };

      return [updatedToast];
    });
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
    if (activeIdRef.current === id) {
      activeIdRef.current = '';
      setStackCount(0);
    }
  }, []);

  return {
    toasts,
    stackCount,
    showToast,
    removeToast,
  };
}
