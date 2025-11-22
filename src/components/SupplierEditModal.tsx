import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { useToastContext } from '../contexts/ToastContext';
import './SupplierEditModal.css';

interface SupplierEditModalProps {
  isOpen: boolean;
  supplier: any | null;
  onClose: () => void;
  onSave: (updatedSupplier: any) => void;
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
}

const SupplierEditModal: React.FC<SupplierEditModalProps> = ({ isOpen, supplier, onClose, onSave }) => {
  const { showToast } = useToastContext();
  const [isSaving, setIsSaving] = useState(false);
  
  // Estados para dropdowns
  const [planners, setPlanners] = useState<string[]>([]);
  const [continuityOptions, setContinuityOptions] = useState<string[]>([]);
  const [sourcingOptions, setSourcingOptions] = useState<string[]>([]);
  const [sqieOptions, setSqieOptions] = useState<string[]>([]);
  const [businessUnits, setBusinessUnits] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);

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
  });

  // Carregar opções dos dropdowns
  useEffect(() => {
    if (!isOpen) return;

    const loadDropdownOptions = async () => {
      try {
        const [plannersData, continuityData, sourcingData, sqieData, businessUnitsData, categoriesData] = await Promise.all([
          invoke<string[]>('get_planners'),
          invoke<string[]>('get_continuity_options'),
          invoke<string[]>('get_sourcing_options'),
          invoke<string[]>('get_sqie_options'),
          invoke<string[]>('get_business_units'),
          invoke<string[]>('get_categories'),
        ]);
        
        setPlanners(plannersData);
        setContinuityOptions(continuityData);
        setSourcingOptions(sourcingData);
        setSqieOptions(sqieData);
        setBusinessUnits(businessUnitsData);
        setCategories(categoriesData);
      } catch (error) {
        console.error('Erro ao carregar opções dos dropdowns:', error);
      }
    };

    loadDropdownOptions();
  }, [isOpen]);

  // Preencher formulário quando o supplier mudar
  useEffect(() => {
    if (supplier) {
      setFormData({
        supplier_id: supplier.supplier_id || '',
        supplier_name: supplier.vendor_name || supplier.supplier_name || '',
        supplier_po: supplier.supplier_po || '',
        bu: supplier.bu || supplier.business_unit || '',
        supplier_email: supplier.supplier_email || '',
        supplier_status: supplier.supplier_status || '',
        planner: supplier.planner || '',
        country: supplier.country || '',
        supplier_category: supplier.supplier_category || '',
        continuity: supplier.continuity || '',
        sourcing: supplier.sourcing || '',
        sqie: supplier.sqie || '',
        ssid: supplier.ssid || '',
      });
    } else {
      // Novo fornecedor - formulário vazio
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
      });
    }
  }, [supplier]);

  const handleInputChange = (field: keyof SupplierUpdate, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = async () => {
    // Validação: Nome do fornecedor obrigatório
    if (!formData.supplier_name || formData.supplier_name.trim() === '') {
      showToast('Nome do fornecedor é obrigatório', 'error');
      return;
    }

    // Validação: Origem obrigatória
    if (!formData.country || formData.country.trim() === '') {
      showToast('Origem é obrigatória', 'error');
      return;
    }

    // Validação: PO único (se preenchido)
    if (formData.supplier_po && formData.supplier_po.trim() !== '') {
      try {
        const existingSupplier = await invoke<any>('check_po_exists', { 
          po: formData.supplier_po,
          currentSupplierId: formData.supplier_id || ''
        });
        
        if (existingSupplier) {
          showToast(`PO ${formData.supplier_po} já está sendo usado por ${existingSupplier.vendor_name}`, 'error');
          return;
        }
      } catch (error) {
        console.error('Erro ao verificar PO:', error);
      }
    }

    try {
      setIsSaving(true);
      
      console.log('💾 Salvando fornecedor:', formData);
      
      if (supplier) {
        // Editar fornecedor existente
        await invoke('update_supplier_data', { supplier: formData });
        showToast('Fornecedor atualizado com sucesso!', 'success');
        console.log('✅ Fornecedor atualizado');
      } else {
        // Criar novo fornecedor - gerar supplier_id único baseado em timestamp
        const newSupplierId = `SUP_${Date.now()}`;
        const newSupplier = {
          ...formData,
          supplier_id: newSupplierId
        };
        
        await invoke('create_supplier', { supplier: newSupplier });
        showToast('Fornecedor criado com sucesso!', 'success');
        console.log('✅ Fornecedor criado');
      }
      
      // Passar o formData atualizado para o callback
      const updatedSupplier = {
        ...supplier,
        ...formData,
        vendor_name: formData.supplier_name
      };
      onSave(updatedSupplier);
      onClose();
    } catch (error) {
      console.error('Erro ao salvar fornecedor:', error);
      showToast(`Erro ao ${supplier ? 'atualizar' : 'criar'} fornecedor`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    // Resetar formulário
    if (supplier) {
      setFormData({
        supplier_id: supplier.supplier_id || '',
        supplier_name: supplier.vendor_name || supplier.supplier_name || '',
        supplier_po: supplier.supplier_po || '',
        bu: supplier.bu || supplier.business_unit || '',
        supplier_email: supplier.supplier_email || '',
        supplier_status: supplier.supplier_status || '',
        planner: supplier.planner || '',
        country: supplier.country || '',
        supplier_category: supplier.supplier_category || '',
        continuity: supplier.continuity || '',
        sourcing: supplier.sourcing || '',
        sqie: supplier.sqie || '',
        ssid: supplier.ssid || '',
      });
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="supplier-edit-modal-overlay">
      <div className="supplier-edit-modal">
        <div className="supplier-edit-header">
          <span className="supplier-edit-title">
            <i className="bi bi-pencil-square"></i> {supplier ? 'Editar Fornecedor' : 'Adicionar Fornecedor'}
          </span>
          <button className="supplier-edit-close" onClick={handleCancel}>
            <i className="bi bi-x-lg"></i>
          </button>
        </div>

        <div className="supplier-edit-main">
          <div className="supplier-edit-form">
            {/* Seção: Informações Básicas */}
            <div className="form-section">
              <h3 className="section-title">
                <i className="bi bi-info-circle"></i>
                Informações Básicas
              </h3>
              
              {/* Nome do Fornecedor */}
              <div className="form-field full-width">
                <label>Vendor Name *</label>
                <input
                  type="text"
                  value={formData.supplier_name}
                  onChange={(e) => handleInputChange('supplier_name', e.target.value)}
                  className="form-input"
                  placeholder="Nome do fornecedor"
                  disabled={!!supplier}
                />
                {supplier && (
                  <small style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
                    Nome do fornecedor não pode ser editado
                  </small>
                )}
              </div>

              {/* Category e BU */}
              <div className="form-row">
                <div className="form-field">
                  <label>Category</label>
                  <div className="custom-select-wrapper">
                    <select
                      value={formData.supplier_category}
                      onChange={(e) => handleInputChange('supplier_category', e.target.value)}
                      className="form-input"
                    >
                      <option value="">Selecione</option>
                      {categories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>
                </div>

                <div className="form-field">
                  <label>BU (Business Unit)</label>
                  <div className="custom-select-wrapper">
                    <select
                      value={formData.bu}
                      onChange={(e) => handleInputChange('bu', e.target.value)}
                      className="form-input"
                    >
                      <option value="">Selecione</option>
                      {businessUnits.map(bu => (
                        <option key={bu} value={bu}>{bu}</option>
                      ))}
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>
                </div>
              </div>

              {/* Origem */}
              <div className="form-field full-width">
                <label>Origem *</label>
                <div className="custom-select-wrapper">
                  <select
                    value={formData.country}
                    onChange={(e) => handleInputChange('country', e.target.value)}
                    className="form-input"
                  >
                    <option value="">Selecione</option>
                    <option value="Nacional">Nacional</option>
                    <option value="Importado">Importado</option>
                  </select>
                  <i className="bi bi-chevron-down select-icon"></i>
                </div>
              </div>
            </div>

            {/* Seção: Contato */}
            <div className="form-section">
              <h3 className="section-title">
                <i className="bi bi-envelope"></i>
                Contato
              </h3>
              
              <div className="form-field full-width">
                <label>Email</label>
                <textarea
                  value={formData.supplier_email}
                  onChange={(e) => handleInputChange('supplier_email', e.target.value)}
                  className="form-input form-textarea"
                  placeholder="Email (use ; para separar os contatos)"
                  rows={2}
                />
              </div>
            </div>

            {/* Seção: Identificação */}
            <div className="form-section">
              <h3 className="section-title">
                <i className="bi bi-hash"></i>
                Identificação
              </h3>
              
              <div className="form-row">
                <div className="form-field">
                  <label>SSID (Único)</label>
                  <input
                    type="text"
                    value={formData.ssid}
                    onChange={(e) => handleInputChange('ssid', e.target.value)}
                    className="form-input"
                    placeholder="SSID"
                  />
                </div>

                <div className="form-field">
                  <label>PO (Único)</label>
                  <input
                    type="text"
                    value={formData.supplier_po}
                    onChange={(e) => handleInputChange('supplier_po', e.target.value)}
                    className="form-input"
                    placeholder="PO"
                  />
                </div>
              </div>

              {/* Status */}
              <div className="form-field full-width">
                <label>Status</label>
                <div className="custom-select-wrapper">
                  <select
                    value={formData.supplier_status}
                    onChange={(e) => handleInputChange('supplier_status', e.target.value)}
                    className={`form-input status-select ${(formData.supplier_status || '').toLowerCase()}`}
                  >
                    <option value="">Selecione</option>
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                  <i className="bi bi-chevron-down select-icon"></i>
                </div>
              </div>
            </div>

            {/* Seção: Responsáveis */}
            <div className="form-section">
              <h3 className="section-title">
                <i className="bi bi-people"></i>
                Responsáveis
              </h3>
              
              <div className="form-row">
                <div className="form-field">
                  <label>Planner</label>
                  <div className="custom-select-wrapper">
                    <select
                      value={formData.planner}
                      onChange={(e) => handleInputChange('planner', e.target.value)}
                      className="form-input"
                    >
                      <option value="">Selecione</option>
                      {planners.map((planner) => (
                        <option key={planner} value={planner}>{planner}</option>
                      ))}
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>
                </div>

                <div className="form-field">
                  <label>Continuity</label>
                  <div className="custom-select-wrapper">
                    <select
                      value={formData.continuity}
                      onChange={(e) => handleInputChange('continuity', e.target.value)}
                      className="form-input"
                    >
                      <option value="">Selecione</option>
                      {continuityOptions.map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>
                </div>
              </div>

              <div className="form-row">
                <div className="form-field">
                  <label>Sourcing</label>
                  <div className="custom-select-wrapper">
                    <select
                      value={formData.sourcing}
                      onChange={(e) => handleInputChange('sourcing', e.target.value)}
                      className="form-input"
                    >
                      <option value="">Selecione</option>
                      {sourcingOptions.map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>
                </div>

                <div className="form-field">
                  <label>SQIE</label>
                  <div className="custom-select-wrapper">
                    <select
                      value={formData.sqie}
                      onChange={(e) => handleInputChange('sqie', e.target.value)}
                      className="form-input"
                    >
                      <option value="">Selecione</option>
                      {sqieOptions.map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="supplier-edit-footer">
          <button className="btn-cancel" onClick={handleCancel} disabled={isSaving}>
            Cancelar
          </button>
          <button className="btn-save" onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <i className="bi bi-arrow-repeat spin"></i> Salvando...
              </>
            ) : (
              <>
                <i className="bi bi-check-lg"></i> Salvar
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SupplierEditModal;
