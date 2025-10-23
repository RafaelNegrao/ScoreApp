import { useState, useEffect } from "react";
import 'bootstrap-icons/font/bootstrap-icons.css';
import "./Home.css";
import { invoke } from '@tauri-apps/api/tauri';

/**
 * Página inicial (Home).
 * Exibe dashboard com estatísticas e resumo das principais métricas.
 */
interface UserPermissions {
  otif: string;
  nil: string;
  pickup: string;
  package: string;
}

function Home() {
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [userName, setUserName] = useState<string>('');
  const [userWWID, setUserWWID] = useState<string>('');
  const [userPrivilege, setUserPrivilege] = useState<string>('');
  const [permissions, setPermissions] = useState<UserPermissions>({
    otif: 'Não',
    nil: 'Não',
    pickup: 'Não',
    package: 'Não',
  });
  const [totalSuppliers, setTotalSuppliers] = useState<number>(0);
  const [totalEvaluations, setTotalEvaluations] = useState<number>(0);
  const [averageScore, setAverageScore] = useState<number>(0);
  const [totalUsers, setTotalUsers] = useState<number>(0);

  useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      const user = JSON.parse(storedUser);
      setUserName(user.user_name || 'Usuário');
      setUserWWID(user.user_wwid || 'N/A');
      setUserPrivilege(user.user_privilege || 'Padrão');
      if (user.permissions) {
        setPermissions(user.permissions);
      }
    }
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      const suppliers = await invoke<number>('get_total_suppliers');
      setTotalSuppliers(suppliers);

      const evaluations = await invoke<number>('get_total_evaluations');
      setTotalEvaluations(evaluations);

      const score = await invoke<number>('get_average_score');
      setAverageScore(score);

      const users = await invoke<number>('get_total_users');
      setTotalUsers(users);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const isPermissionActive = (permission: string): boolean => {
    return permission === 'Sim' || permission === 'Yes' || permission === '1' || permission === 'true';
  };

  const handlePrevCard = () => {
    setCurrentCardIndex((prev) => (prev === 0 ? 2 : prev - 1));
  };

  const handleNextCard = () => {
    setCurrentCardIndex((prev) => (prev === 2 ? 0 : prev + 1));
  };

  return (
    <div className="home-dashboard">
      {/* Saudação */}
      <div className="welcome-section">
        <h1>Bem-vindo, {userName}!</h1>
        <p>Painel de Controle</p>
      </div>

      {/* Cards de Estatísticas */}
      <div className="stats-grid">
        <div className="stat-card" style={{ '--card-color': '#3b82f6' } as React.CSSProperties}>
          <div className="stat-icon">
            <i className="bi bi-building"></i>
          </div>
          <div className="stat-content">
            <h3>{totalSuppliers.toLocaleString('pt-BR')}</h3>
            <p>Fornecedores</p>
          </div>
        </div>

        <div className="stat-card" style={{ '--card-color': '#8b5cf6' } as React.CSSProperties}>
          <div className="stat-icon">
            <i className="bi bi-bar-chart"></i>
          </div>
          <div className="stat-content">
            <h3>{totalEvaluations.toLocaleString('pt-BR')}</h3>
            <p>Avaliações</p>
          </div>
        </div>

        <div className="stat-card" style={{ '--card-color': '#10b981' } as React.CSSProperties}>
          <div className="stat-icon">
            <i className="bi bi-graph-up"></i>
          </div>
          <div className="stat-content">
            <h3>{averageScore.toFixed(1)}</h3>
            <p>Score Médio</p>
          </div>
        </div>

        <div className="stat-card" style={{ '--card-color': '#f59e0b' } as React.CSSProperties}>
          <div className="stat-icon">
            <i className="bi bi-people"></i>
          </div>
          <div className="stat-content">
            <h3>{totalUsers.toLocaleString('pt-BR')}</h3>
            <p>Usuários</p>
          </div>
        </div>
      </div>

      {/* Carousel de Informações */}
      <div className="carousel-section">
        <button className="carousel-btn carousel-btn-prev" onClick={handlePrevCard}>
          <i className="bi bi-chevron-left"></i>
        </button>
        
        <div className="carousel-container-wrapper">
          {/* Card 1: Perfil */}
          <div className={`carousel-card info-card ${currentCardIndex === 0 ? 'center' : currentCardIndex === 1 ? 'left' : 'right'}`}>
            <div className="info-header">
              <i className="bi bi-person-circle"></i>
              <h3>Perfil</h3>
            </div>
            <div className="info-body">
              <div className="info-row">
                <span className="info-label">Nome:</span>
                <span className="info-value">{userName}</span>
              </div>
              <div className="info-row">
                <span className="info-label">WWID:</span>
                <span className="info-value">{userWWID}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Privilégio:</span>
                <span className="info-value">{userPrivilege}</span>
              </div>
            </div>
          </div>

          {/* Card 2: Permissões */}
          <div className={`carousel-card info-card ${currentCardIndex === 1 ? 'center' : currentCardIndex === 2 ? 'left' : 'right'}`}>
            <div className="info-header">
              <i className="bi bi-shield-check"></i>
              <h3>Permissões</h3>
            </div>
            <div className="info-body">
              <div className="permission-item">
                <i 
                  className={isPermissionActive(permissions.otif) ? "bi bi-check-circle-fill" : "bi bi-x-circle-fill"} 
                  style={{ color: isPermissionActive(permissions.otif) ? '#10b981' : '#ef4444' }}
                ></i>
                <span>OTIF</span>
              </div>
              <div className="permission-item">
                <i 
                  className={isPermissionActive(permissions.nil) ? "bi bi-check-circle-fill" : "bi bi-x-circle-fill"} 
                  style={{ color: isPermissionActive(permissions.nil) ? '#10b981' : '#ef4444' }}
                ></i>
                <span>NIL</span>
              </div>
              <div className="permission-item">
                <i 
                  className={isPermissionActive(permissions.pickup) ? "bi bi-check-circle-fill" : "bi bi-x-circle-fill"} 
                  style={{ color: isPermissionActive(permissions.pickup) ? '#10b981' : '#ef4444' }}
                ></i>
                <span>Pickup</span>
              </div>
              <div className="permission-item">
                <i 
                  className={isPermissionActive(permissions.package) ? "bi bi-check-circle-fill" : "bi bi-x-circle-fill"} 
                  style={{ color: isPermissionActive(permissions.package) ? '#10b981' : '#ef4444' }}
                ></i>
                <span>Package</span>
              </div>
            </div>
          </div>

          {/* Card 3: Sistema */}
          <div className={`carousel-card info-card ${currentCardIndex === 2 ? 'center' : currentCardIndex === 0 ? 'left' : 'right'}`}>
            <div className="info-header">
              <i className="bi bi-gear-fill"></i>
              <h3>Sistema</h3>
            </div>
            <div className="info-body">
              <div className="info-row">
                <span className="info-label">Versão:</span>
                <span className="info-value">1.1.5</span>
              </div>
              <div className="info-row">
                <span className="info-label">Banco:</span>
                <span className="info-value status-connected">
                  <i className="bi bi-circle-fill"></i> Conectado
                </span>
              </div>
              <div className="info-row">
                <span className="info-label">Atualizado:</span>
                <span className="info-value">Hoje</span>
              </div>
            </div>
          </div>
        </div>
        
        <button className="carousel-btn carousel-btn-next" onClick={handleNextCard}>
          <i className="bi bi-chevron-right"></i>
        </button>
      </div>
    </div>
  );
}

export default Home;
