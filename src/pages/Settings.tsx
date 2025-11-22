import { useState, useEffect } from "react";
import { invoke } from '@tauri-apps/api/tauri';
import 'bootstrap-icons/font/bootstrap-icons.css';
import ThemeSelector from "../components/ThemeSelector";
import SupplierManager from "../components/SupplierManager";
import PrivilegesManager from "../components/PrivilegesManager";
import Users from "./Users";
import Lists from "./Lists";
import LogsTable from "../components/LogsTable";
import { ToastContainer } from "../components/ToastContainer";
import { useToast } from "../hooks/useToast";
import { usePermissions } from "../contexts/PermissionsContext";
import "./Settings.css";

interface Criteria {
  criteria_id: number;
  criteria_target_id?: number | null;
  criteria_name: string;
  criteria_weight: number;
  criteria_target: number;
}

/**
 * Componente da aba de Critérios
 */
function CriteriaTab() {
  const [criteria, setCriteria] = useState<Criteria[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [hasChanges, setHasChanges] = useState<boolean>(false);
  const { toasts, showToast, removeToast } = useToast();

  type CriteriaDisplayItem = {
    key: string;
    label: string;
    value: number;
    min: number;
    max: number;
    step: number;
    precision: number;
    type: 'weight' | 'target';
    onChange: (value: number) => void;
  };

  // Carregar critérios do banco de dados
  useEffect(() => {
    const loadCriteria = async () => {
      try {
        setIsLoading(true);
        console.log('🔄 Iniciando carregamento de critérios...');
        const loadedCriteria = await invoke<Criteria[]>('get_criteria');
        console.log('📦 Critérios recebidos do backend:', loadedCriteria);
        console.log('📊 Quantidade de critérios:', loadedCriteria?.length);
        
        if (loadedCriteria && loadedCriteria.length > 0) {
          console.log('✅ Definindo critérios no estado');
          setCriteria(loadedCriteria);
        } else {
          console.warn('⚠️ Nenhum critério foi retornado');
        }
      } catch (error) {
        console.error('❌ Erro ao carregar critérios:', error);
      } finally {
        console.log('🏁 Finalizando carregamento');
        setIsLoading(false);
      }
    };

    loadCriteria();
  }, []);

  const normalizeName = (name: string) => {
    const cleaned = name
      .replace(/target/gi, '')
      .replace(/weight/gi, '')
      .replace(/_/g, ' ')
      .trim();

    if (!cleaned) {
      return 'Criteria';
    }

    return cleaned
      .split(/\s+/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Calcular soma dos pesos (apenas os que não são target)
  const totalWeight = criteria
    .filter(c => !c.criteria_name.toLowerCase().includes('target'))
    .reduce((sum, c) => sum + c.criteria_weight, 0);
  const isValidWeight = Math.abs(totalWeight - 1.0) < 0.01;

  console.log('🔢 Estado atual - criteria:', criteria);
  console.log('🔢 Total weight:', totalWeight, 'Valid:', isValidWeight);

  const clamp = (value: number, min: number, max: number) => {
    if (Number.isNaN(value)) {
      return min;
    }
    return Math.min(max, Math.max(min, value));
  };

  const displayCriteria: CriteriaDisplayItem[] = criteria.map((item) => {
    let baseLabel = normalizeName(item.criteria_name);
    // Ajuste dos nomes conforme solicitado
    if (/quality of pickup/i.test(baseLabel)) baseLabel = 'Pickup';
    if (/quality pack/i.test(baseLabel)) baseLabel = 'Package';
    const isTarget = item.criteria_name.toLowerCase().includes('target');

    return {
      key: `${item.criteria_id}`,
      label: baseLabel,
      value: isTarget ? item.criteria_target : item.criteria_weight,
      min: 0,
      max: isTarget ? 10 : 1,
      step: isTarget ? 0.1 : 0.01,
      precision: isTarget ? 1 : 2,
      type: isTarget ? 'target' : 'weight',
      onChange: (value: number) => {
        const clamped = clamp(value, 0, isTarget ? 10 : 1);
        setCriteria(prev => prev.map(c => 
          c.criteria_id === item.criteria_id 
            ? (isTarget 
                ? { ...c, criteria_target: clamped }
                : { ...c, criteria_weight: clamped })
            : c
        ));
        setHasChanges(true);
      },
    };
  });

  console.log('📋 Display criteria gerado:', displayCriteria);
  console.log('📋 Quantidade de itens display:', displayCriteria.length);

  // Auto-ajustar pesos para somar 1.00
  const handleAutoAdjust = () => {
    const weights = criteria.filter(c => !c.criteria_name.toLowerCase().includes('target'));
    const count = weights.length;
    if (count === 0) return;

    const equalWeight = 1.0 / count;
    setCriteria(prev => prev.map(c => 
      c.criteria_name.toLowerCase().includes('target') 
        ? c 
        : { ...c, criteria_weight: equalWeight }
    ));
    setHasChanges(true);
  };

  // Salvar critérios
  const handleSave = async () => {
    if (!isValidWeight) {
      showToast('A soma dos pesos deve ser exatamente 1.00', 'warning');
      return;
    }

    try {
      setIsSaving(true);
      await invoke('update_criteria', { criteria });
      setHasChanges(false);
      showToast('✅ Critérios atualizados com sucesso!', 'success');
    } catch (error) {
      console.error('❌ Erro ao salvar critérios:', error);
      showToast('❌ Erro ao salvar critérios', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="settings-section">
        <div className="criteria-wrapper">
          <div className="criteria-list">
            <div className="criteria-loading">
              <i className="bi bi-arrow-repeat"></i>
              <span>Carregando critérios...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }


  // Ordenação fixa: ORIF, NIL, PICKUP, PACKAGE (pesos), TARGET (abaixo)
  const weightOrder = [
    'otif', // ORIF
    'nil',
    'pick up',
    'package',
  ];
  const targetOrder = [
    'otif',
    'nil',
    'pick up',
    'package',
  ];
  const weights = weightOrder
    .map(name => displayCriteria.find(c => c.label.toLowerCase().includes(name) && c.type === 'weight'))
    .filter(Boolean);
  // Busca os targets na ordem, mas se não encontrar pelo nome, pega todos os do tipo target
  let targets = targetOrder
    .map(name => displayCriteria.find(c => c.label.toLowerCase().includes(name) && c.type === 'target'))
    .filter(Boolean);
  if (targets.length === 0) {
    targets = displayCriteria.filter(c => c.type === 'target');
  }

  // Forçar label 'Target' para todos os targets
  targets = targets.map(t => t && { ...t, label: 'Target' });

  return (
    <div className="settings-section">
      <div className="criteria-wrapper">
        <div className="criteria-summary">
          <div className="criteria-summary-text">
            <span className="criteria-summary-label">Soma Total dos Pesos</span>
            <span className="criteria-summary-helper">ORIF + NIL + Pick Up + Package = 1.00</span>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <div className={`criteria-summary-value ${!isValidWeight ? 'invalid' : ''}`}>
              {totalWeight.toFixed(2)}
            </div>
            <span title="Os pesos de ORIF, NIL, Pick Up e Package devem somar exatamente 1.00" style={{cursor: 'pointer', color: '#f59e0b', fontSize: '1.5rem', display: 'flex', alignItems: 'center'}}>
              <i className="bi bi-info-circle"></i>
            </span>
          </div>
        </div>

        {/* Notas em linha fixa: ORIF, NIL, PICKUP, PACKAGE */}
        <div className="criteria-list">
          {weights.map(item => item && (
            <div
              key={item.key}
              className={`criteria-item ${item.type === 'weight' && !isValidWeight ? 'invalid' : ''}`}
            >
              <div className="criteria-item-header">
                <span className="criteria-item-name">{item.label}</span>
                <span className="criteria-item-value">{item.value.toFixed(item.precision)}</span>
              </div>
              <div className="criteria-item-controls">
                <div className="criteria-slider">
                  <input
                    type="range"
                    min={item.min}
                    max={item.max}
                    step={item.step}
                    value={item.value}
                    onChange={(e) => item.onChange(parseFloat(e.target.value))}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* TARGETS ABAIXO */}
        <div className="criteria-list" style={{marginTop: '0.5rem'}}>
          {targets.map(item => item && (
            <div
              key={item.key}
              className={`criteria-item target-item`}
              style={{ minWidth: '100%', flex: '1 1 100%' }}
            >
              <div className="criteria-item-header">
                <span className="criteria-item-name">{item.label}</span>
                <span className="criteria-item-value">{item.value.toFixed(item.precision)}</span>
              </div>
              <div className="criteria-item-controls">
                <div className="criteria-slider">
                  <input
                    type="range"
                    min={item.min}
                    max={item.max}
                    step={item.step}
                    value={item.value}
                    onChange={(e) => item.onChange(parseFloat(e.target.value))}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="criteria-note">
          <i className="bi bi-info-circle"></i>
          <span>Os valores de Target usam uma escala independente de 0 a 10 pontos.</span>
        </div>

        <div className="criteria-actions">
          <button 
            type="button" 
            className="criteria-btn secondary" 
            onClick={handleAutoAdjust}
            disabled={isSaving}
          >
            <i className="bi bi-magic"></i>
            Auto-ajustar Pesos
          </button>
          <button 
            type="button" 
            className="criteria-btn primary" 
            onClick={handleSave}
            disabled={!hasChanges || isSaving || !isValidWeight}
          >
            <i className="bi bi-save"></i>
            {isSaving ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </div>
      </div>
      
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}

/**
 * Página de Settings.
 * Configurações e preferências do aplicativo com múltiplas abas.
 */
function Settings() {
  const { permissions, isUser } = usePermissions();
  const [activeTab, setActiveTab] = useState<'system' | 'suppliers' | 'criteria' | 'users' | 'lists' | 'log' | 'info'>('system');
  const [autoSave, setAutoSave] = useState<boolean>(() => {
    const saved = localStorage.getItem('autoSave');
    return saved === null || saved === 'true'; // Default: true
  });
  const [allowImportExport, setAllowImportExport] = useState<boolean>(() => {
    const saved = localStorage.getItem('allowImportExport');
    return saved === 'true';
  });
  const [allowSupplierEdit, setAllowSupplierEdit] = useState<boolean>(() => {
    const saved = localStorage.getItem('allowSupplierEdit');
    return saved === 'true';
  });
  const [isSuperAdmin, setIsSuperAdmin] = useState<boolean>(false);

  // Verificar se o usuário é Super Admin
  useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        const privilege = (user.user_privilege || '').toLowerCase();
        setIsSuperAdmin(privilege === 'super admin');
      } catch (error) {
        console.error('❌ Erro ao carregar privilégio do usuário:', error);
        setIsSuperAdmin(false);
      }
    }
  }, []);

  // Listener para mudanças na permissão de editar suppliers
  useEffect(() => {
    const handleSupplierEditChange = () => {
      const newValue = localStorage.getItem('allowSupplierEdit') === 'true';
      setAllowSupplierEdit(newValue);
    };

    window.addEventListener('supplierEditChanged', handleSupplierEditChange);
    return () => window.removeEventListener('supplierEditChanged', handleSupplierEditChange);
  }, []);

  // Salvar preferência de auto-save no localStorage
  const handleAutoSaveToggle = (checked: boolean) => {
    setAutoSave(checked);
    localStorage.setItem('autoSave', checked.toString());
    console.log('💾 Auto Save', checked ? 'ATIVADO' : 'DESATIVADO');
    
    // Disparar evento customizado para sincronizar com outras abas/componentes
    window.dispatchEvent(new CustomEvent('autoSaveChanged', { detail: checked }));
  };

  // Controlar permissão de importar/exportar scores
  const handleImportExportToggle = (checked: boolean) => {
    setAllowImportExport(checked);
    localStorage.setItem('allowImportExport', checked.toString());
    console.log('📊 Import/Export Score', checked ? 'PERMITIDO' : 'BLOQUEADO');
    
    window.dispatchEvent(new CustomEvent('importExportChanged', { detail: checked }));
  };

  // Controlar permissão de editar suppliers
  const handleSupplierEditToggle = (checked: boolean) => {
    setAllowSupplierEdit(checked);
    localStorage.setItem('allowSupplierEdit', checked.toString());
    console.log('✏️ Supplier Edit', checked ? 'PERMITIDO' : 'BLOQUEADO');
    
    window.dispatchEvent(new CustomEvent('supplierEditChanged', { detail: checked }));
  };

  return (
    <div className="settings-page">
      <div className="settings-container">
        {/* Abas Principais */}
        <div className="tabs-main">
          {permissions.canAccessSystemSettings && (
            <button className={`tab-btn ${activeTab === 'system' ? 'active' : ''}`} onClick={() => setActiveTab('system')}>
              <i className="bi bi-gear"></i> System
            </button>
          )}
          {(permissions.canAccessSuppliers || allowSupplierEdit) && (
            <button className={`tab-btn ${activeTab === 'suppliers' ? 'active' : ''}`} onClick={() => setActiveTab('suppliers')}>
              <i className="bi bi-building"></i> Suppliers
            </button>
          )}
          {permissions.canAccessCriteria && (
            <button className={`tab-btn ${activeTab === 'criteria' ? 'active' : ''}`} onClick={() => setActiveTab('criteria')}>
              <i className="bi bi-list-check"></i> Criteria
            </button>
          )}
          {permissions.canAccessUsers && (
            <button className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
              <i className="bi bi-people"></i> Users
            </button>
          )}
          {permissions.canAccessListsSettings && (
            <button className={`tab-btn ${activeTab === 'lists' ? 'active' : ''}`} onClick={() => setActiveTab('lists')}>
              <i className="bi bi-card-list"></i> Lists
            </button>
          )}
          {permissions.canAccessLog && (
            <button className={`tab-btn ${activeTab === 'log' ? 'active' : ''}`} onClick={() => setActiveTab('log')}>
              <i className="bi bi-clock-history"></i> Log
            </button>
          )}
          {permissions.canAccessInfo && (
            <button className={`tab-btn ${activeTab === 'info' ? 'active' : ''}`} onClick={() => setActiveTab('info')}>
              <i className="bi bi-info-circle"></i> Info
            </button>
          )}
        </div>

        {/* Conteúdo das Abas */}
        <div className="tabs-content">
          {/* TAB: SYSTEM */}
          {activeTab === 'system' && permissions.canAccessSystemSettings && (
            <div className="tab-content">
              <div className="settings-section">
                <h3><i className="bi bi-palette"></i> Theme</h3>
                <ThemeSelector />
              </div>

              {!isUser && (
                <>
                  <div className="settings-section">
                    <div className="setting-row">
                      <div className="setting-info">
                        <h3><i className="bi bi-floppy"></i> Auto Save</h3>
                        <p className="section-description">Salvar automaticamente as alterações</p>
                      </div>
                      <label className="switch">
                        <input 
                          type="checkbox" 
                          checked={autoSave}
                          onChange={(e) => handleAutoSaveToggle(e.target.checked)}
                        />
                        <span className="slider"></span>
                      </label>
                    </div>
                  </div>

                  {isSuperAdmin && (
                    <>
                      <div className="settings-section">
                        <div className="setting-row">
                          <div className="setting-info">
                            <h3><i className="bi bi-file-earmark-arrow-up"></i> Import/Export Scores</h3>
                            <p className="section-description">Permitir que usuários Admin importem e exportem formulários de scores</p>
                          </div>
                          <label className="switch">
                            <input 
                              type="checkbox" 
                              checked={allowImportExport}
                              onChange={(e) => handleImportExportToggle(e.target.checked)}
                            />
                            <span className="slider"></span>
                          </label>
                        </div>
                      </div>

                      <div className="settings-section">
                        <div className="setting-row">
                          <div className="setting-info">
                            <h3><i className="bi bi-pencil-square"></i> Supplier Edit</h3>
                            <p className="section-description">Permitir que usuários Admin editem suppliers e vejam o ícone em Settings</p>
                          </div>
                          <label className="switch">
                            <input 
                              type="checkbox" 
                              checked={allowSupplierEdit}
                              onChange={(e) => handleSupplierEditToggle(e.target.checked)}
                            />
                            <span className="slider"></span>
                          </label>
                        </div>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          )}

          {/* TAB: SUPPLIERS */}
          {activeTab === 'suppliers' && (permissions.canAccessSuppliers || allowSupplierEdit) && (
            <div className="tab-content">
              <SupplierManager />
            </div>
          )}

          {/* TAB: CRITERIA */}
          {activeTab === 'criteria' && permissions.canAccessCriteria && (
            <div className="tab-content">
              <CriteriaTab />
            </div>
          )}

          {/* TAB: USERS */}
          {activeTab === 'users' && permissions.canAccessUsers && (
            <div className="tab-content">
              <Users />
            </div>
          )}

          {/* TAB: LISTS */}
          {activeTab === 'lists' && permissions.canAccessListsSettings && (
            <div className="tab-content">
              <Lists />
            </div>
          )}

          {/* TAB: LOG */}
          {activeTab === 'log' && permissions.canAccessLog && (
            <div className="tab-content">
              <LogsTable />
            </div>
          )}

          {/* TAB: INFO */}
          {activeTab === 'info' && permissions.canAccessInfo && (
            <div className="tab-content">
              <div className="settings-section info-compact">
                <h3><i className="bi bi-info-circle"></i> Informações sobre o App</h3>
                
                <div className="info-layout-grid">
                  <div className="info-section-group">
                    <div className="info-section-header">
                      <i className="bi bi-code-slash"></i>
                      <h4>Desenvolvimento</h4>
                    </div>
                    
                    <div className="info-dev-item">
                      <strong>Desenvolvido por:</strong>
                      <p>Rafael Negrão de Souza</p>
                      <a href="mailto:rafael.negrao.souza@cummins.com" className="info-link">
                        <i className="bi bi-envelope"></i> rafael.negrao.souza@cummins.com
                      </a>
                      <span className="info-code">AN62H</span>
                    </div>

                    <div className="info-dev-item">
                      <strong>Autor intelectual:</strong>
                      <p>Cleiton Bianchi dos Santos</p>
                      <a href="mailto:Cleiton.Bianchi.Santos@cummins.com" className="info-link">
                        <i className="bi bi-envelope"></i> Cleiton.Bianchi.Santos@cummins.com
                      </a>
                      <span className="info-code">IV338</span>
                    </div>
                  </div>

                  <div className="info-section-group">
                    <div className="info-section-header">
                      <i className="bi bi-star"></i>
                      <h4>Funcionalidades</h4>
                    </div>
                    <ul className="info-features-list">
                      <li><i className="bi bi-check-circle-fill"></i> Consolidação de notas por período</li>
                      <li><i className="bi bi-check-circle-fill"></i> Gestão completa de fornecedores</li>
                      <li><i className="bi bi-check-circle-fill"></i> Análise de riscos e tendências</li>
                      <li><i className="bi bi-check-circle-fill"></i> Timeline de performance</li>
                      <li><i className="bi bi-check-circle-fill"></i> Controle de permissões de usuários</li>
                      <li><i className="bi bi-check-circle-fill"></i> Geração automática de relatórios</li>
                    </ul>
                  </div>

                  <div className="info-section-group">
                    <div className="info-section-header">
                      <i className="bi bi-cpu"></i>
                      <h4>Tecnologias Utilizadas</h4>
                    </div>
                    <ul className="info-features-list">
                      <li><i className="bi bi-check-circle-fill"></i> React + TypeScript</li>
                      <li><i className="bi bi-check-circle-fill"></i> Tauri (Rust)</li>
                      <li><i className="bi bi-check-circle-fill"></i> SQLite Database</li>
                      <li><i className="bi bi-check-circle-fill"></i> Vite Build Tool</li>
                      <li><i className="bi bi-check-circle-fill"></i> CSS Modules</li>
                    </ul>
                  </div>
                </div>

                <div className="info-grid">
                  <div className="info-card-settings">
                    <i className="bi bi-app"></i>
                    <h4>Sistema</h4>
                    <p>Score App</p>
                  </div>
                  
                  <div className="info-card-settings">
                    <i className="bi bi-tag"></i>
                    <h4>Versão</h4>
                    <p>1.1.5</p>
                  </div>
                  
                  <div className="info-card-settings">
                    <i className="bi bi-calendar"></i>
                    <h4>Data</h4>
                    <p>Out/2025</p>
                  </div>
                  
                  <div className="info-card-settings">
                    <i className="bi bi-building"></i>
                    <h4>Empresa</h4>
                    <p>Cummins</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Settings;
