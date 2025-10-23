import { useState, useEffect, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { useToastContext } from '../contexts/ToastContext';
import SupplierEditModal from './SupplierEditModal';
import './SupplierManager.css';

interface Supplier {
  supplier_id: string;
  vendor_name: string;
  supplier_po?: string;
  bu?: string;
  supplier_email?: string;
  supplier_status?: string;
  planner?: string;
  country?: string;
  supplier_category?: string;
  continuity?: string;
  sourcing?: string;
  sqie?: string;
  ssid?: string;
  otif_target?: string;
  nil_target?: string;
  pickup_target?: string;
  package_target?: string;
  otif_score?: string;
  nil_score?: string;
  pickup_score?: string;
  package_score?: string;
  total_score?: string;
}

interface SupplierUpdate {
  supplier_id: string;
  supplier_name: string;
  supplier_po?: string;
  bu?: string;
  supplier_email?: string;
  supplier_status?: string;
  planner?: string;
  country?: string;
  supplier_category?: string;
  continuity?: string;
  sourcing?: string;
  sqie?: string;
  ssid?: string;
  otif_target?: string;
  nil_target?: string;
  pickup_target?: string;
  package_target?: string;
}

function SupplierManager() {
  const [searchQuery, setSearchQuery] = useState('');
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const { showToast } = useToastContext();

  // Estados para dropdowns
  const [planners, setPlanners] = useState<string[]>([]);
  const [continuityOptions, setContinuityOptions] = useState<string[]>([]);
  const [sourcingOptions, setSourcingOptions] = useState<string[]>([]);
  const [sqieOptions, setSqieOptions] = useState<string[]>([]);
  const [businessUnits, setBusinessUnits] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);

  // Formulário de edição
  const [formData, setFormData] = useState<SupplierUpdate>({
    supplier_id: '',
    supplier_name: '',
    supplier_po: '',
    bu: '',
    supplier_email: '',
    supplier_status: '',
    planner: '',
    country: '',
    supplier_category: '',
    continuity: '',
    sourcing: '',
    sqie: '',
    ssid: '',
    otif_target: '',
    nil_target: '',
    pickup_target: '',
    package_target: '',
  });

  // Carregar opções dos dropdowns ao montar o componente
  useEffect(() => {
    const loadDropdownOptions = async () => {
      try {
        const [plannersData, continuityData, sourcingData, sqieData] = await Promise.all([
          invoke<string[]>('get_planners'),
          invoke<string[]>('get_continuity_options'),
          invoke<string[]>('get_sourcing_options'),
          invoke<string[]>('get_sqie_options'),
        ]);
        
        setPlanners(plannersData);
        setContinuityOptions(continuityData);
        setSourcingOptions(sourcingData);
        setSqieOptions(sqieData);
      } catch (error) {
        console.error('Erro ao carregar opções dos dropdowns:', error);
      }

      // Carregar BU e Categoria
      try {
        const businessUnitsData = await invoke<string[]>('get_business_units');
        setBusinessUnits(businessUnitsData);
      } catch (error) {
        console.error('Erro ao carregar BU:', error);
      }

      try {
        const categoriesData = await invoke<string[]>('get_categories');
        setCategories(categoriesData);
      } catch (error) {
        console.error('Erro ao carregar Categorias:', error);
      }
    };

    loadDropdownOptions();
  }, []);

  // Buscar fornecedores quando o usuário digita
  useEffect(() => {
    const searchTimeout = setTimeout(async () => {
      if (searchQuery.trim().length >= 1) {
        await handleSearch();
      } else if (searchQuery.trim().length === 0) {
        setSuppliers([]);
      }
    }, 300);

    return () => clearTimeout(searchTimeout);
  }, [searchQuery]);

  const handleSearch = async () => {
    try {
      setIsSearching(true);
      console.log('🔍 Buscando por:', searchQuery);
      const results = await invoke<Supplier[]>('search_suppliers_data', {
        query: searchQuery,
      });
      console.log('📦 Resultados recebidos:', results);
      setSuppliers(results);
    } catch (error) {
      console.error('❌ Erro ao buscar fornecedores:', error);
      showToast('Erro ao buscar fornecedores', 'error');
      setSuppliers([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectSupplier = async (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setFormData({
      supplier_id: supplier.supplier_id,
      supplier_name: supplier.vendor_name,
      supplier_po: supplier.supplier_po || '',
      bu: supplier.bu || '',
      supplier_email: supplier.supplier_email || '',
      supplier_status: supplier.supplier_status || '',
      planner: supplier.planner || '',
      country: supplier.country || '',
      supplier_category: supplier.supplier_category || '',
      continuity: supplier.continuity || '',
      sourcing: supplier.sourcing || '',
      sqie: supplier.sqie || '',
      ssid: supplier.ssid || '',
      otif_target: supplier.otif_target || '',
      nil_target: supplier.nil_target || '',
      pickup_target: supplier.pickup_target || '',
      package_target: supplier.package_target || '',
    });
  };

  const handleEditSupplier = (supplier: Supplier) => {
    handleSelectSupplier(supplier);
    setIsEditing(true);
  };

  const handleInputChange = (field: keyof SupplierUpdate, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleFieldChange = (supplier: Supplier, field: keyof SupplierUpdate, value: string) => {
    // Só seleciona o fornecedor se ainda não estiver selecionado
    if (selectedSupplier?.supplier_id !== supplier.supplier_id) {
      handleSelectSupplier(supplier);
    }
    handleInputChange(field, value);
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      await invoke('update_supplier_data', { supplier: formData });
      showToast('Fornecedor atualizado com sucesso!', 'success');
      
      // Atualiza a lista de fornecedores
      const updatedSupplier = {
        ...selectedSupplier!,
        ...formData,
      };
      setSuppliers(prev =>
        prev.map(s => (s.supplier_id === formData.supplier_id ? updatedSupplier : s))
      );
      setSelectedSupplier(updatedSupplier);
      setIsEditing(false);
    } catch (error) {
      console.error('Erro ao salvar fornecedor:', error);
      showToast('Erro ao salvar fornecedor', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (selectedSupplier) {
      setFormData({
        supplier_id: selectedSupplier.supplier_id,
        supplier_name: selectedSupplier.vendor_name,
        supplier_po: selectedSupplier.supplier_po || '',
        bu: selectedSupplier.bu || '',
        supplier_email: selectedSupplier.supplier_email || '',
        supplier_status: selectedSupplier.supplier_status || '',
        planner: selectedSupplier.planner || '',
        country: selectedSupplier.country || '',
        supplier_category: selectedSupplier.supplier_category || '',
        continuity: selectedSupplier.continuity || '',
        sourcing: selectedSupplier.sourcing || '',
        sqie: selectedSupplier.sqie || '',
        ssid: selectedSupplier.ssid || '',
        otif_target: selectedSupplier.otif_target || '',
        nil_target: selectedSupplier.nil_target || '',
        pickup_target: selectedSupplier.pickup_target || '',
        package_target: selectedSupplier.package_target || '',
      });
    }
    setIsEditing(false);
  };

  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      const containerWidth = scrollContainerRef.current.offsetWidth;
      scrollContainerRef.current.scrollBy({ left: -containerWidth, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      const containerWidth = scrollContainerRef.current.offsetWidth;
      scrollContainerRef.current.scrollBy({ left: containerWidth, behavior: 'smooth' });
    }
  };

  return (
    <div className="supplier-manager">
      {/* Header com Busca */}
      <div className="supplier-header">
        <div className="supplier-search-section">
          <div className="supplier-search-controls">
            <div className="supplier-search-box">
              <i className="bi bi-search"></i>
              <input
                type="text"
                placeholder="Buscar fornecedor..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="supplier-search-input"
              />
              {isSearching && (
                <div className="supplier-search-loading">
                  <i className="bi bi-arrow-repeat spin"></i>
                </div>
              )}
            </div>
            {suppliers.length > 0 && (
              <div className="supplier-count">
                <span className="count-number">{suppliers.length}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Carousel de Fornecedores */}
      {suppliers.length > 0 ? (
        <div className="supplier-carousel-container">
          <button className="carousel-nav carousel-nav-left" onClick={scrollLeft}>
            <i className="bi bi-chevron-left"></i>
          </button>

          <div className="supplier-carousel" ref={scrollContainerRef}>
            {suppliers.map((supplier) => (
              <div
                key={supplier.supplier_id}
                className={`supplier-card ${
                  selectedSupplier?.supplier_id === supplier.supplier_id ? 'selected' : ''
                }`}
              >
                <div className="supplier-card-header">
                  <div className="supplier-card-title">
                    <i className="bi bi-building-fill"></i>
                    <h3 
                      className="supplier-card-name" 
                      title={supplier.vendor_name || 'Sem Nome'}
                    >
                      {supplier.vendor_name || 'Sem Nome'}
                    </h3>
                    <span className="supplier-card-id">#{supplier.supplier_id}</span>
                  </div>
                  <div className="supplier-card-actions-header">
                    <button
                      className="btn-icon-action btn-update"
                      onClick={() => handleEditSupplier(supplier)}
                      title="Atualizar"
                    >
                      <i className="bi bi-pencil-square"></i>
                    </button>
                    <button
                      className="btn-icon-action btn-delete"
                      onClick={() => console.log('Deletar', supplier.supplier_id)}
                      title="Excluir"
                    >
                      <i className="bi bi-trash3"></i>
                    </button>
                  </div>
                </div>

                <div className="supplier-card-body">
                  <div className="form-field-inline">
                    <label>Status</label>
                    <div className="custom-select-wrapper">
                      <select
                        value={
                          selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.supplier_status
                            : supplier.supplier_status || ''
                        }
                        onChange={(e) => {
                          handleFieldChange(supplier, 'supplier_status', e.target.value);
                        }}
                        className={`form-input status-select ${
                          ((selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.supplier_status
                            : supplier.supplier_status) || '').toLowerCase()
                        }`}
                      >
                        <option value="">Status</option>
                        <option value="Active">Active</option>
                        <option value="Inactive">Inactive</option>
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  </div>

                  <div className="form-field-inline">
                    <label>Origem</label>
                    <div className="custom-select-wrapper">
                      <select
                        value={
                          selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.supplier_category
                            : supplier.supplier_category || ''
                        }
                        onChange={(e) => {
                          handleFieldChange(supplier, 'supplier_category', e.target.value);
                        }}
                        className="form-input"
                      >
                        <option value="">Origem</option>
                        <option value="Nacional">Nacional</option>
                        <option value="Importado">Importado</option>
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  </div>

                  <div className="form-field-inline full-width">
                    <label>Email (use ; para separar os contatos)</label>
                    <textarea
                      value={
                        selectedSupplier?.supplier_id === supplier.supplier_id
                          ? formData.supplier_email
                          : supplier.supplier_email || ''
                      }
                      onChange={(e) => {
                        handleFieldChange(supplier, 'supplier_email', e.target.value);
                      }}
                      className="form-input form-textarea"
                      placeholder="Email (use ; para separar os contatos)"
                      rows={3}
                    />
                  </div>

                  <div className="form-field-inline">
                    <label>SSID</label>
                    <input
                      type="text"
                      value={
                        selectedSupplier?.supplier_id === supplier.supplier_id
                          ? formData.ssid
                          : supplier.ssid || ''
                      }
                      onChange={(e) => {
                        handleFieldChange(supplier, 'ssid', e.target.value);
                      }}
                      className="form-input"
                      placeholder="SSID"
                    />
                  </div>

                  <div className="form-field-inline">
                    <label>PO</label>
                    <input
                      type="text"
                      value={
                        selectedSupplier?.supplier_id === supplier.supplier_id
                          ? formData.supplier_po
                          : supplier.supplier_po || ''
                      }
                      onChange={(e) => {
                        handleFieldChange(supplier, 'supplier_po', e.target.value);
                      }}
                      className="form-input"
                      placeholder="PO"
                    />
                  </div>

                  <div className="form-field-inline">
                    <label>BU (Business Unit)</label>
                    <div className="custom-select-wrapper">
                      <select
                        value={
                          selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.bu
                            : supplier.bu || ''
                        }
                        onChange={(e) => {
                          handleFieldChange(supplier, 'bu', e.target.value);
                        }}
                        className="form-input"
                      >
                        <option value=""></option>
                        {businessUnits.map(bu => (
                          <option key={bu} value={bu}>{bu}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  </div>

                  <div className="form-field-inline">
                    <label>Categoria</label>
                    <div className="custom-select-wrapper">
                      <select
                        value={
                          selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.supplier_category
                            : supplier.supplier_category || ''
                        }
                        onChange={(e) => {
                          handleFieldChange(supplier, 'supplier_category', e.target.value);
                        }}
                        className="form-input"
                      >
                        <option value=""></option>
                        {categories.map(cat => (
                          <option key={cat} value={cat}>{cat}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  </div>

                  <div className="form-field-inline">
                    <label>Planner</label>
                    <div className="custom-select-wrapper">
                      <select
                        value={
                          selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.planner
                            : supplier.planner || ''
                        }
                        onChange={(e) => {
                          handleFieldChange(supplier, 'planner', e.target.value);
                        }}
                        className="form-input"
                      >
                        <option value=""></option>
                        {planners.map((planner) => (
                          <option key={planner} value={planner}>{planner}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  </div>

                  <div className="form-field-inline">
                    <label>Continuity</label>
                    <div className="custom-select-wrapper">
                      <select
                        value={
                          selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.continuity
                            : supplier.continuity || ''
                        }
                        onChange={(e) => {
                          handleFieldChange(supplier, 'continuity', e.target.value);
                        }}
                        className="form-input"
                      >
                        <option value=""></option>
                        {continuityOptions.map((option) => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  </div>

                  <div className="form-field-inline">
                    <label>Sourcing</label>
                    <div className="custom-select-wrapper">
                      <select
                        value={
                          selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.sourcing
                            : supplier.sourcing || ''
                        }
                        onChange={(e) => {
                          handleFieldChange(supplier, 'sourcing', e.target.value);
                        }}
                        className="form-input"
                      >
                        <option value=""></option>
                        {sourcingOptions.map((option) => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  </div>

                  <div className="form-field-inline">
                    <label>SQIE</label>
                    <div className="custom-select-wrapper">
                      <select
                        value={
                          selectedSupplier?.supplier_id === supplier.supplier_id
                            ? formData.sqie
                            : supplier.sqie || ''
                        }
                        onChange={(e) => {
                          handleFieldChange(supplier, 'sqie', e.target.value);
                        }}
                        className="form-input"
                      >
                        <option value=""></option>
                        {sqieOptions.map((option) => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  </div>

                </div>

                {/* Botões de ação quando em modo de edição */}
                {isEditing && selectedSupplier?.supplier_id === supplier.supplier_id && (
                  <div className="supplier-card-actions">
                    <button 
                      className="btn-cancel-card" 
                      onClick={handleCancel}
                      disabled={isSaving}
                    >
                      <i className="bi bi-x-lg"></i>
                      Cancelar
                    </button>
                    <button 
                      className="btn-save-card" 
                      onClick={handleSave}
                      disabled={isSaving}
                    >
                      {isSaving ? (
                        <>
                          <i className="bi bi-arrow-repeat spin"></i>
                          Salvando...
                        </>
                      ) : (
                        <>
                          <i className="bi bi-check-lg"></i>
                          Salvar
                        </>
                      )}
                    </button>
                  </div>
                )}

                {supplier.total_score && (
                  <div className="supplier-score-badge">
                    <i className="bi bi-trophy-fill"></i>
                    Score Total: {supplier.total_score}
                  </div>
                )}
              </div>
            ))}
          </div>

          <button className="carousel-nav carousel-nav-right" onClick={scrollRight}>
            <i className="bi bi-chevron-right"></i>
          </button>
        </div>
      ) : (
        <div className="supplier-empty-state">
          <i className="bi bi-shop"></i>
          <p>Busque e edite fornecedores</p>
          <span className="empty-state-hint">Use a busca acima para encontrar fornecedores</span>
        </div>
      )}



      {searchQuery.trim().length >= 1 && suppliers.length === 0 && !isSearching && (
        <div className="supplier-empty-state">
          <i className="bi bi-inbox"></i>
          <p>Nenhum fornecedor encontrado</p>
        </div>
      )}

      {/* Botão Flutuante para Adicionar Fornecedor */}
      <button 
        className="btn-add-supplier-fab"
        title="Adicionar Fornecedor"
        onClick={() => setIsAddModalOpen(true)}
      >
        <i className="bi bi-plus"></i>
      </button>

      {/* Modal para Adicionar Fornecedor */}
      <SupplierEditModal
        isOpen={isAddModalOpen}
        supplier={null}
        onClose={() => setIsAddModalOpen(false)}
        onSave={() => {
          setIsAddModalOpen(false);
          if (searchQuery.trim().length >= 1) {
            handleSearch();
          }
        }}
      />
    </div>
  );
}

export default SupplierManager;
