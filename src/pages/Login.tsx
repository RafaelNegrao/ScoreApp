import { useState, FormEvent, useEffect } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { appWindow } from "@tauri-apps/api/window";
import { useToastContext } from "../contexts/ToastContext";
import { userStatusManager } from "../utils/userStatus";
import 'bootstrap-icons/font/bootstrap-icons.css';
import "./Login.css";

interface LoginProps {
  onLogin: () => void;
}

interface LoginResponse {
  success: boolean;
  message: string;
  user?: {
    user_id: number;
    user_name: string;
    user_wwid: string;
    user_privilege: string;
  };
}

// Gerenciador de Credenciais (localStorage)
class CredentialsManager {
  static STORAGE_KEY = 'scoreapp_credentials';

  static saveCredentials(username: string, password: string): boolean {
    try {
      const credentials = {
        username,
        password,
        savedAt: new Date().toISOString()
      };
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(credentials));
      return true;
    } catch (error) {
      console.error('Erro ao salvar credenciais:', error);
      return false;
    }
  }

  static loadSavedCredentials(): { username: string; password: string } {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (saved) {
        const credentials = JSON.parse(saved);
        return {
          username: credentials.username || '',
          password: credentials.password || ''
        };
      }
    } catch (error) {
      console.error('Erro ao carregar credenciais:', error);
    }
    return { username: '', password: '' };
  }

  static clearSavedCredentials(): boolean {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
      return true;
    } catch (error) {
      console.error('Erro ao limpar credenciais:', error);
      return false;
    }
  }

  static hasSavedCredentials(): boolean {
    return !!localStorage.getItem(this.STORAGE_KEY);
  }
}

/**
 * Componente de Login.
 * Responsável por autenticar o usuário através do banco de dados SQLite.
 * Valida credenciais contra a tabela users_table.
 */
function Login({ onLogin }: LoginProps) {
  const [isSignupMode, setIsSignupMode] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { showToast } = useToastContext();
  
  // Estados para mostrar/ocultar senha
  const [showPassword, setShowPassword] = useState(false);
  const [showSignupPassword, setShowSignupPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Campos de cadastro
  const [signupWwid, setSignupWwid] = useState("");
  const [signupName, setSignupName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupConfirmPassword, setSignupConfirmPassword] = useState("");

  // Carrega credenciais salvas ao montar o componente
  useEffect(() => {
    if (CredentialsManager.hasSavedCredentials()) {
      const { username: savedUsername, password: savedPassword } = CredentialsManager.loadSavedCredentials();
      if (savedUsername && savedPassword) {
        setUsername(savedUsername);
        setPassword(savedPassword);
        setRememberMe(true);
      }
    }
  }, []);

  // Garante que o fundo da janela permaneça transparente enquanto o login está ativo
  useEffect(() => {
    const rootElement = document.getElementById("root");
    document.body.classList.add("login-page");
    rootElement?.classList.add("login-page-root");

    // Centraliza a janela na tela
    appWindow.center();

    return () => {
      document.body.classList.remove("login-page");
      rootElement?.classList.remove("login-page-root");
    };
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    
    if (!username || !password) {
      setError("Por favor, preencha todos os campos");
      return;
    }

    setLoading(true);

    try {
      console.log("🔐 Validando login para:", username);
      
      const response = await invoke<LoginResponse>("validate_login", {
        username,
        password,
      });

      console.log("📨 Resposta do backend:", response);

      if (response.success && response.user) {
        // Gerenciar remember-me
        if (rememberMe) {
          CredentialsManager.saveCredentials(username, password);
        } else {
          CredentialsManager.clearSavedCredentials();
        }

        // Armazena informações do usuário no sessionStorage
        sessionStorage.setItem("user", JSON.stringify(response.user));
        console.log("✅ Login bem-sucedido! User salvo no sessionStorage:", response.user);
        
        // Dispara evento customizado para que o PermissionsContext recarregue
        window.dispatchEvent(new Event('userLoggedIn'));
        console.log("📢 Evento 'userLoggedIn' disparado");
        
        // Inicia o gerenciamento de status online
        userStatusManager.start(response.user.user_id);
        
        // Maximiza a janela ao fazer login
        await appWindow.maximize();
        
        onLogin();
      } else {
        console.log("❌ Login falhou:", response.message);
        
        // Verifica se é mensagem de pendência para mostrar como toast warning
        if (response.message === "Aguardando autorização do Admin") {
          showToast(response.message, 'warning');
        } else if (response.message.includes("inativo")) {
          showToast(response.message, 'error');
        } else {
          setError(response.message);
        }
      }
    } catch (err) {
      console.error("❌ Erro na validação:", err);
      setError(`Erro ao conectar: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // Validações
    if (!signupWwid || !signupName || !signupEmail || !signupPassword || !signupConfirmPassword) {
      showToast("Por favor, preencha todos os campos", 'error');
      return;
    }

    if (!signupEmail.endsWith("@cummins.com")) {
      showToast("Use um email corporativo Cummins (@cummins.com)", 'error');
      return;
    }

    if (signupPassword !== signupConfirmPassword) {
      showToast("As senhas não coincidem", 'error');
      return;
    }

    if (signupPassword.length < 6) {
      showToast("A senha deve ter no mínimo 6 caracteres", 'error');
      return;
    }

    setLoading(true);

    try {
      console.log("� Verificando se WWID já existe...");
      
      // Verifica se WWID já existe
      const wwidExists = await invoke<boolean>('check_wwid_exists', {
        wwid: signupWwid,
      });

      if (wwidExists) {
        showToast("WWID já cadastrado no sistema", 'error');
        setLoading(false);
        return;
      }

      console.log("�📝 Cadastrando novo usuário:", signupWwid);
      
      // Criar usuário com status Pendent
      await invoke('create_user', {
        name: signupName,
        wwid: signupWwid,
        privilege: 'User',
        status: 'Pendent',
        password: signupPassword,
        otif: 0,
        nil: 0,
        pickup: 0,
        package: 0,
      });

      console.log("✅ Usuário cadastrado com sucesso!");
      
      // Limpa campos de cadastro
      setSignupWwid("");
      setSignupName("");
      setSignupEmail("");
      setSignupPassword("");
      setSignupConfirmPassword("");
      
      // Volta para tela de login com mensagem de sucesso
      setError("");
      setIsSignupMode(false);
      setLoading(false);
      
      // Mostra mensagem informativa
      showToast("Cadastro realizado com sucesso! Aguarde a aprovação do administrador.", 'success');
    } catch (err) {
      console.error("❌ Erro no cadastro:", err);
      const errorMessage = String(err);
      
      // Trata mensagens de erro específicas
      if (errorMessage.includes("WWID já cadastrado")) {
        showToast("WWID já cadastrado no sistema", 'error');
      } else {
        showToast(`Erro ao cadastrar: ${err}`, 'error');
      }
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setError("");
    setIsSignupMode(!isSignupMode);
  };

  return (
    <div className="login-container">
      <div className={`login-content ${isSignupMode ? 'signup-mode' : ''}`}>
        {/* Lado Esquerdo: Formulários (Fixo) */}
        <div className="login-form-section">
          {/* Formulário de Login */}
          <div className={`login-form-wrapper ${!isSignupMode ? 'login-form' : 'signup-form'}`}>
            {!isSignupMode ? (
              <>
                <div className="app-name">Supplier Score App</div>
                <h1 className="login-title">Login</h1>
                
                <form onSubmit={handleSubmit} className="login-form">
                  <div className="form-group">
                    <label htmlFor="username">WWID</label>
                    <input
                      type="text"
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder=""
                      required
                      disabled={loading}
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="password">senha</label>
                    <div className="password-input-wrapper">
                      <input
                        type={showPassword ? "text" : "password"}
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder=""
                        required
                        disabled={loading}
                        className="form-input"
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() => setShowPassword(!showPassword)}
                        tabIndex={-1}
                        aria-label="Mostrar/ocultar senha"
                      >
                        <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                      </button>
                    </div>
                  </div>

                  <div className="form-options">
                    <label className="remember-me">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        disabled={loading}
                      />
                      <span>Lembrar minha senha</span>
                    </label>
                  </div>

                  {error && !isSignupMode && (
                    <div className="error-message">
                      <i className="bi bi-exclamation-circle"></i>
                      {error}
                    </div>
                  )}

                  <button type="submit" className="login-button" disabled={loading}>
                    {loading ? "Entrando..." : "Entrar"}
                  </button>

                  <div className="register-link" onClick={toggleMode}>
                    ainda não tenho uma conta
                  </div>
                </form>
              </>
            ) : (
              <>
                <h1 className="login-title">Crie sua conta</h1>
                
                <form onSubmit={handleSignup} className="login-form">
                  <div className="form-group">
                    <label htmlFor="signup-wwid">WWID</label>
                    <input
                      type="text"
                      id="signup-wwid"
                      value={signupWwid}
                      onChange={(e) => setSignupWwid(e.target.value)}
                      placeholder=""
                      required
                      disabled={loading}
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="signup-name">nome completo</label>
                    <input
                      type="text"
                      id="signup-name"
                      value={signupName}
                      onChange={(e) => setSignupName(e.target.value)}
                      placeholder=""
                      required
                      disabled={loading}
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="signup-email">email corporativo</label>
                    <input
                      type="email"
                      id="signup-email"
                      value={signupEmail}
                      onChange={(e) => setSignupEmail(e.target.value)}
                      placeholder="@cummins.com"
                      required
                      disabled={loading}
                      className="form-input"
                    />
                  </div>

                  <div className="form-group-row">
                    <div className="form-group">
                      <label htmlFor="signup-password">senha</label>
                      <div className="password-input-wrapper">
                        <input
                          type={showSignupPassword ? "text" : "password"}
                          id="signup-password"
                          value={signupPassword}
                          onChange={(e) => setSignupPassword(e.target.value)}
                          placeholder=""
                          required
                          disabled={loading}
                          className="form-input"
                        />
                        <button
                          type="button"
                          className="password-toggle"
                          onClick={() => setShowSignupPassword(!showSignupPassword)}
                          tabIndex={-1}
                          aria-label="Mostrar/ocultar senha"
                        >
                          <i className={`bi ${showSignupPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                        </button>
                      </div>
                    </div>

                    <div className="form-group">
                      <label htmlFor="signup-confirm">confirmar senha</label>
                      <div className="password-input-wrapper">
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          id="signup-confirm"
                          value={signupConfirmPassword}
                          onChange={(e) => setSignupConfirmPassword(e.target.value)}
                          placeholder=""
                          required
                          disabled={loading}
                          className="form-input"
                        />
                        <button
                          type="button"
                          className="password-toggle"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          tabIndex={-1}
                          aria-label="Mostrar/ocultar senha"
                        >
                          <i className={`bi ${showConfirmPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                        </button>
                      </div>
                    </div>
                  </div>

                  {error && isSignupMode && (
                    <div className="error-message">
                      <i className="bi bi-exclamation-circle"></i>
                      {error}
                    </div>
                  )}

                  <button type="submit" className="login-button" disabled={loading}>
                    {loading ? "Cadastrando..." : "Cadastrar"}
                  </button>

                  <div className="register-link" onClick={toggleMode}>
                    já tenho uma conta
                  </div>
                </form>
              </>
            )}
          </div>
        </div>

        {/* Lado Direito: Slider de Imagens */}
        <div className="login-image-container">
          <div className="login-image-slider">
            {/* Imagem 1: Fundo para Login */}
            <div className="login-image-section login-image-login">
            </div>

            {/* Imagem 2: Fundo para Cadastro */}
            <div className="login-image-section login-image-signup">
            </div>
          </div>
          
          {/* Copyright */}
          <div className="cummins-copyright">Cummins Inc. ®</div>
        </div>
      </div>
    </div>
  );
}

export default Login;
