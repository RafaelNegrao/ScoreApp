import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { appWindow } from "@tauri-apps/api/window";
import { invoke } from "@tauri-apps/api/tauri";
import { applyTheme, getStoredTheme } from "./themes";
import { userStatusManager } from "./utils/userStatus";
import SplashScreen from "./components/SplashScreen";
import TitleBar from "./components/TitleBar";
import BottomBar from "./components/BottomBar";
import { ToastContainer } from "./components/ToastContainer";
import { ToastProvider, useToastContext } from "./contexts/ToastContext";
import { PermissionsProvider } from "./contexts/PermissionsContext";
import Login from "./pages/Login";
import MainLayout from "./components/MainLayout";
import Home from "./pages/Home";
import Score from "./pages/Score";
import Timeline from "./pages/Timeline";
import Risks from "./pages/Risks";
import Settings from "./pages/Settings";

/**
 * Componente que renderiza a TitleBar condicionalmente
 */
function ConditionalTitleBar() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  
  return <TitleBar showUserInfo={!isLoginPage} />;
}

/**
 * Componente que renderiza a BottomBar condicionalmente
 */
function ConditionalBottomBar() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  
  return !isLoginPage ? <BottomBar /> : null;
}

/**
 * Componente principal da aplicação.
 * Gerencia as rotas e o estado de autenticação do usuário.
 * Utiliza React Router para navegação entre páginas.
 */
function AppContent() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const { toasts, removeToast } = useToastContext();

  // Log para debug do estado de autenticação
  useEffect(() => {
    console.log("Estado de autenticação mudou:", isAuthenticated);
  }, [isAuthenticated]);

  return (
    <>
      <BrowserRouter>
        <ConditionalTitleBar />
        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
              <Login onLogin={() => {
                console.log("onLogin callback chamado! Alterando isAuthenticated para true");
                setIsAuthenticated(true);
              }} />
            )
          }
        />
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <MainLayout />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        >
          <Route index element={<Home />} />
  <Route path="score" element={<Score />} />
          <Route path="timeline" element={<Timeline />} />
          <Route path="risks" element={<Risks />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        {/* Redireciona qualquer rota desconhecida para login ou home */}
        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />}
        />
      </Routes>
      <ConditionalBottomBar />
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </BrowserRouter>
    </>
  );
}

function App() {
  const closingRef = useRef(false);
  // Aplica o tema salvo ao inicializar
  useEffect(() => {
    applyTheme(getStoredTheme());

    // Configura listeners para garantir que is_online seja 0 ao fechar
    const setupCloseListener = async () => {
      // Listener para fechar a janela normalmente (inclui botão X)
      await appWindow.onCloseRequested(async (event) => {
        if (closingRef.current) {
          console.log('⚠️ Fechamento já em andamento - permitindo encerramento padrão');
          return;
        }
        closingRef.current = true;

        // Previne o fechamento imediato
        event.preventDefault();
        
        console.log('🔴 ========================================');
        console.log('🔴 BOTÃO X CLICADO - Iniciando processo de fechamento');
        console.log('🔴 ========================================');
        
        try {
          // Para o gerenciamento de status (define is_online = 0) - AGUARDA
          console.log('⏳ Chamando userStatusManager.stop()...');
          await userStatusManager.stop();
          console.log('✅ userStatusManager.stop() concluído');
          
          // Garante que todos sejam offline antes de fechar
          console.log('⏳ Chamando reset_all_users_offline...');
          await invoke('reset_all_users_offline');
          console.log('✅ reset_all_users_offline concluído');
          
          // Delay para garantir persistência no banco
          console.log('⏳ Aguardando 300ms para garantir escrita no banco...');
          await new Promise(resolve => setTimeout(resolve, 300));
          console.log('✅ Tudo pronto para fechar!');
        } catch (error) {
          console.error('❌ Erro durante fechamento:', error);
        } finally {
          console.log('🚪 Fechando janela...');
          await appWindow.close();
        }
      });
    };

    // Listener para beforeunload (caso o app feche inesperadamente)
    const handleBeforeUnload = async () => {
      console.log('🔴 beforeunload - definindo usuários como offline...');
      await userStatusManager.stop();
      try {
        await invoke('reset_all_users_offline');
      } catch (error) {
        console.error('❌ Erro ao resetar status no beforeunload:', error);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    setupCloseListener();

    // Cleanup
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  return (
    <ToastProvider>
      <PermissionsProvider>
        <AppContent />
      </PermissionsProvider>
    </ToastProvider>
  );
}

export default App;