import { useState, useEffect } from "react";
import SupplierInfoModal from "../components/SupplierInfoModal";
import { invoke } from '@tauri-apps/api/tauri';
import { Info } from "lucide-react";
import 'bootstrap-icons/font/bootstrap-icons.css';
import "./Score.css";

interface Supplier {
  supplier_id: string;
  vendor_name: string;
  supplier_po?: string;
  business_unit?: string;
  supplier_status?: string;
}

interface SupplierScore {
  record_id?: number;
  supplier_id: string;
  month: number;
  year: number;
  otif_score?: string;
  nil_score?: string;
  pickup_score?: string;
  package_score?: string;
  total_score?: string;
  comments?: string;
}

interface UserPermissions {
  otif: string;
  nil: string;
  pickup: string;
  package: string;
}

/**
 * Componente da aba de Critérios - Apenas informativo
 */
function CriteriaTab() {
  return (
    <div className="criterios-content">
      <div className="criterios-grid">
        {/* OTIF */}
        <div className="criterio-card">
          <div className="criterio-header">
            <i className="bi bi-clock-history"></i>
            <h3>OTIF (On Time In Full)</h3>
          </div>
          <div className="criterio-body">
            <p className="criterio-description">Segue tabela de OTIF. As notas são de 0 a 100%, porém a conversão para adição é multiplicar por 10.</p>
            <div className="criterio-example">
              <strong>Exemplo:</strong> 87% × 10 = 8,7
            </div>
            <div className="criterio-table">
              <div className="table-row header">
                <span>OTIF (%)</span>
                <span>Nota Final</span>
              </div>
              <div className="table-row nota-10">
                <span>100%</span>
                <span>10,0</span>
              </div>
              <div className="table-row nota-9">
                <span>90%</span>
                <span>9,0</span>
              </div>
              <div className="table-row nota-8">
                <span>87%</span>
                <span>8,7</span>
              </div>
              <div className="table-row nota-7">
                <span>75%</span>
                <span>7,5</span>
              </div>
              <div className="table-row nota-5">
                <span>50%</span>
                <span>5,0</span>
              </div>
              <div className="table-row nota-0">
                <span>0%</span>
                <span>0,0</span>
              </div>
            </div>
          </div>
        </div>

        {/* NIL */}
        <div className="criterio-card">
          <div className="criterio-header">
            <i className="bi bi-box-seam"></i>
            <h3>NIL (Non-Invoiced Items)</h3>
          </div>
          <div className="criterio-body">
            <div className="criterio-rules">
              <div className="rule-item nota-10">
                <i className="bi bi-check-circle-fill"></i>
                <span><strong>0 problemas</strong> → Nota 10</span>
              </div>
              <div className="rule-item nota-5">
                <i className="bi bi-exclamation-triangle-fill"></i>
                <span><strong>1 problema</strong> → Nota 5</span>
              </div>
              <div className="rule-item nota-0">
                <i className="bi bi-x-circle-fill"></i>
                <span><strong>Mais de 1 problema</strong> → Nota 0</span>
              </div>
            </div>
          </div>
        </div>

        {/* PICKUP */}
        <div className="criterio-card">
          <div className="criterio-header">
            <i className="bi bi-truck"></i>
            <h3>PICKUP (Quality Pickup)</h3>
          </div>
          <div className="criterio-body">
            <div className="criterio-rules">
              <div className="rule-item nota-10">
                <i className="bi bi-check-circle-fill"></i>
                <span><strong>0 problemas</strong> → Nota 10</span>
              </div>
              <div className="rule-item nota-5">
                <i className="bi bi-exclamation-triangle-fill"></i>
                <span><strong>1 problema</strong> → Nota 5</span>
              </div>
              <div className="rule-item nota-0">
                <i className="bi bi-x-circle-fill"></i>
                <span><strong>Mais de 1 problema</strong> → Nota 0</span>
              </div>
            </div>
          </div>
        </div>

        {/* PACKAGE */}
        <div className="criterio-card">
          <div className="criterio-header">
            <i className="bi bi-box"></i>
            <h3>PACKAGE (Quality Package)</h3>
          </div>
          <div className="criterio-body">
            <div className="criterio-rules">
              <div className="rule-item nota-10">
                <i className="bi bi-check-circle-fill"></i>
                <span><strong>0 problemas</strong> → Nota 10</span>
              </div>
              <div className="rule-item nota-5">
                <i className="bi bi-exclamation-triangle-fill"></i>
                <span><strong>1 problema</strong> → Nota 5</span>
              </div>
              <div className="rule-item nota-0">
                <i className="bi bi-x-circle-fill"></i>
                <span><strong>Mais de 1 problema</strong> → Nota 0</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Página de Score.
 * Exibe e gerencia pontuações e avaliações.
 */
function Score() {
  const [showSupplierInfo, setShowSupplierInfo] = useState<null | Supplier>(null);
  const [activeTab, setActiveTab] = useState<'input' | 'criterios'>('input');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Supplier[]>([]);
  const [selectedSuppliers, setSelectedSuppliers] = useState<Set<string>>(new Set());
  const [selectedSuppliersData, setSelectedSuppliersData] = useState<Map<string, Supplier>>(new Map());
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const [selectedMonth, setSelectedMonth] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [showSelectedModal, setShowSelectedModal] = useState<boolean>(false);
  const [scores, setScores] = useState<Map<string, SupplierScore>>(new Map());
  const [inputValues, setInputValues] = useState<Map<string, any>>(new Map());
  const [permissions, setPermissions] = useState<UserPermissions>({
    otif: 'Não',
    nil: 'Não',
    pickup: 'Não',
    package: 'Não',
  });
  const [autoSave, setAutoSave] = useState<boolean>(() => {
    const saved = localStorage.getItem('autoSave');
    return saved === null || saved === 'true'; // Default: true
  });
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [modifiedRows, setModifiedRows] = useState<Set<string>>(new Set());
  const [criteriaWeights, setCriteriaWeights] = useState({
    otif: 0.25,
    nil: 0.25,
    pickup: 0.25,
    package: 0.25,
  });
  const [showFullScoreModal, setShowFullScoreModal] = useState<boolean>(false);
  const [fullScoreMonth, setFullScoreMonth] = useState<string>('');
  const [fullScoreYear, setFullScoreYear] = useState<string>('');
  const [includeInactive, setIncludeInactive] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [generationMessage, setGenerationMessage] = useState<string>('');

  // Carregar critérios (pesos) do banco de dados
  useEffect(() => {
    const loadCriteria = async () => {
      try {
        const criteria = await invoke<any[]>('get_criteria');
        const weights: any = {};
        
        criteria.forEach((c: any) => {
          const name = c.criteria_name.toLowerCase();
          if (name.includes('otif')) weights.otif = c.criteria_weight;
          else if (name.includes('nil')) weights.nil = c.criteria_weight;
          else if (name.includes('pickup') || name.includes('pick up')) weights.pickup = c.criteria_weight;
          else if (name.includes('package')) weights.package = c.criteria_weight;
        });
        
        setCriteriaWeights(weights);
        console.log('✅ Critérios carregados:', weights);
      } catch (error) {
        console.error('❌ Erro ao carregar critérios:', error);
      }
    };
    
    loadCriteria();
  }, []);

  // Carregar permissões do usuário
  useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      const user = JSON.parse(storedUser);
      if (user.permissions) {
        setPermissions(user.permissions);
      }
    }
  }, []);

  // Salvar preferência de auto-save
  useEffect(() => {
    localStorage.setItem('autoSave', autoSave.toString());
  }, [autoSave]);

  // Sincronizar autoSave quando alterado em Settings
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'autoSave') {
        const newValue = e.newValue === null || e.newValue === 'true';
        setAutoSave(newValue);
        console.log('🔄 Auto Save atualizado de outra aba:', newValue);
      }
    };

    const handleAutoSaveChanged = (e: CustomEvent) => {
      setAutoSave(e.detail);
      console.log('🔄 Auto Save atualizado:', e.detail);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('autoSaveChanged', handleAutoSaveChanged as EventListener);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('autoSaveChanged', handleAutoSaveChanged as EventListener);
    };
  }, []);

  // Carregar scores quando mês/ano ou suppliers mudarem
  useEffect(() => {
    const loadScores = async () => {
      if (selectedSuppliers.size > 0 && selectedMonth && selectedYear) {
        try {
          const supplierIds = Array.from(selectedSuppliers);
          const month = parseInt(selectedMonth);
          const year = parseInt(selectedYear);
          
          console.log('🔍 Frontend - Carregando scores para:', { 
            supplierIds, 
            month, 
            year,
            tipos: {
              supplierIds: typeof supplierIds,
              month: typeof month,
              year: typeof year
            }
          });
          
          const loadedScores = await invoke<SupplierScore[]>('get_supplier_scores', {
            supplierIds,
            month,
            year,
          });

          console.log('📦 Frontend - Scores recebidos do backend:', loadedScores);
          console.log('📦 Frontend - Quantidade de scores:', loadedScores?.length);

          const scoresMap = new Map<string, SupplierScore>();
          const newInputValues = new Map<string, any>();
          
          loadedScores.forEach(score => {
            scoresMap.set(score.supplier_id, score);
            console.log(`📊 Score para ${score.supplier_id}:`, {
              otif: score.otif_score,
              nil: score.nil_score,
              pickup: score.pickup_score,
              package: score.package_score,
              total: score.total_score,
              comments: score.comments
            });
            
            // Inicializa os valores dos inputs
            newInputValues.set(`${score.supplier_id}-otif`, score.otif_score || '');
            newInputValues.set(`${score.supplier_id}-nil`, score.nil_score || '');
            newInputValues.set(`${score.supplier_id}-pickup`, score.pickup_score || '');
            newInputValues.set(`${score.supplier_id}-package`, score.package_score || '');
            newInputValues.set(`${score.supplier_id}-comments`, score.comments || '');
          });
          
          // Calcular total score inicial para cada supplier
          loadedScores.forEach(score => {
            const totalScore = calculateTotalScore(score.supplier_id, newInputValues);
            newInputValues.set(`${score.supplier_id}-total`, totalScore);
          });
          
          setScores(scoresMap);
          setInputValues(newInputValues);
          console.log('✅ Estados atualizados com sucesso!');
        } catch (error) {
          console.error('❌ Erro ao carregar scores:', error);
        }
      }
      // Removido: não limpar dados automaticamente quando condições não são atendidas
      // Isso permite manter o estado ao trocar de abas
    };

    loadScores();
  }, [selectedSuppliers, selectedMonth, selectedYear]);

  // Função para calcular o total score
  const calculateTotalScore = (supplierId: string, values: Map<string, any>) => {
    const otif = parseFloat(values.get(`${supplierId}-otif`) || '0') || 0;
    const nil = parseFloat(values.get(`${supplierId}-nil`) || '0') || 0;
    const pickup = parseFloat(values.get(`${supplierId}-pickup`) || '0') || 0;
    const packageScore = parseFloat(values.get(`${supplierId}-package`) || '0') || 0;
    
    const total = 
      (otif * criteriaWeights.otif) +
      (nil * criteriaWeights.nil) +
      (pickup * criteriaWeights.pickup) +
      (packageScore * criteriaWeights.package);
    
    return total.toFixed(2);
  };

  const handleSearchInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);

    // Se o campo estiver vazio, esconder dropdown
    if (query.trim().length === 0) {
      setShowDropdown(false);
      setSearchResults([]);
      return;
    }

    // Busca instantânea - sem debounce
    try {
      console.log('Buscando fornecedores com query:', query.trim());
      const results = await invoke<Supplier[]>('search_suppliers', { query: query.trim() });
      console.log('Resultados encontrados:', results);
      setSearchResults(results);
      setShowDropdown(true); // Sempre mostrar dropdown quando há texto, mesmo sem resultados
    } catch (error) {
      console.error('Erro ao buscar fornecedores:', error);
      setSearchResults([]);
      setShowDropdown(true); // Mostrar dropdown com mensagem de erro
    }
  };

  const handleSelectSupplier = (supplier: Supplier) => {
    const newSelected = new Set(selectedSuppliers);
    const newData = new Map(selectedSuppliersData);

    if (newSelected.has(supplier.supplier_id)) {
      // Se já está selecionado, remove
      newSelected.delete(supplier.supplier_id);
      newData.delete(supplier.supplier_id);
    } else {
      // Se não está selecionado, adiciona
      newSelected.add(supplier.supplier_id);
      newData.set(supplier.supplier_id, supplier);
    }

    setSelectedSuppliers(newSelected);
    setSelectedSuppliersData(newData);
  };

  const handleRemoveSupplier = (supplierId: string) => {
    const newSelected = new Set(selectedSuppliers);
    newSelected.delete(supplierId);
    setSelectedSuppliers(newSelected);

    const newData = new Map(selectedSuppliersData);
    newData.delete(supplierId);
    setSelectedSuppliersData(newData);
  };

  const getSupplierById = (supplierId: string): Supplier | undefined => {
    return selectedSuppliersData.get(supplierId);
  };

  // Formata o valor para sempre ter uma casa decimal (ex: 5 -> 5.0, 7,2 -> 7.2)
  const formatScoreValue = (value: string): string => {
    if (!value || value.trim() === '') return '';
    
    // Remove vírgulas e substitui por ponto
    const normalized = value.replace(',', '.');
    const numValue = parseFloat(normalized);
    
    if (isNaN(numValue)) return '';
    
    // Garante que está entre 0 e 10
    const clamped = Math.max(0, Math.min(10, numValue));
    
    // Formata com 1 casa decimal
    return clamped.toFixed(1);
  };

  // Verifica se o usuário tem permissão para editar um campo específico
  const canEdit = (field: 'otif' | 'nil' | 'pickup' | 'package'): boolean => {
    const permission = permissions[field];
    return permission === 'Sim' || permission === 'sim' || permission === 'SIM' || permission === '1' || permission === 'true';
  };

  // Função para salvar um score individual
  const saveScore = async (supplierId: string) => {
    if (!selectedMonth || !selectedYear || isSaving) return;
    
    try {
      setIsSaving(true);
      const supplier = getSupplierById(supplierId);
      if (!supplier) return;

      const storedUser = sessionStorage.getItem('user');
      const userName = storedUser ? JSON.parse(storedUser).user_name : 'Unknown';

      const month = parseInt(selectedMonth);
      const year = parseInt(selectedYear);

      const otif = inputValues.get(`${supplierId}-otif`) || null;
      const nil = inputValues.get(`${supplierId}-nil`) || null;
      const pickup = inputValues.get(`${supplierId}-pickup`) || null;
      const packageScore = inputValues.get(`${supplierId}-package`) || null;
      const comments = inputValues.get(`${supplierId}-comments`) || null;
      const totalScore = calculateTotalScore(supplierId, inputValues);

      console.log('💾 Salvando score:', { supplierId, month, year, otif, nil, pickup, packageScore, totalScore, comments });

      await invoke('save_supplier_score', {
        supplierId: supplierId,
        supplierName: supplier.vendor_name,
        month,
        year,
        otifScore: otif,
        nilScore: nil,
        pickupScore: pickup,
        packageScore: packageScore,
        totalScore: totalScore,
        comments,
        userName,
      });

      console.log('✅ Score salvo com sucesso!');
      
      // Remover linha do set de modificadas
      setModifiedRows(prev => {
        const newSet = new Set(prev);
        newSet.delete(supplierId);
        return newSet;
      });
    } catch (error) {
      console.error('❌ Erro ao salvar score:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Função para gerar nota cheia
  const handleGenerateFullScore = async () => {
    if (!fullScoreMonth || !fullScoreYear) {
      setGenerationMessage('Mês e ano devem ser selecionados para gerar notas.');
      return;
    }

    // Validação para não gerar para meses futuros - TEMPORARIAMENTE DESABILITADA
    /*
    const now = new Date();
    const monthInt = parseInt(fullScoreMonth);
    const yearInt = parseInt(fullScoreYear);

    if ((yearInt > now.getFullYear()) || (yearInt === now.getFullYear() && monthInt > now.getMonth() + 1)) {
      setGenerationMessage('❌ Não é possível gerar notas para meses futuros.');
      return;
    }
    */

    setIsGenerating(true);
    setGenerationProgress(0);
    setGenerationMessage('Carregando critérios...');

    try {
      // Carregar critérios
      const criteria = await invoke<any[]>('get_criteria');
      const criteriaMap: any = {};
      
      criteria.forEach((crit: any) => {
        const name = crit.criteria_name.toLowerCase();
        if (name.includes('package')) {
          criteriaMap.package = crit.criteria_weight;
        } else if (name.includes('pick')) {
          criteriaMap.pickup = crit.criteria_weight;
        } else if (name.includes('nil')) {
          criteriaMap.nil = crit.criteria_weight;
        } else if (name.includes('otif')) {
          criteriaMap.otif = crit.criteria_weight;
        }
      });

      if (!criteriaMap.package || !criteriaMap.pickup || !criteriaMap.nil || !criteriaMap.otif) {
        setGenerationMessage('Um ou mais critérios de pontuação estão faltando.');
        setIsGenerating(false);
        return;
      }

      setGenerationMessage('Carregando fornecedores...');

      // Carregar TODOS os fornecedores da tabela por status
      const suppliers = await invoke<Supplier[]>('get_all_suppliers_by_status', { 
        includeInactive: includeInactive
      });

      if (suppliers.length === 0) {
        setGenerationMessage('Nenhum fornecedor encontrado no banco de dados.');
        setIsGenerating(false);
        return;
      }

      console.log(`Total de fornecedores carregados: ${suppliers.length}`);

      setGenerationProgress(0);
      setGenerationMessage('Gerando notas...');

      const storedUser = sessionStorage.getItem('user');
      const userName = storedUser ? JSON.parse(storedUser).user_name : 'System';

      let added = 0;
      let ignored = 0;

      const notaFixa = 10.0;
      const month = parseInt(fullScoreMonth);
      const year = parseInt(fullScoreYear);

      // Processar em lotes para não travar a interface
      const batchSize = 10;
      const totalBatches = Math.ceil(suppliers.length / batchSize);

      for (let batchIndex = 0; batchIndex < totalBatches; batchIndex++) {
        const startIdx = batchIndex * batchSize;
        const endIdx = Math.min(startIdx + batchSize, suppliers.length);
        const batch = suppliers.slice(startIdx, endIdx);

        // Processar batch em paralelo
        const promises = batch.map(async (supplier) => {
          // Calcular total
          const total = (
            notaFixa * criteriaMap.otif +
            notaFixa * criteriaMap.nil +
            notaFixa * criteriaMap.package +
            notaFixa * criteriaMap.pickup
          );

          try {
            const result = await invoke<string>('save_supplier_score', {
              supplierId: supplier.supplier_id,
              supplierName: supplier.vendor_name,
              month,
              year,
              otifScore: notaFixa.toString(),
              nilScore: notaFixa.toString(),
              pickupScore: notaFixa.toString(),
              packageScore: notaFixa.toString(),
              totalScore: total.toFixed(2),
              comments: 'Maximum score auto-generated.',
              userName
            });

            // Verifica se foi ignorado ou inserido
            if (result.includes('ignorado') || result.includes('já existe')) {
              ignored++;
            } else {
              added++;
            }
          } catch (error) {
            console.error(`Erro ao salvar score para ${supplier.supplier_id}:`, error);
          }
        });

        // Aguardar batch completar
        await Promise.all(promises);

        // Atualizar progresso de 0 a 100%
        const progress = ((endIdx) / suppliers.length) * 100;
        setGenerationProgress(progress);
        setGenerationMessage(`Gerando notas... ${endIdx} de ${suppliers.length}`);

        // Pequeno delay para não travar a UI
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      setGenerationProgress(100);
      setGenerationMessage(
        `Geração de notas concluída!\n\n` +
        `Inseridos: ${added}\n` +
        `Ignorados: ${ignored}\n` +
        `Total processado: ${suppliers.length}`
      );

    } catch (error) {
      console.error('Erro ao gerar notas cheias:', error);
      setGenerationMessage(`Erro durante a geração: ${error}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.search-input-wrapper')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // DEBUG: Monitorar quando o modal é aberto
  useEffect(() => {
    if (showSelectedModal) {
      console.log('🔴 Modal de fornecedores selecionados foi ABERTO');
      console.trace('Stack trace de quem abriu o modal:');
    }
  }, [showSelectedModal]);

  return (
    <div className="score-page">
      {/* Tabs de navegação */}
      <div className="score-tabs">
        <button 
          className={`score-tab ${activeTab === 'input' ? 'active' : ''}`}
          onClick={() => setActiveTab('input')}
        >
          <i className="bi bi-search"></i>
          <span>Pesquisa</span>
        </button>
        <button 
          className={`score-tab ${activeTab === 'criterios' ? 'active' : ''}`}
          onClick={() => setActiveTab('criterios')}
        >
          <i className="bi bi-list-check"></i>
          <span>Critérios</span>
        </button>
      </div>

      {/* Conteúdo das abas */}
      <div className="score-content">
        {/* Aba Input/Pesquisa */}
        <div className="tab-panel" style={{ display: activeTab === 'input' ? 'flex' : 'none' }}>
          <>
            <div className="search-section">
              <div className="search-bar-container">
                <div className="search-input-wrapper">
                  <input 
                    type="text" 
                    className="search-input" 
                    placeholder="Buscar por Nome, ID, PO ou BU..."
                    value={searchQuery}
                    onChange={handleSearchInput}
                    onFocus={() => searchQuery.trim().length > 0 && setShowDropdown(true)}
                  />
                  
                  {selectedSuppliers.size > 0 && (
                    <button 
                      type="button" 
                      className="selected-badge"
                      onClick={() => setShowSelectedModal(true)}
                    >
                      <i className="bi bi-check2-circle"></i>
                      <span className="selected-count">{selectedSuppliers.size}</span>
                    </button>
                  )}

                  {showDropdown && (
                    <div className="search-dropdown show">
                      {searchResults.length > 0 ? (
                        searchResults.map((supplier) => {
                          const isSelected = selectedSuppliers.has(supplier.supplier_id);

                          return (
                            <div 
                              key={supplier.supplier_id}
                              className="dropdown-item"
                              onClick={() => handleSelectSupplier(supplier)}
                            >
                              <div className="dropdown-checkbox">
                                {isSelected ? (
                                  <i className="bi bi-check-circle-fill" style={{ color: '#10b981', fontSize: 20 }}></i>
                                ) : (
                                  <i className="bi bi-circle" style={{ color: 'var(--border-color)', fontSize: 20 }}></i>
                                )}
                              </div>
                              <div className="dropdown-item-content">
                                <div className="dropdown-item-line1">
                                  <strong>{supplier.vendor_name}</strong>
                                </div>
                                <div className="dropdown-item-line2">
                                  <span className="dropdown-detail-item">
                                    <span className="dropdown-detail-label">ID:</span> {supplier.supplier_id || '—'}
                                  </span>
                                  <span className="dropdown-detail-separator">•</span>
                                  <span className="dropdown-detail-item">
                                    <span className="dropdown-detail-label">PO:</span> {supplier.supplier_po || '—'}
                                  </span>
                                  <span className="dropdown-detail-separator">•</span>
                                  <span className="dropdown-detail-item">
                                    <span className="dropdown-detail-label">BU:</span> {supplier.business_unit || '—'}
                                  </span>
                                </div>
                              </div>
                              {supplier.supplier_status && (
                                <div className={`status-indicator ${supplier.supplier_status.toLowerCase()}`}>
                                  <i className="bi bi-circle-fill"></i>
                                </div>
                              )}
                            </div>
                          );
                        })
                      ) : (
                        <div className="dropdown-item no-results">
                          <div className="dropdown-item-main">
                            <i className="bi bi-search" style={{ marginRight: '8px', opacity: 0.5 }}></i>
                            <span style={{ color: 'var(--text-secondary)' }}>Nenhum fornecedor encontrado</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                <div className="search-filters">
                  <div className="custom-select-wrapper">
                    <select 
                      className="filter-select"
                      value={selectedMonth}
                      onChange={(e) => setSelectedMonth(e.target.value)}
                      required
                    >
                      <option value="">Mês</option>
                      <option value="1">Janeiro</option>
                      <option value="2">Fevereiro</option>
                      <option value="3">Março</option>
                      <option value="4">Abril</option>
                      <option value="5">Maio</option>
                      <option value="6">Junho</option>
                      <option value="7">Julho</option>
                      <option value="8">Agosto</option>
                      <option value="9">Setembro</option>
                      <option value="10">Outubro</option>
                      <option value="11">Novembro</option>
                      <option value="12">Dezembro</option>
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>
                  <div className="custom-select-wrapper">
                    <select 
                      className="filter-select"
                      value={selectedYear}
                      onChange={(e) => setSelectedYear(e.target.value)}
                      required
                    >
                      <option value="">Ano</option>
                      {Array.from({ length: 6 }, (_, i) => new Date().getFullYear() + i).map((year) => (
                        <option key={year} value={year.toString()}>{year}</option>
                      ))}
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>
                  
                  {/* Botão para gerar nota cheia */}
                  <button 
                    className="more-options-btn"
                    onClick={() => setShowFullScoreModal(true)}
                    title="Mais opções"
                  >
                    <i className="bi bi-gear"></i>
                  </button>
                </div>
              </div>

              {selectedSuppliers.size === 0 && searchQuery.trim().length === 0 ? (
                <div className="empty-state">
                  <i className="bi bi-search"></i>
                  <p>Pesquise por fornecedores</p>
                  <small>Use os filtros acima para buscar</small>
                </div>
              ) : null}

              {/* Tabela de fornecedores selecionados */}
              {selectedSuppliers.size > 0 && (
                <div className="suppliers-table-section">
                  {!selectedMonth || !selectedYear ? (
                    <div className="info-message">
                      <i className="bi bi-info-circle"></i>
                      <p>Selecione o mês e o ano para carregar as notas salvas</p>
                    </div>
                  ) : null}
                  <div className="table-container">
                    <table className="suppliers-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Supplier ID</th>
                          <th>PO</th>
                          <th>BU</th>
                          <th>Supplier Name</th>
                          <th>OTIF</th>
                          <th>NIL</th>
                          <th>Pickup</th>
                          <th>Package</th>
                          <th>Total</th>
                          <th>Comments</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Array.from(selectedSuppliers).map((supplierId, index) => {
                          const supplier = getSupplierById(supplierId);
                          if (!supplier) return null;
                          
                          const score = scores.get(supplierId);
                          
                          return (
                            <tr key={`${supplierId}-${selectedMonth}-${selectedYear}`}>
                              <td>{index + 1}</td>
                              <td>{supplier.supplier_id}</td>
                              <td>{supplier.supplier_po || '—'}</td>
                              <td>{supplier.business_unit || '—'}</td>
                              <td className="supplier-name-cell">{supplier.vendor_name}</td>
                              <td>
                                <input 
                                  type="number" 
                                  className={`score-input ${!canEdit('otif') || !selectedMonth || !selectedYear ? 'readonly' : ''}`}
                                  min="0" 
                                  max="10" 
                                  step="0.1"

                                  value={inputValues.get(`${supplierId}-otif`) || ''}
                                  readOnly={!canEdit('otif') || !selectedMonth || !selectedYear}
                                  disabled={!canEdit('otif') || !selectedMonth || !selectedYear}
                                  onChange={(e) => {
                                    if (!canEdit('otif') || !selectedMonth || !selectedYear) return;
                                    let value = e.target.value;
                                    const numValue = parseFloat(value);
                                    if (numValue > 10) value = '10';
                                    if (numValue < 0) value = '0';
                                    const newValues = new Map(inputValues);
                                    newValues.set(`${supplierId}-otif`, value);
                                    
                                    // Calcular e atualizar o total score em tempo real
                                    const totalScore = calculateTotalScore(supplierId, newValues);
                                    newValues.set(`${supplierId}-total`, totalScore);
                                    
                                    // Marcar linha como modificada
                                    setModifiedRows(prev => new Set(prev).add(supplierId));
                                    
                                    setInputValues(newValues);
                                  }}
                                  onBlur={(e) => {
                                    if (!canEdit('otif') || !selectedMonth || !selectedYear) return;
                                    const formatted = formatScoreValue(e.target.value);
                                    if (formatted !== '') {
                                      const newValues = new Map(inputValues);
                                      newValues.set(`${supplierId}-otif`, formatted);
                                      setInputValues(newValues);
                                    }
                                    if (autoSave) {
                                      saveScore(supplierId);
                                    }
                                  }}
                                />
                              </td>
                              <td>
                                <input 
                                  type="number" 
                                  className={`score-input ${!canEdit('nil') || !selectedMonth || !selectedYear ? 'readonly' : ''}`}
                                  min="0" 
                                  max="10" 
                                  step="0.1"

                                  value={inputValues.get(`${supplierId}-nil`) || ''}
                                  readOnly={!canEdit('nil') || !selectedMonth || !selectedYear}
                                  disabled={!canEdit('nil') || !selectedMonth || !selectedYear}
                                  onChange={(e) => {
                                    if (!canEdit('nil') || !selectedMonth || !selectedYear) return;
                                    let value = e.target.value;
                                    const numValue = parseFloat(value);
                                    if (numValue > 10) value = '10';
                                    if (numValue < 0) value = '0';
                                    const newValues = new Map(inputValues);
                                    newValues.set(`${supplierId}-nil`, value);
                                    
                                    // Calcular e atualizar o total score em tempo real
                                    const totalScore = calculateTotalScore(supplierId, newValues);
                                    newValues.set(`${supplierId}-total`, totalScore);
                                    
                                    // Marcar linha como modificada
                                    setModifiedRows(prev => new Set(prev).add(supplierId));
                                    
                                    setInputValues(newValues);
                                  }}
                                  onBlur={(e) => {
                                    if (!canEdit('nil') || !selectedMonth || !selectedYear) return;
                                    const formatted = formatScoreValue(e.target.value);
                                    if (formatted !== '') {
                                      const newValues = new Map(inputValues);
                                      newValues.set(`${supplierId}-nil`, formatted);
                                      setInputValues(newValues);
                                    }
                                    if (autoSave) {
                                      saveScore(supplierId);
                                    }
                                  }}
                                />
                              </td>
                              <td>
                                <input 
                                  type="number" 
                                  className={`score-input ${!canEdit('pickup') || !selectedMonth || !selectedYear ? 'readonly' : ''}`}
                                  min="0" 
                                  max="10" 
                                  step="0.1"

                                  value={inputValues.get(`${supplierId}-pickup`) || ''}
                                  readOnly={!canEdit('pickup') || !selectedMonth || !selectedYear}
                                  disabled={!canEdit('pickup') || !selectedMonth || !selectedYear}
                                  onChange={(e) => {
                                    if (!canEdit('pickup') || !selectedMonth || !selectedYear) return;
                                    let value = e.target.value;
                                    const numValue = parseFloat(value);
                                    if (numValue > 10) value = '10';
                                    if (numValue < 0) value = '0';
                                    const newValues = new Map(inputValues);
                                    newValues.set(`${supplierId}-pickup`, value);
                                    
                                    // Calcular e atualizar o total score em tempo real
                                    const totalScore = calculateTotalScore(supplierId, newValues);
                                    newValues.set(`${supplierId}-total`, totalScore);
                                    
                                    // Marcar linha como modificada
                                    setModifiedRows(prev => new Set(prev).add(supplierId));
                                    
                                    setInputValues(newValues);
                                  }}
                                  onBlur={(e) => {
                                    if (!canEdit('pickup') || !selectedMonth || !selectedYear) return;
                                    const formatted = formatScoreValue(e.target.value);
                                    if (formatted !== '') {
                                      const newValues = new Map(inputValues);
                                      newValues.set(`${supplierId}-pickup`, formatted);
                                      setInputValues(newValues);
                                    }
                                    if (autoSave) {
                                      saveScore(supplierId);
                                    }
                                  }}
                                />
                              </td>
                              <td>
                                <input 
                                  type="number" 
                                  className={`score-input ${!canEdit('package') || !selectedMonth || !selectedYear ? 'readonly' : ''}`}
                                  min="0" 
                                  max="10" 
                                  step="0.1"

                                  value={inputValues.get(`${supplierId}-package`) || ''}
                                  readOnly={!canEdit('package') || !selectedMonth || !selectedYear}
                                  disabled={!canEdit('package') || !selectedMonth || !selectedYear}
                                  onChange={(e) => {
                                    if (!canEdit('package') || !selectedMonth || !selectedYear) return;
                                    let value = e.target.value;
                                    const numValue = parseFloat(value);
                                    if (numValue > 10) value = '10';
                                    if (numValue < 0) value = '0';
                                    const newValues = new Map(inputValues);
                                    newValues.set(`${supplierId}-package`, value);
                                    
                                    // Calcular e atualizar o total score em tempo real
                                    const totalScore = calculateTotalScore(supplierId, newValues);
                                    newValues.set(`${supplierId}-total`, totalScore);
                                    
                                    // Marcar linha como modificada
                                    setModifiedRows(prev => new Set(prev).add(supplierId));
                                    
                                    setInputValues(newValues);
                                  }}
                                  onBlur={(e) => {
                                    if (!canEdit('package') || !selectedMonth || !selectedYear) return;
                                    const formatted = formatScoreValue(e.target.value);
                                    if (formatted !== '') {
                                      const newValues = new Map(inputValues);
                                      newValues.set(`${supplierId}-package`, formatted);
                                      setInputValues(newValues);
                                    }
                                    if (autoSave) {
                                      saveScore(supplierId);
                                    }
                                  }}
                                />
                              </td>
                              <td className="total-cell">
                                <span className="total-score">
                                  {inputValues.get(`${supplierId}-total`) || calculateTotalScore(supplierId, inputValues)}
                                </span>
                              </td>
                              <td>
                                <input 
                                  type="text" 
                                  className="comment-input" 
                                  placeholder="Comentário..."
                                  value={inputValues.get(`${supplierId}-comments`) || ''}
                                  readOnly={!selectedMonth || !selectedYear}
                                  disabled={!selectedMonth || !selectedYear}
                                  onChange={(e) => {
                                    if (!selectedMonth || !selectedYear) return;
                                    const newValues = new Map(inputValues);
                                    newValues.set(`${supplierId}-comments`, e.target.value);
                                    
                                    // Marcar linha como modificada
                                    setModifiedRows(prev => new Set(prev).add(supplierId));
                                    
                                    setInputValues(newValues);
                                  }}
                                  onBlur={() => {
                                    if (!selectedMonth || !selectedYear) return;
                                    if (autoSave) {
                                      saveScore(supplierId);
                                    }
                                  }}
                                />
                              </td>
                              <td>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  {/* Ícone de info */}
                                  <button 
                                    className="action-btn info-btn"
                                    style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
                                    title="Informações do fornecedor"
                                    onClick={e => { e.stopPropagation(); setShowSupplierInfo(supplier); }}
                                  >
                                    <Info size={16} color="var(--accent-primary)" />
                                  </button>
                                  {/* Ícone de modificado */}
                                  {modifiedRows.has(supplierId) && (
                                    <i 
                                      className="bi bi-pencil-fill" 
                                      style={{ color: '#f39c12', fontSize: '16px' }}
                                      title="Modificado - não salvo"
                                    ></i>
                                  )}
                                  {/* Botão Salvar - apenas quando auto-save está desativado */}
                                  {!autoSave && (
                                    <button 
                                      className="action-btn save-btn"
                                      onClick={() => saveScore(supplierId)}
                                      disabled={isSaving || !selectedMonth || !selectedYear}
                                      title={!selectedMonth || !selectedYear ? "Selecione mês e ano" : "Salvar"}
                                    >
                                      <i className="bi bi-save"></i>
                                    </button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Modal de fornecedores selecionados */}
            {showSelectedModal && (
              <div className="selected-modal-overlay" onClick={() => setShowSelectedModal(false)}>
                <div className="selected-modal" onClick={(e) => e.stopPropagation()}>
                  <div className="selected-modal-header">
                    <h3>Fornecedores Selecionados ({selectedSuppliers.size})</h3>
                    <button className="modal-close" onClick={() => setShowSelectedModal(false)}>
                      <i className="bi bi-x-lg"></i>
                    </button>
                  </div>
                  <div className="selected-modal-content">
                    {selectedSuppliers.size > 0 ? (
                      Array.from(selectedSuppliers).map((supplierId) => {
                        const supplier = getSupplierById(supplierId);
                        return supplier ? (
                          <div key={supplierId} className="supplier-card-modal">
                            <div className="supplier-card-main">
                              <div className="supplier-card-header">
                                <h4>{supplier.vendor_name}</h4>
                                {supplier.supplier_status && (
                                  <span className={`status-badge ${supplier.supplier_status.toLowerCase()}`}>
                                    {supplier.supplier_status}
                                  </span>
                                )}
                              </div>
                              <div className="supplier-card-details">
                                <div className="detail-item">
                                  <i className="bi bi-hash"></i>
                                  <span className="detail-label">ID:</span>
                                  <span className="detail-value">{supplier.supplier_id || '—'}</span>
                                </div>
                                <div className="detail-item">
                                  <i className="bi bi-file-text"></i>
                                  <span className="detail-label">PO:</span>
                                  <span className="detail-value">{supplier.supplier_po || '—'}</span>
                                </div>
                                <div className="detail-item">
                                  <i className="bi bi-building"></i>
                                  <span className="detail-label">BU:</span>
                                  <span className="detail-value">{supplier.business_unit || '—'}</span>
                                </div>
                              </div>
                            </div>
                            <button 
                              type="button" 
                              className="supplier-card-remove"
                              onClick={() => handleRemoveSupplier(supplierId)}
                              title="Remover fornecedor"
                            >
                              <i className="bi bi-trash"></i>
                            </button>
                          </div>
                        ) : null;
                      })
                    ) : (
                      <div className="empty-state-modal">
                        <i className="bi bi-inbox" style={{ fontSize: '48px', color: 'var(--text-secondary)', marginBottom: '16px' }}></i>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '16px' }}>Nenhum fornecedor selecionado</p>
                        <small style={{ color: 'var(--text-tertiary)', fontSize: '14px' }}>Use a busca acima para adicionar fornecedores</small>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        </div>

        {/* Aba Critérios */}
        <div className="tab-panel" style={{ display: activeTab === 'criterios' ? 'flex' : 'none' }}>
          <CriteriaTab />
        </div>
      </div>

      {/* Modal de informações do fornecedor */}
      {showSupplierInfo && (
        <SupplierInfoModal
          isOpen={true}
          supplier={showSupplierInfo}
          onClose={() => setShowSupplierInfo(null)}
        />
      )}

      {/* Modal Gerar Nota Cheia */}
      {showFullScoreModal && (
        <>
          <div className="modal-overlay" onClick={() => !isGenerating && setShowFullScoreModal(false)} />
          <div className="full-score-modal">
            <div className="full-score-header">
              <h2>Gerar Nota Cheia</h2>
              <button 
                className="close-modal-btn"
                onClick={() => !isGenerating && setShowFullScoreModal(false)}
                disabled={isGenerating}
              >
                <i className="bi bi-x"></i>
              </button>
            </div>
            
            <div className="full-score-content">
              <p className="full-score-description">
                Selecione o mês e ano para gerar notas máximas para todos os fornecedores ativos:
              </p>

              <div className="full-score-selects">
                <div className="full-score-select-wrapper">
                  <label>Mês</label>
                  <select 
                    value={fullScoreMonth}
                    onChange={(e) => setFullScoreMonth(e.target.value)}
                    disabled={isGenerating}
                    required
                  >
                    <option value="">Selecione</option>
                    <option value="1">Janeiro</option>
                    <option value="2">Fevereiro</option>
                    <option value="3">Março</option>
                    <option value="4">Abril</option>
                    <option value="5">Maio</option>
                    <option value="6">Junho</option>
                    <option value="7">Julho</option>
                    <option value="8">Agosto</option>
                    <option value="9">Setembro</option>
                    <option value="10">Outubro</option>
                    <option value="11">Novembro</option>
                    <option value="12">Dezembro</option>
                  </select>
                </div>

                <div className="full-score-select-wrapper">
                  <label>Ano</label>
                  <select 
                    value={fullScoreYear}
                    onChange={(e) => setFullScoreYear(e.target.value)}
                    disabled={isGenerating}
                    required
                  >
                    <option value="">Selecione</option>
                    <option value="2024">2024</option>
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                    <option value="2027">2027</option>
                    <option value="2028">2028</option>
                    <option value="2029">2029</option>
                    <option value="2030">2030</option>
                  </select>
                </div>
              </div>

              <div className="full-score-switch">
                <label className="switch-container">
                  <input 
                    type="checkbox"
                    checked={includeInactive}
                    onChange={(e) => setIncludeInactive(e.target.checked)}
                    disabled={isGenerating}
                  />
                  <span className="switch-slider"></span>
                </label>
                <span className="switch-label">Gerar score também para Inactives</span>
              </div>

              {generationMessage && (
                <div className="generation-status">
                  <div className={`generation-message-container ${!isGenerating ? 'complete' : ''}`}>
                    {!isGenerating ? (
                      <i className="bi bi-check-circle-fill" style={{ color: 'var(--accent-primary)', fontSize: '20px' }}></i>
                    ) : generationProgress === 0 ? (
                      <i className="bi bi-arrow-repeat spinning-icon" style={{ color: 'var(--accent-primary)', fontSize: '20px' }}></i>
                    ) : (
                      <i className="bi bi-hourglass-split" style={{ color: 'var(--accent-primary)', fontSize: '20px' }}></i>
                    )}
                    <p className="generation-message">{generationMessage}</p>
                  </div>
                  {isGenerating && generationProgress > 0 && (
                    <div className="progress-bar-container">
                      <div 
                        className="progress-bar-fill" 
                        style={{ width: `${generationProgress}%` }}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="full-score-footer">
              <button 
                className="btn-cancel"
                onClick={() => setShowFullScoreModal(false)}
                disabled={isGenerating}
              >
                {isGenerating ? 'Cancelar' : 'Fechar'}
              </button>
              <button 
                className="btn-generate"
                onClick={handleGenerateFullScore}
                disabled={isGenerating || !fullScoreMonth || !fullScoreYear}
              >
                Gerar
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Score;
