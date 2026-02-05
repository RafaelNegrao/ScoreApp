import { useEffect, useState } from "react";
import "../../pages/Page.css";
import "./ActionsPanel.css";

interface ActionItem {
  id: string;
  text: string;
  createdAt: string;
  done: boolean;
}

interface ActionsPanelProps {
  supplierId: string | null;
}

function ActionsPanel({ supplierId }: ActionsPanelProps) {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState<string>('');
  const [newText, setNewText] = useState<string>('');

  const loadActions = (id: string) => {
    const stored = localStorage.getItem(`riskActions:${id}`);
    if (!stored) return [] as ActionItem[];
    try {
      const parsed = JSON.parse(stored) as ActionItem[];
      return Array.isArray(parsed)
        ? parsed.map((action) => ({
            ...action,
            done: action.done ?? false,
          }))
        : [];
    } catch {
      return [] as ActionItem[];
    }
  };

  useEffect(() => {
    if (!supplierId) {
      setActions([]);
      setNewText('');
      return;
    }
    setActions(loadActions(supplierId));
  }, [supplierId]);

  const saveActions = (id: string, updated: ActionItem[]) => {
    localStorage.setItem(`riskActions:${id}`, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent('riskActionsChanged', { detail: id }));
    setActions(updated);
  };

  const toggleDone = (actionId: string) => {
    if (!supplierId) return;
    const updated = actions.map((a) => a.id === actionId ? { ...a, done: !a.done } : a);
    saveActions(supplierId, updated);
  };

  const handleDelete = (actionId: string) => {
    if (!supplierId) return;
    const updated = actions.filter((a) => a.id !== actionId);
    saveActions(supplierId, updated);
  };

  const startEdit = (actionId: string, currentText: string) => {
    setEditingId(actionId);
    setEditingText(currentText);
    setTimeout(() => {
      const el = document.getElementById(`panel-edit-${actionId}`) as HTMLTextAreaElement | null;
      if (el) {
        el.style.height = 'auto';
        el.style.height = `${el.scrollHeight}px`;
        el.focus();
      }
    }, 0);
  };

  const saveEdit = (actionId: string) => {
    if (!supplierId) return;
    const updated = actions.map((a) => a.id === actionId ? { ...a, text: editingText } : a);
    saveActions(supplierId, updated);
    setEditingId(null);
    setEditingText('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingText('');
  };

  useEffect(() => {
    const handleActionsChange = (event: Event) => {
      if (!supplierId) return;
      const detail = (event as CustomEvent<string>).detail;
      if (detail && detail !== supplierId) return;
      setActions(loadActions(supplierId));
    };

    window.addEventListener('riskActionsChanged', handleActionsChange as EventListener);
    return () => window.removeEventListener('riskActionsChanged', handleActionsChange as EventListener);
  }, [supplierId]);

  if (!supplierId) {
    return (
      <div className="empty-state">
        <i className="bi bi-list-check" style={{ fontSize: '3rem', color: 'var(--text-muted)', opacity: 0.5 }}></i>
        <p style={{ fontSize: '0.95rem', fontWeight: 400, color: 'var(--text-muted)', opacity: 0.85 }}>Selecione um fornecedor para visualizar as ações</p>
      </div>
    );
  }

  return (
    <div className="actions-panel">
      {actions.length === 0 ? (
        <div className="empty-state">
          <i className="bi bi-list-check" style={{ fontSize: '3rem', color: 'var(--text-muted)', opacity: 0.5 }}></i>
          <p style={{ fontSize: '0.95rem', fontWeight: 400, color: 'var(--text-muted)', opacity: 0.85 }}>Nenhuma ação registrada</p>
        </div>
      ) : (
        <div className="actions-panel-list">
          {actions.map((action) => (
            <div key={action.id} className={`actions-panel-item ${action.done ? 'done' : ''}`}>
              <div className="actions-panel-row">
                <label className="actions-panel-check">
                  <input
                    type="checkbox"
                    checked={action.done}
                    onChange={() => toggleDone(action.id)}
                  />
                </label>

                <div className="actions-panel-content">
                  {editingId === action.id ? (
                    <textarea
                      id={`panel-edit-${action.id}`}
                      className="actions-panel-edit"
                      value={editingText}
                      onChange={(e) => { setEditingText(e.target.value); e.currentTarget.style.height = 'auto'; e.currentTarget.style.height = `${e.currentTarget.scrollHeight}px`; }}
                      rows={1}
                    />
                  ) : (
                    <div className="actions-panel-text">{action.text}</div>
                  )}
                  <div className="actions-panel-date">{action.createdAt}</div>
                </div>

                <div className="actions-panel-buttons">
                  {editingId === action.id ? (
                    <>
                      <button className="actions-btn save" onClick={() => saveEdit(action.id)} title="Salvar edição"><i className="bi bi-check-lg"></i></button>
                      <button className="actions-btn cancel" onClick={cancelEdit} title="Cancelar"><i className="bi bi-x-lg"></i></button>
                    </>
                  ) : (
                    <>
                      <button className="actions-btn edit" onClick={() => startEdit(action.id, action.text)} title="Editar"><i className="bi bi-pencil"></i></button>
                      <button className="actions-btn delete" onClick={() => handleDelete(action.id)} title="Excluir"><i className="bi bi-trash"></i></button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {/* Add new action area */}
      <div className="actions-panel-add">
        <textarea
          className="actions-panel-newtext"
          placeholder="Adicionar nova ação..."
          value={newText}
          onChange={(e) => { setNewText(e.target.value); e.currentTarget.style.height = 'auto'; e.currentTarget.style.height = `${e.currentTarget.scrollHeight}px`; }}
          rows={1}
        />
        <div className="actions-panel-add-buttons">
          <button
            className="actions-panel-add-btn"
            onClick={() => {
              const text = (newText || '').trim();
              if (!text || !supplierId) return;
              const newAction: ActionItem = { id: `${Date.now()}`, text, createdAt: new Date().toLocaleString('pt-BR'), done: false };
              const updated = [newAction, ...actions];
              saveActions(supplierId, updated);
              setNewText('');
              const ta = document.querySelector('.actions-panel-newtext') as HTMLTextAreaElement | null;
              if (ta) { ta.value = ''; ta.style.height = 'auto'; }
            }}
          >
            <i className="bi bi-plus-lg"></i> Adicionar
          </button>
        </div>
      </div>
    </div>
  );
}

export default ActionsPanel;
