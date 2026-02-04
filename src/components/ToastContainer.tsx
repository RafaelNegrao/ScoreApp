import { Toast } from './Toast';
import { ToastData } from '../hooks/useToast';
import './ToastContainer.css';

export interface ToastContainerProps {
  toasts: ToastData[];
  stackCount?: number;
  onRemove: (id: string) => void;
}

/**
 * Container para múltiplos toasts
 */
export function ToastContainer({ toasts, stackCount = 0, onRemove }: ToastContainerProps) {
  const activeToast = toasts[0];
  return (
    <div className="toast-container">
      {activeToast && (
        <div className="toast-stack">
          {stackCount > 1 && <div className="toast-stack-back" />}
          <div className="toast-stack-front">
            <Toast
              message={activeToast.message}
              type={activeToast.type}
              duration={activeToast.duration}
              onClose={() => onRemove(activeToast.id)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
