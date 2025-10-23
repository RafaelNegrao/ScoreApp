import React, { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { useToast } from '../hooks/useToast';
import './TopBar.css';

interface PendingUser {
  user_id: number;
  user_name: string;
  user_wwid: string;
}

const TopBar: React.FC = () => {
  const [userName, setUserName] = useState<string>('');
  const [userRole, setUserRole] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);
  const [showPendingModal, setShowPendingModal] = useState(false);
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    // Simula carregamento de dados do usuário
    setTimeout(() => {
      const storedUser = sessionStorage.getItem('user');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        setUserName(user.name || 'Usuário');
        setUserRole(user.privilege || 'Padrão');
        setIsSuperAdmin(user.privilege === 'Super Admin');
        
        // Se for Super Admin, carrega contagem de pendentes
        if (user.privilege === 'Super Admin') {
          loadPendingCount();
        }
      }
      setLoading(false);
    }, 800);
  }, []);

  const loadPendingCount = async () => {
    try {
      const count = await invoke<number>('count_pending_users');
      setPendingCount(count);
    } catch (error) {
      console.error('Erro ao carregar contagem de pendentes:', error);
    }
  };

  const loadPendingUsers = async () => {
    try {
      const users = await invoke<PendingUser[]>('get_pending_users');
      setPendingUsers(users);
    } catch (error) {
      console.error('Erro ao carregar usuários pendentes:', error);
    }
  };

  const handleShowPending = async () => {
    await loadPendingUsers();
    setShowPendingModal(true);
  };

  const handleApprove = async (userId: number) => {
    try {
      await invoke('update_user_status', { userId, status: 'Active' });
      showToast('Usuário aprovado com sucesso!', 'success');
      await loadPendingUsers();
      await loadPendingCount();
    } catch (error) {
      console.error('Erro ao aprovar usuário:', error);
      showToast('Erro ao aprovar usuário', 'error');
    }
  };

  const handleReject = async (userId: number) => {
    try {
      await invoke('update_user_status', { userId, status: 'Inactive' });
      showToast('Usuário rejeitado', 'warning');
      await loadPendingUsers();
      await loadPendingCount();
    } catch (error) {
      console.error('Erro ao rejeitar usuário:', error);
      showToast('Erro ao rejeitar usuário', 'error');
    }
  };

  return (
    <div className="top-bar">
      <div className="top-bar-left">
        <div className="user-info">
          <div className="user-avatar">
            <i className="bi bi-person-circle"></i>
          </div>
          <div className="user-details">
            <span className="user-name">
              {loading ? <span className="skeleton skeleton-text"></span> : userName}
            </span>
            <span className="user-role">
              {loading ? <span className="skeleton skeleton-text-small"></span> : userRole}
            </span>
          </div>
        </div>
      </div>
      <div className="top-bar-right">
        {isSuperAdmin && (
          <button 
            className="btn-pendencias" 
            onClick={handleShowPending}
            title="Ver usuários pendentes"
          >
            <i className="bi bi-bell-fill"></i>
            <span>Pendências</span>
            {pendingCount > 0 && (
              <span className="pending-badge">{pendingCount}</span>
            )}
          </button>
        )}
      </div>

      {/* Modal de usuários pendentes */}
      {showPendingModal && (
        <div className="pending-modal-overlay" onClick={() => setShowPendingModal(false)}>
          <div className="pending-modal" onClick={(e) => e.stopPropagation()}>
            <div className="pending-modal-header">
              <h3>Usuários Aguardando Aprovação</h3>
              <button className="modal-close" onClick={() => setShowPendingModal(false)}>
                <i className="bi bi-x-lg"></i>
              </button>
            </div>
            <div className="pending-modal-content">
              {pendingUsers.length === 0 ? (
                <div className="empty-pending">
                  <i className="bi bi-check-circle"></i>
                  <p>Nenhum usuário pendente</p>
                </div>
              ) : (
                pendingUsers.map((user) => (
                  <div key={user.user_id} className="pending-user-card">
                    <div className="pending-user-info">
                      <i className="bi bi-person-circle"></i>
                      <div>
                        <strong>{user.user_name}</strong>
                        <span>WWID: {user.user_wwid}</span>
                      </div>
                    </div>
                    <div className="pending-user-actions">
                      <button 
                        className="btn-approve"
                        onClick={() => handleApprove(user.user_id)}
                        title="Aprovar usuário"
                      >
                        <i className="bi bi-check-lg"></i>
                        Aprovar
                      </button>
                      <button 
                        className="btn-reject"
                        onClick={() => handleReject(user.user_id)}
                        title="Rejeitar usuário"
                      >
                        <i className="bi bi-x-lg"></i>
                        Rejeitar
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TopBar;
