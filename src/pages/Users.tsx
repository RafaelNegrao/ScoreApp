import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import './Users.css';
import DeleteModal from '../utils/DeleteModal';
import { usePermissions } from '../contexts/PermissionsContext';
import { useToast } from '../hooks/useToast';
import { ToastContainer } from '../components/ToastContainer';

interface User {
  user_id: number;
  user_name: string;
  user_wwid: string;
  user_privilege: string;
  user_status: string;
  otif: number;
  nil: number;
  pickup: number;
  package: number;
}

const Users = () => {
  const { user: currentUser, permissions, isUser, isAdmin } = usePermissions();
  const { toasts, showToast, removeToast } = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    user: User | null;
    confirmationCode: string;
    userInput: string;
  }>({
    isOpen: false,
    user: null,
    confirmationCode: '',
    userInput: '',
  });
  const [formData, setFormData] = useState({
    userId: 0,
    name: '',
    wwid: '',
    privilege: 'User',
    status: 'Active',
    password: '',
    otif: false,
    nil: false,
    pickup: false,
    package: false,
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      console.log('🔍 Carregando usuários...');
      const result = await invoke<User[]>('get_all_users');
      console.log('✅ Usuários carregados:', result);
      console.log('🔐 Permissões atuais:', { 
        canEditAllUsers: permissions.canEditAllUsers, 
        canEditOnlySelf: permissions.canEditOnlySelf,
        currentUserId: currentUser?.user_id 
      });
      
      // Filtrar usuários baseado no privilégio
      let filteredUsers = result;
      
      // Super Admin (canEditAllUsers = true) vê TODOS os usuários
      // Admin e User (canEditOnlySelf = true) veem apenas eles mesmos
      if (!permissions.canEditAllUsers && permissions.canEditOnlySelf && currentUser) {
        filteredUsers = result.filter(user => user.user_id === currentUser.user_id);
        console.log('👤 Filtrando para mostrar apenas o usuário atual:', currentUser.user_id);
      } else if (permissions.canEditAllUsers) {
        console.log('👑 Super Admin - mostrando todos os usuários');
      }
      
      setUsers(filteredUsers);
    } catch (error) {
      console.error('❌ Erro ao carregar usuários:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      userId: 0,
      name: '',
      wwid: '',
      privilege: 'User',
      status: 'Active',
      password: '',
      otif: false,
      nil: false,
      pickup: false,
      package: false,
    });
    setEditingUser(null);
  };

  const generateConfirmationCode = (): string => {
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    let code = '';
    for (let i = 0; i < 5; i++) {
      code += letters.charAt(Math.floor(Math.random() * letters.length));
    }
    return code;
  };

  const openDeleteModal = (user: User) => {
    setDeleteModal({
      isOpen: true,
      user,
      confirmationCode: generateConfirmationCode(),
      userInput: '',
    });
  };

  const closeDeleteModal = () => {
    setDeleteModal({
      isOpen: false,
      user: null,
      confirmationCode: '',
      userInput: '',
    });
  };

  const handleEdit = async (user: User) => {
    setEditingUser(user);
    
    // Buscar a senha do usuário
    try {
      const password = await invoke<string>('get_user_password', { userId: user.user_id });
      setFormData({
        userId: user.user_id,
        name: user.user_name,
        wwid: user.user_wwid,
        privilege: user.user_privilege,
        status: user.user_status || 'Active',
        password: password,
        otif: user.otif === 1,
        nil: user.nil === 1,
        pickup: user.pickup === 1,
        package: user.package === 1,
      });
    } catch (error) {
      console.error('Erro ao buscar senha:', error);
      setFormData({
        userId: user.user_id,
        name: user.user_name,
        wwid: user.user_wwid,
        privilege: user.user_privilege,
        status: user.user_status || 'Active',
        password: '',
        otif: user.otif === 1,
        nil: user.nil === 1,
        pickup: user.pickup === 1,
        package: user.package === 1,
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Se o usuário atual for Admin, eles não podem alterar as permissões de score nesta tela.
      const otifVal = isAdmin ? (editingUser ? (editingUser.otif === 1 ? 1 : 0) : 0) : (formData.otif ? 1 : 0);
      const nilVal = isAdmin ? (editingUser ? (editingUser.nil === 1 ? 1 : 0) : 0) : (formData.nil ? 1 : 0);
      const pickupVal = isAdmin ? (editingUser ? (editingUser.pickup === 1 ? 1 : 0) : 0) : (formData.pickup ? 1 : 0);
      const packageVal = isAdmin ? (editingUser ? (editingUser.package === 1 ? 1 : 0) : 0) : (formData.package ? 1 : 0);

      if (editingUser) {
        // Atualizar usuário existente
        await invoke('update_user', {
          userId: formData.userId,
          name: formData.name,
          wwid: formData.wwid,
          privilege: formData.privilege,
          status: formData.status,
          password: formData.password || undefined,
          otif: otifVal,
          nil: nilVal,
          pickup: pickupVal,
          package: packageVal,
        });
        showToast('Usuário atualizado com sucesso!', 'success');
      } else {
        // Criar novo usuário
        await invoke('create_user', {
          name: formData.name,
          wwid: formData.wwid,
          privilege: formData.privilege,
          status: formData.status,
          password: formData.password,
          otif: otifVal,
          nil: nilVal,
          pickup: pickupVal,
          package: packageVal,
        });
        showToast('Usuário cadastrado com sucesso!', 'success');
      }

      resetForm();
      loadUsers();
    } catch (error) {
      console.error('Erro ao salvar usuário:', error);
      showToast('Erro ao salvar usuário. Tente novamente.', 'error');
    }
  };

  const handleDelete = async (user: User) => {
    openDeleteModal(user);
  };

  const confirmDelete = async () => {
    if (!deleteModal.user) return;

    if (deleteModal.userInput.toUpperCase() !== deleteModal.confirmationCode) {
      showToast('Código de confirmação incorreto!', 'error');
      return;
    }

    try {
      await invoke('delete_user', { userId: deleteModal.user.user_id });
      showToast('Usuário excluído com sucesso!', 'success');
      resetForm();
      loadUsers();
      closeDeleteModal();
    } catch (error) {
      console.error('Erro ao excluir usuário:', error);
      showToast('Erro ao excluir usuário. Tente novamente.', 'error');
    }
  };

  return (
    <div className="users-management">
      <div className="users-form-panel">
        <div className="user-form-header">
          <h4>{editingUser ? 'Editar usuário' : 'Novo usuário'}</h4>
          {/* Removido texto de edição */}
        </div>

        <form onSubmit={handleSubmit} className="user-form">
          <div className="form-field">
            <label htmlFor="userName">Nome completo</label>
            <input
              type="text"
              id="userName"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Ex: Sabrina Geane"
              maxLength={80}
              required
            />
          </div>

          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="userWwid">WWID</label>
              <input
                type="text"
                id="userWwid"
                value={formData.wwid}
                onChange={(e) => setFormData({ ...formData, wwid: e.target.value.toUpperCase() })}
                placeholder="Ex: AL890"
                maxLength={10}
                disabled={!permissions.canEditWWID}
                required
              />
            </div>
            <div className="form-field">
              <label htmlFor="userPrivilege">Privilégio</label>
              <select
                id="userPrivilege"
                value={formData.privilege}
                onChange={(e) => setFormData({ ...formData, privilege: e.target.value })}
                disabled={!permissions.canEditAllUsers}
                required
              >
                <option value="User">User</option>
                <option value="Admin">Admin</option>
                <option value="Super Admin">Super Admin</option>
              </select>
            </div>
          </div>

          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="userStatus">Status</label>
              <select
                id="userStatus"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                disabled={!permissions.canEditAllUsers}
                required
              >
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
                <option value="Pendent">Pendent</option>
              </select>
            </div>
            <div className="form-field">
              <label htmlFor="userPassword">Senha</label>
              <div className="password-input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="userPassword"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder={editingUser ? 'Senha atual' : 'Defina uma senha'}
                  maxLength={40}
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  title={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                >
                  <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                </button>
              </div>
            </div>
          </div>

          {!isUser && !isAdmin && (
            <div className="permissions-group">
              <span className="permissions-title">Permissões de módulos</span>
              <div className="permissions-grid">
                <label className="permission-toggle">
                  <input
                    type="checkbox"
                    checked={formData.otif}
                    onChange={(e) => setFormData({ ...formData, otif: e.target.checked })}
                  />
                  <span className="custom-checkbox">
                    <i className={`bi ${formData.otif ? 'bi-check-circle-fill' : 'bi-circle-fill'}`}></i>
                  </span>
                  <span className="permission-label">OTIF</span>
                </label>
                <label className="permission-toggle">
                  <input
                    type="checkbox"
                    checked={formData.nil}
                    onChange={(e) => setFormData({ ...formData, nil: e.target.checked })}
                  />
                  <span className="custom-checkbox">
                    <i className={`bi ${formData.nil ? 'bi-check-circle-fill' : 'bi-circle-fill'}`}></i>
                  </span>
                  <span className="permission-label">NIL</span>
                </label>
                <label className="permission-toggle">
                  <input
                    type="checkbox"
                    checked={formData.pickup}
                    onChange={(e) => setFormData({ ...formData, pickup: e.target.checked })}
                  />
                  <span className="custom-checkbox">
                    <i className={`bi ${formData.pickup ? 'bi-check-circle-fill' : 'bi-circle-fill'}`}></i>
                  </span>
                  <span className="permission-label">Pick Up</span>
                </label>
                <label className="permission-toggle">
                  <input
                    type="checkbox"
                    checked={formData.package}
                    onChange={(e) => setFormData({ ...formData, package: e.target.checked })}
                  />
                  <span className="custom-checkbox">
                    <i className={`bi ${formData.package ? 'bi-check-circle-fill' : 'bi-circle-fill'}`}></i>
                  </span>
                  <span className="permission-label">Package</span>
                </label>
              </div>
            </div>
          )}

          <div className="user-form-actions">
            <button type="button" className="user-btn user-btn-secondary" onClick={resetForm}>
              Cancelar
            </button>
            <button type="submit" className="user-btn user-btn-primary">
              {editingUser ? 'Atualizar usuário' : 'Salvar usuário'}
            </button>
          </div>
        </form>
      </div>

  <div className="users-list-panel" style={{flex: 1, minHeight: 0, overflowY: 'auto', maxHeight: '100vh', marginLeft: 0}}>
        {loading ? (
          <div className="users-list-loading">
            <i className="bi bi-arrow-repeat spin"></i>
            <p>Carregando usuários...</p>
          </div>
        ) : users.length === 0 ? (
          <div className="users-list-empty">
            <i className="bi bi-inbox"></i>
            <p>Nenhum usuário cadastrado</p>
            <small>Use o formulário ao lado para adicionar o primeiro usuário.</small>
          </div>
        ) : (
          <div className="users-list" style={{display: 'flex', flexDirection: 'column', gap: 16}}>
            {users.map((user) => (
              <div key={user.user_id} className="user-card">
                <div className="user-card-header">
                  <div className="user-card-avatar">
                    <i className="bi bi-person-circle"></i>
                  </div>
                  <div className="user-card-info">
                    <span className="user-card-name">{user.user_name}</span>
                    <span className="user-card-wwid">WWID: {user.user_wwid}</span>
                  </div>
                  <div className="user-card-badges">
                    <span className={`user-card-badge badge-${user.user_privilege.toLowerCase().replace(' ', '-')}`}>
                      {user.user_privilege}
                    </span>
                    <span className={`user-status-badge status-${user.user_status?.toLowerCase() || 'active'}`}>
                      {user.user_status || 'Active'}
                    </span>
                  </div>
                </div>
                <div className="user-card-body">
                  <div className="user-card-permissions">
                    {user.otif === 1 && <span className="permission-badge">OTIF</span>}
                    {user.nil === 1 && <span className="permission-badge">NIL</span>}
                    {user.pickup === 1 && <span className="permission-badge">Pick Up</span>}
                    {user.package === 1 && <span className="permission-badge">Package</span>}
                  </div>
                </div>
                <div className="user-card-footer">
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, width: '100%' }}>
                    <button className="user-card-action" title="Editar" onClick={() => handleEdit(user)}>
                      <i className="bi bi-pencil"></i>
                    </button>
                    {permissions.canDeleteUsers && (
                      <button className="user-card-action danger" title="Excluir" onClick={() => openDeleteModal(user)}>
                        <i className="bi bi-trash"></i>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteModal
        isOpen={deleteModal.isOpen}
        title={deleteModal.user ? `Excluir usuário: ${deleteModal.user.user_name}` : 'Confirmar exclusão'}
        description="Esta ação não pode ser desfeita."
        confirmationCode={deleteModal.confirmationCode}
        userInput={deleteModal.userInput}
        onInputChange={val => setDeleteModal(prev => ({ ...prev, userInput: val }))}
        onCancel={closeDeleteModal}
        onConfirm={confirmDelete}
        confirmLabel="Excluir usuário"
        cancelLabel="Cancelar"
        disabled={deleteModal.userInput.length !== 5}
      />

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
};

export default Users;
