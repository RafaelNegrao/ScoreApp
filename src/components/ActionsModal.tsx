import { useEffect, useState } from "react";
import './ActionsModal.css';

interface ActionItem {
  id: string;
  text: string;
  createdAt: string;
  done: boolean;
}

interface ActionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  supplierName?: string;
  actions: ActionItem[];
  onAddAction: (text: string) => void;
  onToggleDone: (id: string, done: boolean) => void;
  onDeleteAction: (id: string) => void;
  onEditAction?: (id: string, text: string) => void;
}

export const ActionsModal: React.FC<ActionsModalProps> = ({
  isOpen,
  onClose,
  supplierName,
  actions,
  onAddAction,
  onToggleDone,
  onDeleteAction,
  onEditAction,
}) => {
  const [text, setText] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      setText('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    if (!text.trim()) return;
    onAddAction(text.trim());
    setText('');
  };

  const startEdit = (id: string, currentText: string) => {
    setEditingId(id);
    setEditingText(currentText);
    setTimeout(() => {
      const el = document.getElementById(`modal-edit-${id}`) as HTMLTextAreaElement | null;
      if (el) {
        el.style.height = 'auto';
        el.style.height = `${el.scrollHeight}px`;
        el.focus();
      }
    }, 0);
  };

  const saveEdit = (id: string) => {
    if (!editingText.trim()) return;
    if (onEditAction) onEditAction(id, editingText.trim());
    setEditingId(null);
    setEditingText('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingText('');
  };

  return (
    <div className="actions-modal-overlay" onClick={onClose}>
      <div className="actions-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="actions-modal-header">
          <h3>
            Ações
            {supplierName && <><br />{supplierName}</>}
          </h3>
          <button className="actions-modal-close" onClick={onClose}>
            <i className="bi bi-x-lg"></i>
          </button>
        </div>

        <div className="actions-modal-body">
          <div className="actions-list">
            {actions.length === 0 ? (
              <div className="actions-empty">Nenhuma ação registrada</div>
            ) : (
              actions.map((action) => (
                <div key={action.id} className={`actions-item ${action.done ? 'done' : ''}`}>
                  <label className="actions-item-check">
                    <input
                      type="checkbox"
                      checked={action.done}
                      onChange={(e) => onToggleDone(action.id, e.target.checked)}
                    />
                  </label>

                  <div className="actions-item-text-wrapper">
                    {editingId === action.id ? (
                      <textarea
                          id={`modal-edit-${action.id}`}
                          className="actions-item-edit"
                          value={editingText}
                          onChange={(e) => { setEditingText(e.target.value); e.currentTarget.style.height = 'auto'; e.currentTarget.style.height = `${e.currentTarget.scrollHeight}px`; }}
                          rows={1}
                        />
                    ) : (
                      <span className="actions-item-text">{action.text}</span>
                    )}
                    <div className="actions-item-meta">
                      <span className="actions-item-date">{action.createdAt}</span>
                    </div>
                  </div>

                  <div className="actions-item-controls">
                    {editingId === action.id ? (
                      <>
                        <button className="actions-item-btn save" onClick={() => saveEdit(action.id)} title="Salvar edição"><i className="bi bi-check-lg"></i></button>
                        <button className="actions-item-btn cancel" onClick={cancelEdit} title="Cancelar"><i className="bi bi-x-lg"></i></button>
                      </>
                    ) : (
                      <>
                        <button className="actions-item-btn edit" onClick={() => startEdit(action.id, action.text)} title="Editar"><i className="bi bi-pencil"></i></button>
                        <button className="actions-item-btn delete" onClick={() => onDeleteAction(action.id)} title="Excluir ação"><i className="bi bi-trash"></i></button>
                      </>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="actions-input">
            <textarea
              className="actions-textarea"
              placeholder="Adicionar ação a ser tomada..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={4}
              autoFocus
            />
          </div>
        </div>

        <div className="actions-modal-footer">
          <button className="actions-modal-button cancel" onClick={onClose}>
            Fechar
          </button>
          <button className="actions-modal-button save" onClick={handleSave}>
            <i className="bi bi-plus-lg"></i> Adicionar
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActionsModal;
