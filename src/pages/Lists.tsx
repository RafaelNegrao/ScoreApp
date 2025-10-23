import { useState, useEffect } from "react";
import { invoke } from '@tauri-apps/api/tauri';
import 'bootstrap-icons/font/bootstrap-icons.css';
import "./Lists.css";

type ListType = 'sqie' | 'continuity' | 'planner' | 'sourcing' | 'bu' | 'category';

interface ListItemThreeFields {
  name: string;
  email: string;
  alias: string;
}

interface ListItemSingleField {
  name: string;
}

/**
 * Componente genérico para listas com 3 campos (nome, email, alias)
 */
function ThreeFieldList({ type, title }: { type: string; title: string }) {
  const [items, setItems] = useState<ListItemThreeFields[]>([]);
  const [formData, setFormData] = useState({ name: '', email: '', alias: '' });
  const [editingName, setEditingName] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Carregar items do banco de dados
  useEffect(() => {
    loadItems();
  }, [type]);

  const loadItems = async () => {
    try {
      setLoading(true);
      const result = await invoke<ListItemThreeFields[]>(`get_${type}_list`);
      setItems(result);
    } catch (error) {
      console.error('Erro ao carregar itens:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingName) {
        // Editar item existente
        await invoke(`update_${type}_item`, { 
          oldName: editingName, 
          item: formData 
        });
        setEditingName(null);
      } else {
        // Adicionar novo item
        await invoke(`add_${type}_item`, { item: formData });
      }
      
      setFormData({ name: '', email: '', alias: '' });
      await loadItems();
    } catch (error) {
      console.error('Erro ao salvar item:', error);
      alert(`Erro ao salvar: ${error}`);
    }
  };

  const handleEdit = (item: ListItemThreeFields) => {
    setFormData({
      name: item.name,
      email: item.email,
      alias: item.alias
    });
    setEditingName(item.name);
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Deseja realmente deletar "${name}"?`)) return;
    
    try {
      await invoke(`delete_${type}_item`, { name });
      await loadItems();
    } catch (error) {
      console.error('Erro ao deletar item:', error);
      alert(`Erro ao deletar: ${error}`);
    }
  };

  const handleCancel = () => {
    setFormData({ name: '', email: '', alias: '' });
    setEditingName(null);
  };

  return (
    <div className="lists-management">
      {/* Formulário */}
      <div className="lists-form-panel">
        <div className="list-form-header">
          <h4>{editingName ? 'Editar Item' : 'Novo Item'}</h4>
          <span>Preencha os campos abaixo</span>
        </div>

        <form className="list-form" onSubmit={handleSubmit}>
          <div className="form-field">
            <label>Nome</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Digite o nome"
              required
            />
          </div>

          <div className="form-field">
            <label>Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="Digite o email"
              required
            />
          </div>

          <div className="form-field">
            <label>Alias</label>
            <input
              type="text"
              value={formData.alias}
              onChange={(e) => setFormData({ ...formData, alias: e.target.value })}
              placeholder="Digite o alias"
              required
            />
          </div>

          <div className="form-actions">
            <button type="submit" className="list-btn-primary">
              <i className={`bi ${editingName ? 'bi-check-lg' : 'bi-plus-lg'}`}></i>
              {editingName ? 'Atualizar' : 'Adicionar'}
            </button>
            {editingName && (
              <button type="button" className="list-btn-secondary" onClick={handleCancel}>
                <i className="bi bi-x-lg"></i>
                Cancelar
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Lista de itens */}
      <div className="lists-items-panel">
        {loading ? (
          <div className="lists-empty">
            <i className="bi bi-arrow-repeat spin"></i>
            <p>Carregando...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="lists-empty">
            <i className="bi bi-inbox"></i>
            <p>Nenhum item cadastrado</p>
            <small>Use o formulário ao lado para adicionar itens.</small>
          </div>
        ) : (
          <div className="lists-items">
            {items.map((item) => (
              <div key={item.name} className="list-item-card">
                <div className="list-item-content">
                  <div className="list-item-header">
                    <h5>{item.name}</h5>
                  </div>
                  <div className="list-item-details">
                    <span><i className="bi bi-envelope"></i> {item.email}</span>
                    <span><i className="bi bi-at"></i> {item.alias}</span>
                  </div>
                </div>
                <div className="list-item-actions">
                  <button className="list-action-btn edit" onClick={() => handleEdit(item)}>
                    <i className="bi bi-pencil"></i>
                  </button>
                  <button className="list-action-btn delete" onClick={() => handleDelete(item.name)}>
                    <i className="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Componente para listas simples (apenas 1 campo)
 */
function SingleFieldList({ type, title, fieldLabel }: { type: string; title: string; fieldLabel: string }) {
  const [items, setItems] = useState<ListItemSingleField[]>([]);
  const [formData, setFormData] = useState({ name: '' });
  const [editingName, setEditingName] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Carregar items do banco de dados
  useEffect(() => {
    loadItems();
  }, [type]);

  const loadItems = async () => {
    try {
      setLoading(true);
      const result = await invoke<ListItemSingleField[]>(`get_${type}_list`);
      setItems(result);
    } catch (error) {
      console.error('Erro ao carregar itens:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingName) {
        // Editar item existente
        await invoke(`update_${type}_item`, { 
          oldName: editingName, 
          newName: formData.name 
        });
        setEditingName(null);
      } else {
        // Adicionar novo item
        await invoke(`add_${type}_item`, { name: formData.name });
      }
      
      setFormData({ name: '' });
      await loadItems();
    } catch (error) {
      console.error('Erro ao salvar item:', error);
      alert(`Erro ao salvar: ${error}`);
    }
  };

  const handleEdit = (item: ListItemSingleField) => {
    setFormData({ name: item.name });
    setEditingName(item.name);
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Deseja realmente deletar "${name}"?`)) return;
    
    try {
      await invoke(`delete_${type}_item`, { name });
      await loadItems();
    } catch (error) {
      console.error('Erro ao deletar item:', error);
      alert(`Erro ao deletar: ${error}`);
    }
  };

  const handleCancel = () => {
    setFormData({ name: '' });
    setEditingName(null);
  };

  return (
    <div className="lists-management single-field">
      {/* Formulário */}
      <div className="lists-form-panel">
        <div className="list-form-header">
          <h4>{editingName ? 'Editar' : 'Novo'} {fieldLabel}</h4>
          <span>Preencha o campo abaixo</span>
        </div>

        <form className="list-form" onSubmit={handleSubmit}>
          <div className="form-field">
            <label>{fieldLabel}</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ name: e.target.value })}
              placeholder={`Digite o ${fieldLabel.toLowerCase()}`}
              required
            />
          </div>

          <div className="form-actions">
            <button type="submit" className="list-btn-primary">
              <i className={`bi ${editingName ? 'bi-check-lg' : 'bi-plus-lg'}`}></i>
              {editingName ? 'Atualizar' : 'Adicionar'}
            </button>
            {editingName && (
              <button type="button" className="list-btn-secondary" onClick={handleCancel}>
                <i className="bi bi-x-lg"></i>
                Cancelar
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Lista de itens */}
      <div className="lists-items-panel">
        {loading ? (
          <div className="lists-empty">
            <i className="bi bi-arrow-repeat spin"></i>
            <p>Carregando...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="lists-empty">
            <i className="bi bi-inbox"></i>
            <p>Nenhum {fieldLabel.toLowerCase()} cadastrado</p>
            <small>Use o formulário ao lado para adicionar.</small>
          </div>
        ) : (
          <div className="lists-items">
            {items.map((item) => (
              <div key={item.name} className="list-item-card single">
                <div className="list-item-content">
                  <h5>{item.name}</h5>
                </div>
                <div className="list-item-actions">
                  <button className="list-action-btn edit" onClick={() => handleEdit(item)}>
                    <i className="bi bi-pencil"></i>
                  </button>
                  <button className="list-action-btn delete" onClick={() => handleDelete(item.name)}>
                    <i className="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Componente principal de Lists com subabas
 */
export default function Lists() {
  const [activeSubTab, setActiveSubTab] = useState<ListType>('sqie');

  return (
    <div className="lists-container">
      {/* Subabas */}
      <div className="lists-subtabs">
        <button 
          className={`subtab-btn ${activeSubTab === 'sqie' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('sqie')}
        >
          <i className="bi bi-file-text"></i>
          <span>SQIE</span>
        </button>
        <button 
          className={`subtab-btn ${activeSubTab === 'continuity' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('continuity')}
        >
          <i className="bi bi-arrow-repeat"></i>
          <span>Continuity</span>
        </button>
        <button 
          className={`subtab-btn ${activeSubTab === 'planner' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('planner')}
        >
          <i className="bi bi-person"></i>
          <span>Planner</span>
        </button>
        <button 
          className={`subtab-btn ${activeSubTab === 'sourcing' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('sourcing')}
        >
          <i className="bi bi-globe"></i>
          <span>Sourcing</span>
        </button>
        <button 
          className={`subtab-btn ${activeSubTab === 'bu' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('bu')}
        >
          <i className="bi bi-building"></i>
          <span>Business Unit</span>
        </button>
        <button 
          className={`subtab-btn ${activeSubTab === 'category' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('category')}
        >
          <i className="bi bi-diagram-3"></i>
          <span>Category</span>
        </button>
      </div>

      {/* Conteúdo das subabas */}
      <div className="lists-content">
        {activeSubTab === 'sqie' && <ThreeFieldList type="sqie" title="SQIE" />}
        {activeSubTab === 'continuity' && <ThreeFieldList type="continuity" title="Continuity" />}
        {activeSubTab === 'planner' && <ThreeFieldList type="planner" title="Planner" />}
        {activeSubTab === 'sourcing' && <ThreeFieldList type="sourcing" title="Sourcing" />}
        {activeSubTab === 'bu' && <SingleFieldList type="bu" title="Business Unit" fieldLabel="Business Unit" />}
        {activeSubTab === 'category' && <SingleFieldList type="category" title="Category" fieldLabel="Category" />}
      </div>
    </div>
  );
}