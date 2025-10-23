import { appWindow } from '@tauri-apps/api/window';
import { useEffect, useState, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import { useToast } from '../hooks/useToast';
import { userStatusManager } from '../utils/userStatus';
import './TitleBar.css';

interface TitleBarProps {
  showUserInfo?: boolean;
}

interface Notification {
  id: number;
  title: string;
  message: string;
  time: string;
  read: boolean;
  type: 'info' | 'warning' | 'pending_user' | 'pending_score';
  userId?: number;
  userName?: string;
  userWwid?: string;
  // Para pending_score
  recordId?: number;             // ID do registro na tabela
  supplierId?: string;
  supplierName?: string;
  month?: string;
  year?: string;
  pendingFields?: string[];      // Campos que o usuário pode preencher
}

interface PendingUser {
  user_id: number;
  user_name: string;
  user_wwid: string;
}

const TitleBar = ({ showUserInfo = true }: TitleBarProps) => {
  const [userName, setUserName] = useState<string>('');
  const [userRole, setUserRole] = useState<string>('');
  const [userId, setUserId] = useState<number>(0);
  const { showToast } = useToast();
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [bellAnimate, setBellAnimate] = useState(false);
  const bellTimeout = useRef<NodeJS.Timeout | null>(null);
  const pollInterval = useRef<NodeJS.Timeout | null>(null);
  const previousCountRef = useRef<number>(0);
  const [isClosing, setIsClosing] = useState(false);
  
  // Estados para gerenciar privilégios e permissões de usuários pendentes
  const [userPrivileges, setUserPrivileges] = useState<{[key: number]: string}>({});
  const [userPermissions, setUserPermissions] = useState<{[key: number]: {otif: boolean, nil: boolean, pickup: boolean, package: boolean}}>({});
  
  const [scoreToEdit, setScoreToEdit] = useState<{
    supplierId: string;
    supplierName: string;
    month: string;
    year: string;
    scoreType: string;
    scoreValue: string;
  } | null>(null);

  // Monitor de evento para animação do sino
  useEffect(() => {
    const unlistenPromise = listen('notification-received', () => {
      console.log('🔔 Evento notification-received recebido');
      triggerBellAnimation();
      // Recarrega notificações quando recebe evento
      if (isSuperAdmin) {
        loadPendingUsersNotifications();
      } else if (userId > 0) {
        loadPendingScoresNotificationsWithId(userId);
      }
    });
    return () => {
      unlistenPromise.then(unlisten => unlisten());
      if (bellTimeout.current) clearTimeout(bellTimeout.current);
    };
  }, [isSuperAdmin, userId]);

  // Função para disparar animação do sino
  const triggerBellAnimation = () => {
    setBellAnimate(true);
    if (bellTimeout.current) clearTimeout(bellTimeout.current);
    bellTimeout.current = setTimeout(() => setBellAnimate(false), 1200);
  };

  // Polling periódico para verificar novas notificações
  useEffect(() => {
    // TODOS os usuários fazem polling de scores pendentes
    if (userId > 0) {
      // Carrega imediatamente
      loadPendingScoresNotificationsWithId(userId);

      // Polling a cada 30 segundos
      pollInterval.current = setInterval(() => {
        loadPendingScoresNotificationsWithId(userId);
      }, 30000);
    }
    
    // Super Admin TAMBÉM faz polling de usuários pendentes
    if (isSuperAdmin) {
      loadPendingUsersNotifications();
      
      const superAdminInterval = setInterval(() => {
        checkForNewNotifications();
      }, 10000);
      
      return () => {
        if (pollInterval.current) clearInterval(pollInterval.current);
        clearInterval(superAdminInterval);
      };
    }

    return () => {
      if (pollInterval.current) {
        clearInterval(pollInterval.current);
      }
    };
  }, [isSuperAdmin, userId]);

  // Verifica se há novas notificações
  const checkForNewNotifications = async () => {
    try {
      const pendingUsers = await invoke<PendingUser[]>('get_pending_users');
      const currentCount = pendingUsers.length;

      // Se a contagem aumentou, há nova notificação
      if (currentCount > previousCountRef.current && previousCountRef.current > 0) {
        console.log('🔔 Nova notificação detectada!');
        triggerBellAnimation();
      }

      // Sempre atualiza as notificações de usuários pendentes
      const pendingNotifications: Notification[] = pendingUsers.map((user) => ({
        id: user.user_id,
        title: 'Novo usuário aguardando aprovação',
        message: `${user.user_name} (WWID: ${user.user_wwid}) solicitou acesso ao sistema`,
        time: 'Pendente',
        read: false,
        type: 'pending_user',
        userId: user.user_id,
        userName: user.user_name,
        userWwid: user.user_wwid,
      }));
      
      // Combina com notificações de scores existentes
      setNotifications(prev => {
        const scoreNotifs = prev.filter(n => n.type === 'pending_score');
        return [...pendingNotifications, ...scoreNotifs];
      });

      previousCountRef.current = currentCount;
    } catch (error) {
      console.error('Erro ao verificar novas notificações:', error);
    }
  };

  useEffect(() => {
    console.log('🔄 useEffect showUserInfo disparado. showUserInfo:', showUserInfo);
    if (showUserInfo) {
      const storedUser = sessionStorage.getItem('user');
      console.log('📦 sessionStorage user:', storedUser);
      if (storedUser) {
        const user = JSON.parse(storedUser);
        console.log('👤 Usuário carregado:', user);
        setUserName(user.user_name || 'Usuário');
        setUserRole(user.user_privilege || 'Padrão');
        const uid = user.user_id || 0;
        setUserId(uid);
        setIsSuperAdmin(user.user_privilege === 'Super Admin');
        
        console.log('🔑 User ID definido:', uid);
        console.log('👑 É Super Admin?', user.user_privilege === 'Super Admin');
        
        // TODOS carregam scores pendentes
        if (uid > 0) {
          console.log('⭐ CARREGANDO NOTIFICAÇÕES DE SCORES...');
          loadPendingScoresNotificationsWithId(uid);
        }
        
        // Super Admin TAMBÉM carrega notificações de usuários pendentes
        if (user.user_privilege === 'Super Admin') {
          console.log('📋 SUPER ADMIN - Carregando notificações de usuários pendentes...');
          loadPendingUsersNotifications();
        }
      } else {
        console.warn('⚠️ Nenhum usuário encontrado no sessionStorage');
      }
    }
  }, [showUserInfo]);

  const loadPendingScoresNotificationsWithId = async (userIdParam: number) => {
    console.log('🚨🚨🚨 FUNÇÃO CHAMADA! userId:', userIdParam);
    try {
      console.log('🔍 loadPendingScoresNotifications chamada - userId:', userIdParam);
      
      if (userIdParam === 0) {
        console.log('⚠️ userId é 0, aguardando inicialização...');
        return;
      }
      
      console.log('📡 Chamando get_pending_scores com userId:', userIdParam);
      const pendingScores = await invoke<any[]>('get_pending_scores', { userId: userIdParam });
      
      console.log('✅ Scores pendentes recebidos:', pendingScores);
      console.log('📊 Total de scores pendentes:', pendingScores.length);
      
      if (pendingScores.length === 0) {
        console.log('ℹ️ Nenhum score pendente para este usuário');
        // Remove apenas as notificações de scores, mantém as de usuários
        setNotifications(prev => prev.filter(n => n.type !== 'pending_score'));
        return;
      }

      const scoreNotifications: Notification[] = pendingScores.map((score, index) => {
        const userFields = (score.pending_fields || []).join(', ');
        console.log(`  - ${score.supplier_name} (${score.month}/${score.year}): ${userFields}`);

        return {
          id: Date.now() + index,
          title: 'Avaliação Pendente',
          message: `${score.supplier_name} - ${score.month}/${score.year}`,
          time: 'Pendente',
          read: false,
          type: 'pending_score',
          recordId: score.record_id,  // ADICIONEI O RECORD_ID
          supplierId: score.supplier_id,
          supplierName: score.supplier_name,
          month: score.month,
          year: score.year,
          pendingFields: score.pending_fields,
        };
      });

      console.log('📬 Setando notificações:', scoreNotifications.length);
      
      // Se for Super Admin, combina com notificações de usuários pendentes
      setNotifications(prev => {
        const userNotifs = prev.filter(n => n.type === 'pending_user');
        if (userNotifs.length > 0) {
          console.log('🔗 Combinando com', userNotifs.length, 'notificações de usuários');
          return [...userNotifs, ...scoreNotifications];
        }
        return scoreNotifications;
      });

      // Anima sino se houver novas notificações
      if (scoreNotifications.length > 0) {
        console.log('🔔 Animando sino - há notificações pendentes');
        triggerBellAnimation();
      }
    } catch (error) {
      console.error('❌ Erro ao carregar notificações de scores pendentes:', error);
    }
  };

  const loadPendingUsersNotifications = async () => {
    try {
      const pendingUsers = await invoke<PendingUser[]>('get_pending_users');
      
      const pendingNotifications: Notification[] = pendingUsers.map((user, index) => ({
        id: user.user_id,
        title: 'Novo usuário aguardando aprovação',
        message: `${user.user_name} (WWID: ${user.user_wwid}) solicitou acesso ao sistema`,
        time: 'Pendente',
        read: false,
        type: 'pending_user',
        userId: user.user_id,
        userName: user.user_name,
        userWwid: user.user_wwid,
      }));

      // Combina com notificações de scores existentes
      setNotifications(prev => {
        const scoreNotifs = prev.filter(n => n.type === 'pending_score');
        return [...pendingNotifications, ...scoreNotifs];
      });
    } catch (error) {
      console.error('Erro ao carregar notificações de usuários pendentes:', error);
    }
  };

  const handleApprove = async (userId: number) => {
    try {
      const privilege = userPrivileges[userId];
      
      if (!privilege) {
        showToast('Selecione um privilégio antes de aprovar', 'warning');
        return;
      }
      
      const permissions = userPermissions[userId] || { otif: false, nil: false, pickup: false, package: false };
      
      // Busca os dados do usuário pendente
      const pendingUsers = await invoke<PendingUser[]>('get_pending_users');
      const user = pendingUsers.find(u => u.user_id === userId);
      
      if (!user) {
        showToast('Usuário não encontrado', 'error');
        return;
      }
      
      // Atualiza o usuário com privilégio e permissões
      await invoke('update_user', { 
        userId, 
        name: user.user_name,
        wwid: user.user_wwid,
        privilege,
        status: 'Active',
        password: null,
        otif: permissions.otif ? 1 : 0,
        nil: permissions.nil ? 1 : 0,
        pickup: permissions.pickup ? 1 : 0,
        package: permissions.package ? 1 : 0
      });
      
      showToast('Usuário aprovado com sucesso!', 'success');
      
      // Limpa os estados do usuário aprovado
      setUserPrivileges(prev => {
        const newPriv = {...prev};
        delete newPriv[userId];
        return newPriv;
      });
      setUserPermissions(prev => {
        const newPerm = {...prev};
        delete newPerm[userId];
        return newPerm;
      });
      
      loadPendingUsersNotifications();
    } catch (error) {
      console.error('Erro ao aprovar usuário:', error);
      showToast('Erro ao aprovar usuário', 'error');
    }
  };

  const handleReject = async (userId: number) => {
    try {
      await invoke('update_user_status', { userId, status: 'Inactive' });
      showToast('Usuário rejeitado', 'warning');
      loadPendingUsersNotifications(); // Recarrega as notificações
    } catch (error) {
      console.error('Erro ao rejeitar usuário:', error);
      showToast('Erro ao rejeitar usuário', 'error');
    }
  };

  const handleSaveScoresFromNotification = async (
    recordId: number,
    supplierName: string,
    pendingFields: string[]
  ) => {
    console.log('💾 Iniciando salvamento de notas...');
    console.log('Record ID:', recordId);
    console.log('Campos pendentes:', pendingFields);
    
    try {
      // Pega o nome do usuário do sessionStorage
      const storedUser = sessionStorage.getItem('user');
      if (!storedUser) {
        showToast('Usuário não encontrado', 'error');
        return;
      }
      const user = JSON.parse(storedUser);
      const userName = user.user_name || 'Unknown';

      // Coleta os valores de todos os inputs
      const scores: Record<string, string> = {};

      for (const field of pendingFields) {
        const inputId = `score-${recordId}-${field}`;
        const inputElement = document.getElementById(inputId) as HTMLInputElement;
        
        console.log(`📝 Verificando campo ${field}, ID: ${inputId}`);
        
        if (!inputElement || !inputElement.value) {
          console.log(`⚠️ Campo ${field} vazio, pulando...`);
          continue;
        }

        const value = parseFloat(inputElement.value);
        console.log(`✓ Campo ${field} = ${value}`);
        
        if (isNaN(value) || value < 0 || value > 10) {
          showToast(`Nota inválida para ${field}. Use valores entre 0 e 10`, 'error');
          return;
        }

        scores[field.toLowerCase()] = value.toFixed(1);
      }

      if (Object.keys(scores).length === 0) {
        showToast('Preencha pelo menos uma nota', 'warning');
        return;
      }

      console.log('📊 Scores a salvar:', scores);

      // Salva cada nota no banco usando save_individual_score
      let savedCount = 0;
      for (const [fieldName, value] of Object.entries(scores)) {
        const scoreTypeMap: Record<string, string> = {
          'otif': 'otif',
          'nil': 'nil',
          'pickup': 'pickup',
          'package': 'package'
        };

        const scoreType = scoreTypeMap[fieldName];
        if (!scoreType) {
          console.log(`⚠️ scoreType não encontrado para ${fieldName}`);
          continue;
        }

        console.log(`💾 Salvando ${scoreType} = ${value}...`);
        console.log('Parâmetros:', {
          recordId,
          scoreType,
          scoreValue: value,
          userName
        });
        
        try {
          const result = await invoke('save_individual_score', {
            recordId,
            scoreType,
            scoreValue: value,
            userName
          });
          savedCount++;
          console.log(`✅ ${scoreType} salvo com sucesso! Resultado:`, result);
        } catch (err) {
          console.error(`❌ Erro ao salvar ${scoreType}:`, err);
          throw err;
        }
      }

      console.log(`✅ Total de ${savedCount} notas salvas!`);
      showToast(`${savedCount} nota(s) salva(s) para ${supplierName}!`, 'success');
      
      // Recarrega as notificações
      console.log('🔄 Recarregando notificações...');
      if (userId > 0) {
        await loadPendingScoresNotificationsWithId(userId);
      }
      
      console.log('✅ Processo completo!');
    } catch (error) {
      console.error('❌ Erro ao salvar notas:', error);
      showToast(`Erro: ${error}`, 'error');
    }
  };

  const handleEvaluateScore = (
    supplierId: string,
    supplierName: string,
    month: string,
    year: string,
    pendingFields: string[]
  ) => {
    // Define o primeiro campo pendente para avaliação
    if (pendingFields.length > 0) {
      const scoreType = pendingFields[0].toLowerCase();
      setScoreToEdit({
        supplierId,
        supplierName,
        month,
        year,
        scoreType,
        scoreValue: '',
      });
    }
  };

  const handleSaveScore = async () => {
    if (!scoreToEdit || !scoreToEdit.scoreValue) {
      showToast('Por favor, insira uma nota', 'warning');
      return;
    }

    const score = parseFloat(scoreToEdit.scoreValue);
    if (isNaN(score) || score < 0 || score > 10) {
      showToast('Nota deve ser entre 0 e 10', 'error');
      return;
    }

    try {
      await invoke('save_individual_score', {
        supplierId: scoreToEdit.supplierId,
        month: scoreToEdit.month,
        year: scoreToEdit.year,
        scoreType: scoreToEdit.scoreType,
        scoreValue: scoreToEdit.scoreValue,
        userName: userName,
      });

      showToast('Nota salva com sucesso!', 'success');
      setScoreToEdit(null);
      
      // Recarrega as notificações
      if (isSuperAdmin) {
        loadPendingUsersNotifications();
      } else if (userId > 0) {
        loadPendingScoresNotificationsWithId(userId);
      }
    } catch (error) {
      console.error('Erro ao salvar nota:', error);
      showToast('Erro ao salvar nota', 'error');
    }
  };

  const handleMinimize = () => {
    appWindow.minimize();
  };

  const handleMaximize = () => {
    appWindow.toggleMaximize();
  };

  const handleClose = async () => {
    if (isClosing) return;
    setIsClosing(true);

    console.log('🛑 Botão X personalizado clicado - iniciando rotina de desligamento');

    try {
      console.log('⏳ Encerrando heartbeat e marcando usuário como offline...');
      await userStatusManager.stop();

      if (userId) {
        console.log(`⏳ Forçando status offline para user_id ${userId}`);
        await invoke('set_user_online_status', { userId, isOnline: false });
      }

      console.log('✅ Usuário marcado como offline. Solicitando fechamento da janela...');
      await appWindow.close();
    } catch (error) {
      console.error('❌ Erro ao processar fechamento personalizado:', error);
      await appWindow.close();
    }
  };

  return (
    <div className="titlebar">
      <div className="titlebar-content" data-tauri-drag-region>
        <div className="titlebar-left" data-tauri-drag-region>
          {showUserInfo && (
            <div className="titlebar-user-info" data-tauri-drag-region>
              <div className="titlebar-avatar" data-tauri-drag-region>
                <i className="bi bi-person-circle"></i>
              </div>
              <div className="titlebar-user-details" data-tauri-drag-region>
                <span className="titlebar-user-name">{userName}</span>
                <span className="titlebar-user-role">{userRole}</span>
              </div>
            </div>
          )}
        </div>
        
        <div className="titlebar-center" data-tauri-drag-region>
          {/* Espaço vazio no centro */}
        </div>

        <div className="titlebar-controls">
          <button 
            className={`titlebar-button notification ${notifications.filter(n => !n.read).length > 0 ? 'has-notifications' : ''} ${bellAnimate ? 'bell-animate' : ''}`}
            onClick={() => setShowNotifications(!showNotifications)}
            title="Notificações"
          >
            <i className="bi bi-bell-fill"></i>
          </button>
          <div className="titlebar-separator"></div>
          <button className="titlebar-button minimize" onClick={handleMinimize}>
            <i className="bi bi-dash"></i>
          </button>
          <button className="titlebar-button maximize" onClick={handleMaximize}>
            <i className="bi bi-square"></i>
          </button>
          <button className="titlebar-button close" onClick={handleClose}>
            <i className="bi bi-x"></i>
          </button>
        </div>
      </div>

      {/* Overlay de Notificações */}
      {showNotifications && (
        <>
          <div className="notification-overlay" onClick={() => setShowNotifications(false)} />
          <div className="notification-panel">
            <div className="notification-header">
              <h3>
                <i className="bi bi-bell-fill"></i>
                Notificações
              </h3>
              <button className="close-notifications" onClick={() => setShowNotifications(false)}>
                <i className="bi bi-x"></i>
              </button>
            </div>
            <div className="notification-list">
              {notifications.length === 0 ? (
                <div className="notification-empty">
                  <i className="bi bi-inbox"></i>
                  <p>Nenhuma notificação</p>
                </div>
              ) : (
                notifications.map(notif => (
                  <div key={notif.id} className={`notification-item ${notif.read ? 'read' : 'unread'} ${notif.type}`}>
                    <div className="notification-icon">
                      {notif.type === 'pending_user' ? (
                        <i className="bi bi-person-plus"></i>
                      ) : notif.type === 'pending_score' ? (
                        <i className="bi bi-star"></i>
                      ) : (
                        <i className={`bi ${notif.read ? 'bi-envelope-open' : 'bi-envelope'}`}></i>
                      )}
                    </div>
                    <div className="notification-content">
                      <h4>{notif.title}</h4>
                      <p>{notif.message}</p>
                      <span className="notification-time">{notif.time}</span>
                      
                      {notif.type === 'pending_user' && notif.userId && (
                        <>
                          <div className="user-approval-section">
                            <div className="privilege-select-wrapper">
                              <label className="privilege-label">Privilégio:</label>
                              <select
                                className="privilege-select"
                                value={userPrivileges[notif.userId] || ''}
                                onChange={(e) => {
                                  setUserPrivileges(prev => ({
                                    ...prev,
                                    [notif.userId!]: e.target.value
                                  }));
                                }}
                                onClick={(e) => e.stopPropagation()}
                              >
                                <option value="">Selecione...</option>
                                <option value="User">User</option>
                                <option value="Admin">Admin</option>
                                <option value="Super Admin">Super Admin</option>
                              </select>
                            </div>
                            
                            {(userPrivileges[notif.userId] === 'Admin' || userPrivileges[notif.userId] === 'Super Admin') && (
                              <div className="permissions-checkboxes">
                                <label className="permission-checkbox">
                                  <input
                                    type="checkbox"
                                    checked={userPermissions[notif.userId]?.otif || false}
                                    onChange={(e) => {
                                      setUserPermissions(prev => ({
                                        ...prev,
                                        [notif.userId!]: {
                                          ...prev[notif.userId!] || { otif: false, nil: false, pickup: false, package: false },
                                          otif: e.target.checked
                                        }
                                      }));
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                  />
                                  <span>OTIF</span>
                                </label>
                                <label className="permission-checkbox">
                                  <input
                                    type="checkbox"
                                    checked={userPermissions[notif.userId]?.nil || false}
                                    onChange={(e) => {
                                      setUserPermissions(prev => ({
                                        ...prev,
                                        [notif.userId!]: {
                                          ...prev[notif.userId!] || { otif: false, nil: false, pickup: false, package: false },
                                          nil: e.target.checked
                                        }
                                      }));
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                  />
                                  <span>NIL</span>
                                </label>
                                <label className="permission-checkbox">
                                  <input
                                    type="checkbox"
                                    checked={userPermissions[notif.userId]?.pickup || false}
                                    onChange={(e) => {
                                      setUserPermissions(prev => ({
                                        ...prev,
                                        [notif.userId!]: {
                                          ...prev[notif.userId!] || { otif: false, nil: false, pickup: false, package: false },
                                          pickup: e.target.checked
                                        }
                                      }));
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                  />
                                  <span>PICKUP</span>
                                </label>
                                <label className="permission-checkbox">
                                  <input
                                    type="checkbox"
                                    checked={userPermissions[notif.userId]?.package || false}
                                    onChange={(e) => {
                                      setUserPermissions(prev => ({
                                        ...prev,
                                        [notif.userId!]: {
                                          ...prev[notif.userId!] || { otif: false, nil: false, pickup: false, package: false },
                                          package: e.target.checked
                                        }
                                      }));
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                  />
                                  <span>PACKAGE</span>
                                </label>
                              </div>
                            )}
                          </div>
                          
                          <div className="notification-actions">
                            <button 
                              className="btn-approve-notif"
                              onClick={() => handleApprove(notif.userId!)}
                            >
                              <i className="bi bi-check-lg"></i>
                              Aprovar
                            </button>
                            <button 
                              className="btn-reject-notif"
                              onClick={() => handleReject(notif.userId!)}
                            >
                              <i className="bi bi-x-lg"></i>
                              Rejeitar
                            </button>
                          </div>
                        </>
                      )}

                      {notif.type === 'pending_score' && notif.supplierId && (
                        <>
                          <div className="scores-row">
                            {notif.pendingFields?.map((field, idx) => (
                              <div key={`${field}-${idx}`} className="score-input-col">
                                <label className="score-label">{field}</label>
                                <input 
                                  type="number" 
                                  min="0" 
                                  max="10" 
                                  step="0.1"
                                  className="score-input"
                                  placeholder="0.0"
                                  id={`score-${notif.recordId}-${field}`}
                                  onClick={(e) => e.stopPropagation()}
                                  onInput={(e) => {
                                    const input = e.target as HTMLInputElement;
                                    const value = parseFloat(input.value);
                                    if (value > 10) {
                                      input.value = '10';
                                    } else if (value < 0) {
                                      input.value = '0';
                                    }
                                  }}
                                  onBlur={(e) => {
                                      const value = parseFloat(e.target.value);
                                      if (!isNaN(value)) {
                                        const clamped = Math.min(Math.max(value, 0), 10);
                                        e.target.value = clamped.toFixed(1);
                                      }
                                    }}
                                  />
                                </div>
                              ))}
                          </div>
                          <div className="notification-actions">
                            <button 
                              className="btn-evaluate-notif"
                              onClick={() => handleSaveScoresFromNotification(
                                notif.recordId!,
                                notif.supplierName!,
                                notif.pendingFields || []
                              )}
                            >
                              <i className="bi bi-save"></i>
                              Salvar Notas
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}

      {/* Modal de Avaliação de Score */}
      {scoreToEdit && (
        <>
          <div className="notification-overlay" onClick={() => setScoreToEdit(null)} />
          <div className="score-edit-modal">
            <div className="score-edit-header">
              <h3>
                <i className="bi bi-star-fill"></i>
                Avaliar Fornecedor
              </h3>
              <button className="close-modal" onClick={() => setScoreToEdit(null)}>
                <i className="bi bi-x"></i>
              </button>
            </div>
            <div className="score-edit-content">
              <div className="score-info">
                <p><strong>Fornecedor:</strong> {scoreToEdit.supplierName}</p>
                <p><strong>Período:</strong> {scoreToEdit.month}/{scoreToEdit.year}</p>
                <p><strong>Campo:</strong> {scoreToEdit.scoreType.toUpperCase()}</p>
              </div>
              <div className="score-input-group">
                <label htmlFor="score-value">Nota (0 - 10):</label>
                <input
                  id="score-value"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={scoreToEdit.scoreValue}
                  onChange={(e) => setScoreToEdit({ ...scoreToEdit, scoreValue: e.target.value })}
                  placeholder="Digite a nota"
                  autoFocus
                />
              </div>
              <div className="score-edit-actions">
                <button className="btn-cancel" onClick={() => setScoreToEdit(null)}>
                  <i className="bi bi-x-lg"></i>
                  Cancelar
                </button>
                <button className="btn-save" onClick={handleSaveScore}>
                  <i className="bi bi-check-lg"></i>
                  Salvar
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TitleBar;
