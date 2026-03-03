import { useState, useEffect, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { useToastContext } from '../contexts/ToastContext';
import SupplierEditModal from './SupplierEditModal';
import ImportSupplierModal from './ImportSupplierModal';
import DeleteModal from '../utils/DeleteModal';
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
  const [isSaving, setIsSaving] = useState(false);
  const [savingSuppliers, setSavingSuppliers] = useState<Set<string>>(new Set());
  const saveTimeouts = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Supplier | null>(null);
  const [deleteCode, setDeleteCode] = useState('');
  const [deleteInput, setDeleteInput] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [emailChipsMap, setEmailChipsMap] = useState<Map<string, string[]>>(new Map());
  const [emailInputMap, setEmailInputMap] = useState<Map<string, string>>(new Map());
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

  const generateDeleteCode = () => {
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    let code = '';
    for (let i = 0; i < 3; i += 1) {
      code += letters.charAt(Math.floor(Math.random() * letters.length));
    }
    return code;
  };

  const handleRequestDelete = (supplier: Supplier) => {
    if ((supplier.supplier_status || '').toLowerCase() === 'active') {
      showToast('Não é possível excluir fornecedor com status Active', 'warning');
      return;
    }
    const code = generateDeleteCode();
    setDeleteTarget(supplier);
    setDeleteCode(code);
    setDeleteInput('');
    setIsDeleteModalOpen(true);
  };

  const handleCancelDelete = () => {
    setIsDeleteModalOpen(false);
    setDeleteTarget(null);
    setDeleteCode('');
    setDeleteInput('');
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    if (deleteInput.trim().toUpperCase() !== deleteCode) {
      showToast('Código de confirmação inválido', 'error');
      return;
    }

    try {
      await invoke('delete_supplier', { supplierId: deleteTarget.supplier_id });
      setSuppliers(prev => prev.filter(s => s.supplier_id !== deleteTarget.supplier_id));
      if (selectedSupplier?.supplier_id === deleteTarget.supplier_id) {
        setSelectedSupplier(null);
        setFormData({
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
      }
      handleCancelDelete();
      showToast('Fornecedor excluído com sucesso', 'success');
    } catch (error) {
      console.error('Erro ao excluir fornecedor:', error);
      showToast('Erro ao excluir fornecedor', 'error');
    }
  };



  const handleInputChange = (field: keyof SupplierUpdate, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleFieldChange = async (supplier: Supplier, field: keyof SupplierUpdate, value: string) => {
    // Atualizar formData
    if (selectedSupplier?.supplier_id !== supplier.supplier_id) {
      handleSelectSupplier(supplier);
    }
    handleInputChange(field, value);

    // Cancelar timeout anterior se existir
    const existingTimeout = saveTimeouts.current.get(supplier.supplier_id);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }

    // Criar novo timeout para salvar após 1 segundo
    const newTimeout = setTimeout(async () => {
      await autoSave(supplier.supplier_id, field, value);
    }, 1000);

    saveTimeouts.current.set(supplier.supplier_id, newTimeout);
  };

  const autoSave = async (supplierId: string, field: keyof SupplierUpdate, value: string) => {
    try {
      setSavingSuppliers(prev => new Set(prev).add(supplierId));
      
      // Buscar dados atuais do fornecedor
      const currentSupplier = suppliers.find(s => s.supplier_id === supplierId);
      if (!currentSupplier) return;

      const updateData: SupplierUpdate = {
        supplier_id: currentSupplier.supplier_id,
        supplier_name: currentSupplier.vendor_name,
        supplier_po: currentSupplier.supplier_po || '',
        bu: currentSupplier.bu || '',
        supplier_email: currentSupplier.supplier_email || '',
        supplier_status: currentSupplier.supplier_status || '',
        planner: currentSupplier.planner || '',
        country: currentSupplier.country || '',
        supplier_category: currentSupplier.supplier_category || '',
        continuity: currentSupplier.continuity || '',
        sourcing: currentSupplier.sourcing || '',
        sqie: currentSupplier.sqie || '',
        ssid: currentSupplier.ssid || '',
        otif_target: currentSupplier.otif_target || '',
        nil_target: currentSupplier.nil_target || '',
        pickup_target: currentSupplier.pickup_target || '',
        package_target: currentSupplier.package_target || '',
        [field]: value,
      };

      await invoke('update_supplier_data', { supplier: updateData });
      
      // Atualizar a lista local
      setSuppliers(prev =>
        prev.map(s => s.supplier_id === supplierId ? { ...s, [field]: value } : s)
      );
      
      showToast('Salvo automaticamente', 'success');
    } catch (error) {
      console.error('Erro ao salvar automaticamente:', error);
      showToast('Erro ao salvar', 'error');
    } finally {
      setSavingSuppliers(prev => {
        const newSet = new Set(prev);
        newSet.delete(supplierId);
        return newSet;
      });
      saveTimeouts.current.delete(supplierId);
    }
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
    } catch (error) {
      console.error('Erro ao salvar fornecedor:', error);
      showToast('Erro ao salvar fornecedor', 'error');
    } finally {
      setIsSaving(false);
    }
  };



  const splitEmails = (raw: string | undefined): string[] => {
    if (!raw) return [];
    return raw.split(/[;,\n]/).map(s => s.trim()).filter(Boolean);
  };

  const initEmailChips = (supplierId: string, emailStr: string) => {
    const chips = splitEmails(emailStr);
    setEmailChipsMap(prev => new Map(prev).set(supplierId, chips));
    setEmailInputMap(prev => new Map(prev).set(supplierId, ''));
  };

  const addEmailChip = (supplier: Supplier, rawValue: string) => {
    const trimmed = rawValue.trim();
    if (!trimmed) return;
    const parts = splitEmails(trimmed);
    if (parts.length === 0) return;

    setEmailChipsMap(prev => {
      const current = prev.get(supplier.supplier_id) || [];
      const existing = new Set(current.map(e => e.toLowerCase()));
      const next = [...current];
      for (const part of parts) {
        if (!existing.has(part.toLowerCase())) {
          existing.add(part.toLowerCase());
          next.push(part);
        }
      }
      const updated = new Map(prev).set(supplier.supplier_id, next);
      // Sync to formData
      const normalized = next.join('; ');
      handleFieldChange(supplier, 'supplier_email', normalized);
      return updated;
    });
    setEmailInputMap(prev => new Map(prev).set(supplier.supplier_id, ''));
  };

  const removeEmailChip = (supplier: Supplier, target: string) => {
    setEmailChipsMap(prev => {
      const current = prev.get(supplier.supplier_id) || [];
      const next = current.filter(e => e !== target);
      const updated = new Map(prev).set(supplier.supplier_id, next);
      const normalized = next.join('; ');
      handleFieldChange(supplier, 'supplier_email', normalized);
      return updated;
    });
  };

  const toggleRowExpanded = (supplierId: string, supplier: Supplier) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      if (next.has(supplierId)) {
        next.delete(supplierId);
      } else {
        next.add(supplierId);
        // Init chips when expanding
        const emailStr = selectedSupplier?.supplier_id === supplierId
          ? formData.supplier_email
          : supplier.supplier_email || '';
        initEmailChips(supplierId, emailStr || '');
      }
      return next;
    });
  };

  const handleExportSuppliers = async () => {
    try {
      console.log('📤 Iniciando exportação de suppliers...');
      
      const excelBuffer = await invoke<number[]>('export_suppliers');
      const uint8Array = new Uint8Array(excelBuffer);
      
      const fileName = `Suppliers_Export_${new Date().toISOString().split('T')[0]}.xlsx`;
      
      const { save } = await import('@tauri-apps/api/dialog');
      const filePath = await save({
        defaultPath: fileName,
        filters: [{
          name: 'Excel',
          extensions: ['xlsx']
        }]
      });

      if (filePath) {
        const { writeBinaryFile } = await import('@tauri-apps/api/fs');
        await writeBinaryFile(filePath, uint8Array);
        showToast('Suppliers exportados com sucesso!', 'success');
      }
    } catch (error) {
      console.error('❌ Erro ao exportar suppliers:', error);
      showToast(`Erro ao exportar: ${error}`, 'error');
    }
  };

  const handleImportSuppliers = () => {
    setIsImportModalOpen(true);
  };

  const handleImportSuccess = async () => {
    // Atualiza a busca se houver
    if (searchQuery.trim().length >= 1) {
      await handleSearch();
    }
    showToast('Suppliers importados com sucesso!', 'success');
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
              {suppliers.length > 0 && !isSearching && (
                <span className="count-inside-input">{suppliers.length}</span>
              )}
            </div>
            <div className="supplier-actions">
              <button className="btn-secondary" onClick={handleExportSuppliers}>
                <i className="bi bi-download"></i>
                Exportar
              </button>
              <button className="btn-secondary" onClick={handleImportSuppliers}>
                Importar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabela de Fornecedores */}
      {isSearching ? (
        <div className="supplier-table-container">
          <table className="supplier-table">
            <thead>
              <tr>
                <th className="col-arrow"></th>
                <th className="col-id">ID</th>
                <th className="col-name">Nome</th>
                <th className="col-status">Status</th>
                <th className="col-po">PO</th>
                <th className="col-bu">BU</th>
                <th className="col-actions"></th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3].map((i) => (
                <tr key={i} className="supplier-row skeleton-row">
                  <td><div className="skeleton skeleton-sm"></div></td>
                  <td><div className="skeleton skeleton-sm"></div></td>
                  <td><div className="skeleton skeleton-md"></div></td>
                  <td><div className="skeleton skeleton-sm"></div></td>
                  <td><div className="skeleton skeleton-sm"></div></td>
                  <td><div className="skeleton skeleton-sm"></div></td>
                  <td><div className="skeleton skeleton-sm"></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : suppliers.length > 0 ? (
        <div className="supplier-table-container">
          <table className="supplier-table">
            <thead>
              <tr>
                <th className="col-arrow"></th>
                <th className="col-id">ID</th>
                <th className="col-name">Nome</th>
                <th className="col-status">Status</th>
                <th className="col-po">PO</th>
                <th className="col-bu">BU</th>
                <th className="col-actions"></th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((supplier) => {
                const isExpanded = expandedRows.has(supplier.supplier_id);
                const isSelected = selectedSupplier?.supplier_id === supplier.supplier_id;
                const statusValue = isSelected ? formData.supplier_status : supplier.supplier_status || '';
                const poValue = isSelected ? formData.supplier_po : supplier.supplier_po || '';
                const buValue = isSelected ? formData.bu : supplier.bu || '';

                return (
                  <>
                    <tr
                      key={supplier.supplier_id}
                      className={`supplier-row ${isExpanded ? 'expanded' : ''}`}
                      onClick={() => {
                        toggleRowExpanded(supplier.supplier_id, supplier);
                        if (!isSelected) handleSelectSupplier(supplier);
                      }}
                    >
                      <td className="col-arrow">
                        <i className={`bi bi-chevron-${isExpanded ? 'down' : 'right'} row-expand-icon`}></i>
                      </td>
                      <td className="col-id">{supplier.supplier_id}</td>
                      <td className="col-name" title={supplier.vendor_name || 'Sem Nome'}>
                        {supplier.vendor_name || 'Sem Nome'}
                      </td>
                      <td className="col-status">
                        <span className={`status-badge ${(statusValue || '').toLowerCase()}`}>
                          {statusValue || '—'}
                        </span>
                      </td>
                      <td className="col-po">{poValue || '—'}</td>
                      <td className="col-bu">{buValue || '—'}</td>
                      <td className="col-actions" onClick={(e) => e.stopPropagation()}>
                        {savingSuppliers.has(supplier.supplier_id) && (
                          <span className="auto-save-indicator">
                            <i className="bi bi-arrow-repeat spin"></i>
                          </span>
                        )}
                        <button
                          className="btn-icon-action btn-delete"
                          onClick={() => handleRequestDelete(supplier)}
                          title="Excluir"
                        >
                          <i className="bi bi-trash3"></i>
                        </button>
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr key={`${supplier.supplier_id}-expanded`} className="supplier-expanded-row">
                        <td colSpan={7}>
                          <div className="supplier-expanded-content">
                            <div className="expanded-fields-grid">
                              <div className="form-field-inline">
                                <label>Status</label>
                                <div className="custom-select-wrapper">
                                  <select
                                    value={isSelected ? formData.supplier_status : supplier.supplier_status || ''}
                                    onChange={(e) => handleFieldChange(supplier, 'supplier_status', e.target.value)}
                                    className={`form-input status-select ${((isSelected ? formData.supplier_status : supplier.supplier_status) || '').toLowerCase()}`}
                                  >
                                    <option value=""></option>
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
                                    value={isSelected ? formData.country : supplier.country || ''}
                                    onChange={(e) => handleFieldChange(supplier, 'country', e.target.value)}
                                    className="form-input"
                                  >
                                    <option value=""></option>
                                    <option value="Nacional">Nacional</option>
                                    <option value="Importado">Importado</option>
                                  </select>
                                  <i className="bi bi-chevron-down select-icon"></i>
                                </div>
                              </div>

                              <div className="form-field-inline">
                                <label>SSID</label>
                                <input
                                  type="text"
                                  value={isSelected ? formData.ssid : supplier.ssid || ''}
                                  onChange={(e) => handleFieldChange(supplier, 'ssid', e.target.value)}
                                  className="form-input"
                                />
                              </div>

                              <div className="form-field-inline">
                                <label>PO</label>
                                <input
                                  type="text"
                                  value={isSelected ? formData.supplier_po : supplier.supplier_po || ''}
                                  onChange={(e) => handleFieldChange(supplier, 'supplier_po', e.target.value)}
                                  className="form-input"
                                />
                              </div>

                              <div className="form-field-inline">
                                <label>BU (Business Unit)</label>
                                <div className="custom-select-wrapper">
                                  <select
                                    value={isSelected ? formData.bu : supplier.bu || ''}
                                    onChange={(e) => handleFieldChange(supplier, 'bu', e.target.value)}
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
                                <label>Planner</label>
                                <div className="custom-select-wrapper">
                                  <select
                                    value={isSelected ? formData.planner : supplier.planner || ''}
                                    onChange={(e) => handleFieldChange(supplier, 'planner', e.target.value)}
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
                                    value={isSelected ? formData.continuity : supplier.continuity || ''}
                                    onChange={(e) => handleFieldChange(supplier, 'continuity', e.target.value)}
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
                                    value={isSelected ? formData.sourcing : supplier.sourcing || ''}
                                    onChange={(e) => handleFieldChange(supplier, 'sourcing', e.target.value)}
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
                                    value={isSelected ? formData.sqie : supplier.sqie || ''}
                                    onChange={(e) => handleFieldChange(supplier, 'sqie', e.target.value)}
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

                              <div className="form-field-inline">
                                <label>Categoria</label>
                                <div className="custom-select-wrapper">
                                  <select
                                    value={isSelected ? formData.supplier_category : supplier.supplier_category || ''}
                                    onChange={(e) => handleFieldChange(supplier, 'supplier_category', e.target.value)}
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

                              <div className="form-field-inline full-width">
                                <label>Email</label>
                                <div className="sm-email-chips-box">
                                  <div className="sm-email-chips-list">
                                    {(emailChipsMap.get(supplier.supplier_id) || []).map((email) => (
                                      <span key={email} className="sm-email-chip">
                                        <span>{email}</span>
                                        <button
                                          type="button"
                                          className="sm-email-chip-remove"
                                          onClick={() => removeEmailChip(supplier, email)}
                                          title="Remover email"
                                        >
                                          <i className="bi bi-x"></i>
                                        </button>
                                      </span>
                                    ))}
                                  </div>
                                  <input
                                    className="form-input sm-email-chip-input"
                                    value={emailInputMap.get(supplier.supplier_id) || ''}
                                    onChange={(e) => setEmailInputMap(prev => new Map(prev).set(supplier.supplier_id, e.target.value))}
                                    onKeyDown={(e) => {
                                      const val = emailInputMap.get(supplier.supplier_id) || '';
                                      if (e.key === 'Enter' || e.key === ';' || e.key === ',') {
                                        e.preventDefault();
                                        addEmailChip(supplier, val);
                                      }
                                      if (e.key === 'Backspace' && !val) {
                                        const chips = emailChipsMap.get(supplier.supplier_id) || [];
                                        if (chips.length > 0) {
                                          e.preventDefault();
                                          removeEmailChip(supplier, chips[chips.length - 1]);
                                        }
                                      }
                                    }}
                                    onBlur={() => addEmailChip(supplier, emailInputMap.get(supplier.supplier_id) || '')}
                                  />
                                </div>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : !isSearching && (
        searchQuery.trim().length >= 1 ? (
          <div className="supplier-empty-state">
            <i className="bi bi-inbox"></i>
            <p>Nenhum fornecedor encontrado</p>
          </div>
        ) : (
          <div className="supplier-empty-state">
            <i className="bi bi-shop"></i>
            <p>Busque e edite fornecedores</p>
            <span className="empty-state-hint">Use a busca acima para encontrar fornecedores</span>
          </div>
        )
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

      {/* Modal de Importação */}
      <ImportSupplierModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={handleImportSuccess}
      />

      <DeleteModal
        isOpen={isDeleteModalOpen}
        title="Confirmar exclusão do fornecedor"
        description={`Você está prestes a excluir o fornecedor ${deleteTarget?.vendor_name || ''}. Esta ação não pode ser desfeita.`}
        confirmationCode={deleteCode}
        userInput={deleteInput}
        onInputChange={setDeleteInput}
        onCancel={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        confirmLabel="Excluir"
        cancelLabel="Cancelar"
        disabled={deleteInput.trim().toUpperCase() !== deleteCode || !deleteTarget}
      />
    </div>
  );
}

export default SupplierManager;
