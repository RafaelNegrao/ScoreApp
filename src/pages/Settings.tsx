import { useState, useEffect } from "react";
import { invoke } from '@tauri-apps/api/tauri';
import 'bootstrap-icons/font/bootstrap-icons.css';
import ThemeSelector from "../components/ThemeSelector";
import SupplierManager from "../components/SupplierManager";
import PrivilegesManager from "../components/PrivilegesManager";
import Users from "./Users";
import Lists from "./Lists";
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
    const baseLabel = normalizeName(item.criteria_name);
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

  return (
    <div className="settings-section">
      <div className="criteria-wrapper">
        <div className="criteria-alert">
          <i className="bi bi-exclamation-triangle-fill"></i>
          <span>Os pesos de NIL, OTIF, Pick Up e Package devem somar exatamente 1.00</span>
        </div>

        <div className="criteria-summary">
          <div className="criteria-summary-text">
            <span className="criteria-summary-label">Soma Total dos Pesos</span>
            <span className="criteria-summary-helper">NIL + OTIF + Pick Up + Package = 1.00</span>
          </div>
          <div className={`criteria-summary-value ${!isValidWeight ? 'invalid' : ''}`}>
            {totalWeight.toFixed(2)}
          </div>
        </div>

        <div className="criteria-list">
          {displayCriteria.map(item => (
            <div
              key={item.key}
              className={`criteria-item ${item.type === 'target' ? 'target-item' : ''} ${item.type === 'weight' && !isValidWeight ? 'invalid' : ''}`}
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

  // Salvar preferência de auto-save no localStorage
  const handleAutoSaveToggle = (checked: boolean) => {
    setAutoSave(checked);
    localStorage.setItem('autoSave', checked.toString());
    console.log('💾 Auto Save', checked ? 'ATIVADO' : 'DESATIVADO');
    
    // Disparar evento customizado para sincronizar com outras abas/componentes
    window.dispatchEvent(new CustomEvent('autoSaveChanged', { detail: checked }));
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
          {permissions.canAccessSuppliers && (
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
                <p className="section-description">Escolha o tema visual do sistema</p>
                <ThemeSelector />
              </div>

              {!isUser && (
                <div className="settings-section">
                  <h3><i className="bi bi-floppy"></i> Auto Save</h3>
                  <p className="section-description">Salvar automaticamente as alterações</p>
                  
                  <div className="switch-container">
                    <label className="switch">
                      <input 
                        type="checkbox" 
                        checked={autoSave}
                        onChange={(e) => handleAutoSaveToggle(e.target.checked)}
                      />
                      <span className="slider"></span>
                    </label>
                    <span className="switch-label">Auto Save {autoSave ? 'habilitado' : 'desabilitado'}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: SUPPLIERS */}
          {activeTab === 'suppliers' && permissions.canAccessSuppliers && (
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
              <div className="settings-section">
                <h3><i className="bi bi-clock-history"></i> System Log</h3>
                <p className="section-description">Histórico de atividades do sistema</p>
                
                <div className="empty-state">
                  <i className="bi bi-inbox"></i>
                  <p>Logs do sistema</p>
                  <small>Em desenvolvimento</small>
                </div>
              </div>
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
                      <i className="bi bi-bullseye"></i>
                      <h4>Objetivo do Sistema</h4>
                    </div>
                    <p className="info-section-text">
                      Sistema para consolidar e gerenciar notas de avaliação dos fornecedores, facilitando decisões estratégicas.
                    </p>
                  </div>

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
                      <li><i className="bi bi-check-circle-fill"></i> Importação/exportação via Excel</li>
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
