import { Outlet, useNavigate, useLocation } from "react-router-dom";
import 'bootstrap-icons/font/bootstrap-icons.css';
import "./MainLayout.css";
import { useState, useEffect } from "react";
import { usePermissions } from "../contexts/PermissionsContext";

/**
 * Layout principal da aplicação.
 * Contém o menu lateral com navegação e área de conteúdo dinâmico.
 * Utiliza ícones Bootstrap Icons e menu com estado persistente.
 */
function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { permissions } = usePermissions();
  const [menuOpen, setMenuOpen] = useState(() => {
    return localStorage.getItem('menuOpen') === 'true';
  });

  // Efeito para aplicar estado inicial do menu
  useEffect(() => {
    if (menuOpen) {
      document.body.classList.add('menu-expanded');
    }
    // Cleanup quando o componente desmontar
    return () => {
      document.body.classList.remove('menu-expanded');
    };
  }, []);

  // Efeito para controlar o menu baseado no tamanho da tela
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1300) {
        setMenuOpen(false);
      } else if (window.innerWidth >= 1300) {
        setMenuOpen(true);
      }
    };

    // Executa ao montar o componente
    handleResize();

    // Adiciona listener para mudanças de tamanho
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  useEffect(() => {
    localStorage.setItem('menuOpen', menuOpen.toString());
    // Adiciona/remove classe no body para controlar a barra inferior
    if (menuOpen) {
      document.body.classList.add('menu-expanded');
    } else {
      document.body.classList.remove('menu-expanded');
    }
  }, [menuOpen]);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  const allMenuItems = [
    { path: "/", icon: "bi-house", label: "Home", permission: permissions.canAccessHome },
    { path: "/score", icon: "bi-trophy", label: "Score", permission: permissions.canAccessScore },
    { path: "/timeline", icon: "bi-clock-history", label: "Timeline", permission: permissions.canAccessTimeline },
    { path: "/contributors", icon: "bi-people", label: "Contributors", permission: permissions.canAccessContributors },
    { path: "/risks", icon: "bi-exclamation-triangle", label: "Risks", permission: permissions.canAccessRisks },
  ];
  
  // Filtra apenas os itens que o usuário tem permissão
  const menuItems = allMenuItems.filter(item => item.permission);

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className="main-layout">
      <button 
        className={`toggle-btn ${menuOpen ? 'active' : ''}`}
        onClick={toggleMenu}
      >
        <i className={menuOpen ? 'bi bi-x' : 'bi bi-list'}></i>
      </button>

      <nav className={`sidebar ${menuOpen ? 'active' : ''}`}>
        <div className="sidebar-menu">
          {menuItems.map((item, index) => {
            return (
              <button
                key={item.path}
                className={`menu-item ${isActive(item.path) ? "active" : ""}`}
                onClick={() => navigate(item.path)}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <span className="icon">
                  <i className={`bi ${item.icon}`}></i>
                </span>
                <span className="text">{item.label}</span>
              </button>
            );
          })}
        </div>
        
        <div className="sidebar-footer">
          {permissions.canAccessSettings && (
            <button
              className={`menu-item ${isActive("/settings") ? "active" : ""} settings-link`}
              onClick={() => navigate("/settings")}
            >
              <span className="icon">
                <i className="bi bi-gear"></i>
              </span>
              <span className="text">Settings</span>
            </button>
          )}
        </div>
      </nav>
      
      <main className={`main-content ${menuOpen ? 'expanded' : ''}`}>
        <Outlet />
      </main>
    </div>
  );
}

export default MainLayout;
