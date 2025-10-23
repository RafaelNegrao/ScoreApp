import "./PrivilegesManager.css";
import { usePermissions } from "../contexts/PermissionsContext";

const roleInfo = {
  'Super Admin': {
    icon: 'bi-star-fill',
    color: '#ffd700',
    description: 'Acesso total e irrestrito a todas as funcionalidades do sistema',
    permissions: [
      'Visualizar todas as abas e sub-abas',
      'Editar e deletar notas de fornecedores',
      'Gerenciar todos os usuários e fornecedores',
      'Configurar critérios de avaliação',
      'Exportar e importar dados',
      'Gerenciar listas e configurações',
      'Acessar logs do sistema'
    ]
  },
  'Admin': {
    icon: 'bi-shield-fill-check',
    color: '#3b82f6',
    description: 'Acesso administrativo com permissões limitadas',
    permissions: [
      'Visualizar todas as abas principais',
      'Editar notas de fornecedores',
      'Editar apenas o próprio usuário',
      'Não pode editar WWID',
      'Exportar dados',
      'Gerenciar listas',
      'SEM acesso a: Criteria, Suppliers, Log'
    ]
  },
  'User': {
    icon: 'bi-person-fill',
    color: '#10b981',
    description: 'Acesso padrão limitado para visualização',
    permissions: [
      'Visualizar apenas Home e Timeline',
      'Ver métricas e históricos',
      'Editar apenas o próprio usuário',
      'Não pode editar WWID',
      'Acesso limitado a Settings (System, Users, Info)',
      'SEM acesso a Score e outras abas'
    ]
  }
};

function PrivilegesManager() {
  const { isSuperAdmin } = usePermissions();

  if (!isSuperAdmin) {
    return (
      <div className="privileges-denied">
        <i className="bi bi-shield-lock-fill"></i>
        <h3>Acesso Restrito</h3>
        <p>Apenas Super Admins podem visualizar informações detalhadas sobre privilégios.</p>
      </div>
    );
  }

  return (
    <div className="privileges-manager">
      <div className="privileges-header">
        <div className="privileges-title">
          <i className="bi bi-shield-lock"></i>
          <h3>Gerenciamento de Privilégios</h3>
        </div>
        <p className="privileges-subtitle">
          Visão geral dos níveis de acesso e permissões do sistema
        </p>
      </div>

      <div className="privileges-info-notice">
        <i className="bi bi-info-circle-fill"></i>
        <p>Os privilégios são definidos no campo <code>user_privilege</code> da tabela <code>users_table</code>. Para alterar o nível de acesso de um usuário, edite este campo diretamente através da aba Users.</p>
      </div>

      <div className="privileges-roles-grid">
        {Object.entries(roleInfo).map(([role, info]) => (
          <div key={role} className="privilege-role-card">
            <div className="role-card-header">
              <i className={`bi ${info.icon}`} style={{ color: info.color }}></i>
              <h4>{role}</h4>
            </div>
            <p className="role-description">{info.description}</p>
            <div className="role-permissions">
              <h5>Permissões:</h5>
              <ul>
                {info.permissions.map((perm, idx) => (
                  <li key={idx}>
                    <i className="bi bi-check-circle-fill"></i>
                    {perm}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      <div className="privileges-footer-note">
        <i className="bi bi-lightbulb-fill"></i>
        <div>
          <strong>Nota importante:</strong>
          <p>Para modificar privilégios de um usuário, vá para a aba <strong>Users</strong> e edite o campo "Privilege" do usuário desejado. Os valores aceitos são: <code>Super Admin</code>, <code>Admin</code> ou <code>User</code>.</p>
        </div>
      </div>
    </div>
  );
}

export default PrivilegesManager;
