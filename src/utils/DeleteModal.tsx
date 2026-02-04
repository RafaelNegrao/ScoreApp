import React from 'react';
import './DeleteModal.css';

interface DeleteModalProps {
  isOpen: boolean;
  title?: string;
  description?: string;
  confirmationCode: string;
  userInput: string;
  onInputChange: (value: string) => void;
  onCancel: () => void;
  onConfirm: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  disabled?: boolean;
}

const DeleteModal: React.FC<DeleteModalProps> = ({
  isOpen,
  title = 'Confirmar exclusão',
  description = 'Esta ação não pode ser desfeita.',
  confirmationCode,
  userInput,
  onInputChange,
  onCancel,
  onConfirm,
  confirmLabel = 'Excluir',
  cancelLabel = 'Cancelar',
  disabled = false,
}) => {
  if (!isOpen) return null;
  return (
    <div className="delete-modal-overlay">
      <div className="delete-modal">
        <div className="delete-modal-header">
          <h3>{title}</h3>
          <button className="delete-modal-close" onClick={onCancel}>
            <i className="bi bi-x"></i>
          </button>
        </div>
        <div className="delete-modal-body">
          <div className="delete-warning">
            <i className="bi bi-exclamation-triangle"></i>
            <p>{description}</p>
          </div>
          <div className="confirmation-code-section">
            <div className="confirmation-label">Digite o código abaixo para confirmar:</div>
            <div className="confirmation-code-view">{confirmationCode.split('').join(' ')}</div>
            <input
              type="text"
              id="confirmation-code"
              value={userInput}
              onChange={e => onInputChange(e.target.value)}
              placeholder={`Digite as ${confirmationCode.length} letras`}
              maxLength={confirmationCode.length}
              className="confirmation-input themed-bg"
              autoComplete="off"
            />
          </div>
        </div>
        <div className="delete-modal-footer">
          <button className="delete-modal-btn cancel" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button
            className="delete-modal-btn confirm"
            onClick={onConfirm}
            disabled={disabled}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;
