import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { usePermissions } from '../contexts/PermissionsContext';
import { useToastContext } from '../contexts/ToastContext';
import './SupplierInfoModal.css';

interface ListItemThreeFields {
  name: string;
  email: string;
  alias: string;
}

interface SupplierInfoModalProps {
  isOpen: boolean;
  supplier: any;
  onClose: () => void;
  onEdit?: () => void;
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

const emptyFormData: SupplierUpdate = {
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
};

const SupplierInfoModal: React.FC<SupplierInfoModalProps> = ({ isOpen, supplier, onClose, onEdit }) => {
  const { showToast } = useToastContext();
  const { permissions } = usePermissions();
  const [plannerList, setPlannerList] = useState<ListItemThreeFields[]>([]);
  const [continuityList, setContinuityList] = useState<ListItemThreeFields[]>([]);
  const [sourcingList, setSourcingList] = useState<ListItemThreeFields[]>([]);
  const [sqieList, setSqieList] = useState<ListItemThreeFields[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [businessUnits, setBusinessUnits] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [currentSupplier, setCurrentSupplier] = useState(supplier);
  const [formData, setFormData] = useState<SupplierUpdate>(emptyFormData);
  const [emailChips, setEmailChips] = useState<string[]>([]);
  const [emailInput, setEmailInput] = useState('');
  const [allowSupplierEdit, setAllowSupplierEdit] = useState<boolean>(() => {
    return localStorage.getItem('allowSupplierEdit') === 'true';
  });

  const mapSupplierToFormData = (supplierData: any): SupplierUpdate => ({
    supplier_id: supplierData?.supplier_id || supplierData?.supplierId || '',
    supplier_name: supplierData?.vendor_name || supplierData?.supplier_name || '',
    supplier_po: supplierData?.supplier_po || '',
    bu: supplierData?.bu || supplierData?.business_unit || '',
    supplier_email: supplierData?.supplier_email || '',
    supplier_status: supplierData?.supplier_status || '',
    planner: supplierData?.planner || '',
    country: supplierData?.country || '',
    supplier_category: supplierData?.supplier_category || '',
    continuity: supplierData?.continuity || '',
    sourcing: supplierData?.sourcing || '',
    sqie: supplierData?.sqie || '',
    ssid: supplierData?.ssid || '',
  });

  const getResponsibleByName = (list: ListItemThreeFields[], name?: string) => {
    if (!name) return null;
    return list.find((item) => item.name === name) || null;
  };

  const copyToClipboard = async (value?: string | null, label = 'Valor') => {
    const text = (value || '').toString();
    if (!text) {
      showToast(`${label} vazio. Nada para copiar.`, 'error');
      return;
    }
    try {
      if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      showToast(`${label} copiado para a área de transferência`, 'success');
    } catch (err) {
      console.error('Erro ao copiar:', err);
      showToast('Erro ao copiar para a área de transferência', 'error');
    }
  };

  const copyAllEmails = () => {
    const source = isEditing ? formData.supplier_email : currentSupplier?.supplier_email;
    const list = splitEmails(source);
    if (!list || list.length === 0) {
      showToast('Nenhum email para copiar', 'error');
      return;
    }
    copyToClipboard(list.join('; '), 'Emails');
  };

  const splitEmails = (raw: string | undefined) => {
    if (!raw) return [];
    return raw
      .split(/[;,\n]/)
      .map((item) => item.trim())
      .filter(Boolean);
  };

  const syncEmailField = (chips: string[]) => {
    const normalized = chips.join('; ');
    setFormData((prev) => ({
      ...prev,
      supplier_email: normalized,
    }));
  };

  const addEmailChip = (rawValue: string) => {
    const trimmed = rawValue.trim();
    if (!trimmed) return;

    const parts = splitEmails(trimmed);
    if (parts.length === 0) return;

    setEmailChips((prev) => {
      const existing = new Set(prev.map((item) => item.toLowerCase()));
      const next = [...prev];

      for (const part of parts) {
        const key = part.toLowerCase();
        if (!existing.has(key)) {
          existing.add(key);
          next.push(part);
        }
      }

      syncEmailField(next);
      return next;
    });

    setEmailInput('');
  };

  const removeEmailChip = (target: string) => {
    setEmailChips((prev) => {
      const next = prev.filter((item) => item !== target);
      syncEmailField(next);
      return next;
    });
  };

  // Listener para mudanças na permissão de editar suppliers
  useEffect(() => {
    const handleSupplierEditChange = () => {
      const newValue = localStorage.getItem('allowSupplierEdit') === 'true';
      setAllowSupplierEdit(newValue);
    };

    window.addEventListener('supplierEditChanged', handleSupplierEditChange);
    return () => window.removeEventListener('supplierEditChanged', handleSupplierEditChange);
  }, []);

  // Carregar responsáveis do banco de dados
  useEffect(() => {
    if (!isOpen || !supplier) return;

    const loadSupplierData = async () => {
      try {
        setLoading(true);

        const supplierId = supplier?.supplier_id || (supplier as any)?.supplierId;
        let resolvedSupplier = supplier;

        if (supplierId) {
          const fullSupplier = await invoke<any>('get_supplier_data', {
            supplierId,
          });

          resolvedSupplier = fullSupplier || supplier;
        }

        setCurrentSupplier(resolvedSupplier);

        const [plannerData, continuityData, sourcingData, sqieData, businessUnitsData, categoriesData] = await Promise.all([
          invoke<ListItemThreeFields[]>('get_planner_list'),
          invoke<ListItemThreeFields[]>('get_continuity_list'),
          invoke<ListItemThreeFields[]>('get_sourcing_list'),
          invoke<ListItemThreeFields[]>('get_sqie_list'),
          invoke<string[]>('get_business_units'),
          invoke<string[]>('get_categories'),
        ]);

        setPlannerList(plannerData || []);
        setContinuityList(continuityData || []);
        setSourcingList(sourcingData || []);
        setSqieList(sqieData || []);
        setBusinessUnits(businessUnitsData || []);
        setCategories(categoriesData || []);
        setFormData(mapSupplierToFormData(resolvedSupplier));
        setIsEditing(false);

      } catch (error) {
        console.error('Erro ao carregar responsáveis:', error);
        setPlannerList([]);
        setContinuityList([]);
        setSourcingList([]);
        setSqieList([]);
        setFormData(mapSupplierToFormData(supplier));
      } finally {
        setLoading(false);
      }
    };

    loadSupplierData();
  }, [isOpen, supplier]);

  useEffect(() => {
    if (isOpen) {
      setIsClosing(false);
    }
  }, [isOpen, supplier]);

  const handleInputChange = (field: keyof SupplierUpdate, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleStartEdit = () => {
    const mapped = mapSupplierToFormData(currentSupplier);
    setFormData(mapped);
    setEmailChips(splitEmails(mapped.supplier_email));
    setEmailInput('');
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setFormData(mapSupplierToFormData(currentSupplier));
    setEmailChips([]);
    setEmailInput('');
    setIsEditing(false);
  };

  const handleSaveSupplier = async () => {
    if (!formData.supplier_name || formData.supplier_name.trim() === '') {
      showToast('Nome do fornecedor é obrigatório', 'error');
      return;
    }

    if (!formData.country || formData.country.trim() === '') {
      showToast('Origem é obrigatória', 'error');
      return;
    }

    if (formData.supplier_po && formData.supplier_po.trim() !== '') {
      try {
        const existingSupplier = await invoke<any>('check_po_exists', {
          po: formData.supplier_po,
          currentSupplierId: formData.supplier_id || '',
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
      await invoke('update_supplier_data', { supplier: formData });

      const updatedSupplier = {
        ...currentSupplier,
        ...formData,
        vendor_name: formData.supplier_name,
        business_unit: formData.bu,
      };

      setCurrentSupplier(updatedSupplier);
      setEmailChips([]);
      setEmailInput('');
      setIsEditing(false);
      showToast('Fornecedor atualizado com sucesso!', 'success');

      if (onEdit) {
        onEdit();
      }
    } catch (error) {
      console.error('Erro ao atualizar fornecedor:', error);
      showToast('Erro ao atualizar fornecedor', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const requestClose = () => {
    if (isClosing) return;
    setIsClosing(true);
    window.setTimeout(() => {
      onClose();
    }, 220);
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      requestClose();
    }
  };

  const planner = getResponsibleByName(plannerList, isEditing ? formData.planner : currentSupplier?.planner);
  const continuity = getResponsibleByName(continuityList, isEditing ? formData.continuity : currentSupplier?.continuity);
  const sourcing = getResponsibleByName(sourcingList, isEditing ? formData.sourcing : currentSupplier?.sourcing);
  const sqie = getResponsibleByName(sqieList, isEditing ? formData.sqie : currentSupplier?.sqie);

  if (!isOpen || !supplier) return null;

  return (
    <>
      <div className={`supplier-info-modal-overlay ${isClosing ? 'closing' : 'open'}`} onClick={handleOverlayClick}>
        <div className={`supplier-info-modal ${isClosing ? 'closing' : 'open'}`} onClick={(e) => e.stopPropagation()}>
          <div className="supplier-info-header">
            <span className="supplier-info-title">
              <i className="bi bi-buildings"></i> {isEditing ? (formData.supplier_name || currentSupplier.vendor_name) : currentSupplier.vendor_name}
            </span>
            <div className="supplier-info-header-actions">
              {(permissions.canManageSuppliers || allowSupplierEdit) && (
                isEditing ? (
                  <>
                    <button
                      className="supplier-info-header-btn supplier-info-header-cancel"
                      onClick={handleCancelEdit}
                      disabled={isSaving}
                      title="Cancelar"
                    >
                      <i className="bi bi-x-lg"></i>
                    </button>
                    <button
                      className="supplier-info-header-btn supplier-info-header-save"
                      onClick={handleSaveSupplier}
                      disabled={isSaving}
                      title="Salvar"
                    >
                      <i className="bi bi-check-lg"></i>
                    </button>
                  </>
                ) : (
                  <button className="supplier-info-edit" onClick={handleStartEdit} title="Editar">
                    <i className="bi bi-pencil"></i>
                  </button>
                )
              )}
              {!isEditing && (
                <button className="supplier-info-close" onClick={requestClose}>
                  <i className="bi bi-x-lg"></i>
                </button>
              )}
            </div>
          </div>
          <div className="supplier-info-main">
            <div className="supplier-info-scrollable">
              <div className="supplier-info-fields">
              <div className="supplier-info-row">
                <div className="supplier-info-item">
                  <span className="supplier-info-label">ID:</span>
                  <span className="supplier-info-value">{currentSupplier.supplier_id}</span>
                </div>
                <div className="supplier-info-item">
                  <span className="supplier-info-label">Fornecedor:</span>
                  {isEditing ? (
                    <input
                      className="supplier-info-inline-input"
                      value={formData.supplier_name || ''}
                      onChange={(e) => handleInputChange('supplier_name', e.target.value)}
                      placeholder="Nome do fornecedor"
                    />
                  ) : (
                    <div className="supplier-info-value-row">
                      <span className="supplier-info-value">{currentSupplier.vendor_name || '-'}</span>
                      <button
                        type="button"
                        className="supplier-info-copy-btn"
                        onClick={() => copyToClipboard(currentSupplier.vendor_name, 'Fornecedor')}
                        title="Copiar fornecedor"
                      >
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                          <rect x="4" y="8" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.8" fill="none" />
                          <rect x="10" y="4" width="10" height="10" rx="2" stroke="currentColor" strokeWidth="1.8" fill="none" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="supplier-info-row">
                <div className="supplier-info-item">
                  <span className="supplier-info-label">Categoria:</span>
                  {isEditing ? (
                    <div className="supplier-info-inline-select-wrapper">
                      <select
                        className="supplier-info-inline-select"
                        value={formData.supplier_category || ''}
                        onChange={(e) => handleInputChange('supplier_category', e.target.value)}
                      >
                        <option value="">-</option>
                        {categories.map((cat) => (
                          <option key={cat} value={cat}>{cat}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down"></i>
                    </div>
                  ) : (
                    <span className="supplier-info-value">{currentSupplier.supplier_category || '-'}</span>
                  )}
                </div>
                <div className="supplier-info-item">
                  <span className="supplier-info-label">BU:</span>
                  {isEditing ? (
                    <div className="supplier-info-inline-select-wrapper">
                      <select
                        className="supplier-info-inline-select"
                        value={formData.bu || ''}
                        onChange={(e) => handleInputChange('bu', e.target.value)}
                      >
                        <option value="">-</option>
                        {businessUnits.map((unit) => (
                          <option key={unit} value={unit}>{unit}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down"></i>
                    </div>
                  ) : (
                    <span className="supplier-info-value">{currentSupplier.bu || currentSupplier.business_unit || '-'}</span>
                  )}
                </div>
              </div>

              <div className="supplier-info-row">
                <div className="supplier-info-item">
                  <span className="supplier-info-label">Origem:</span>
                  {isEditing ? (
                    <div className="supplier-info-inline-select-wrapper">
                      <select
                        className="supplier-info-inline-select"
                        value={formData.country || ''}
                        onChange={(e) => handleInputChange('country', e.target.value)}
                      >
                        <option value="">Selecione</option>
                        <option value="Nacional">Nacional</option>
                        <option value="Importado">Importado</option>
                      </select>
                      <i className="bi bi-chevron-down"></i>
                    </div>
                  ) : (
                    <span className="supplier-info-value">{currentSupplier.country || '-'}</span>
                  )}
                </div>
                <div className="supplier-info-item">
                  <span className="supplier-info-label">SSID:</span>
                  {isEditing ? (
                    <input
                      className="supplier-info-inline-input"
                      value={formData.ssid || ''}
                      onChange={(e) => handleInputChange('ssid', e.target.value)}
                      placeholder="SSID"
                    />
                  ) : (
                    <span className="supplier-info-value">{currentSupplier.ssid || '-'}</span>
                  )}
                </div>
              </div>

              <div className="supplier-info-row">
                <div className="supplier-info-item">
                  <span className="supplier-info-label">PO:</span>
                  {isEditing ? (
                    <input
                      className="supplier-info-inline-input"
                      value={formData.supplier_po || ''}
                      onChange={(e) => handleInputChange('supplier_po', e.target.value)}
                      placeholder="PO"
                    />
                  ) : (
                    <div className="supplier-info-value-row">
                      <span className="supplier-info-value">{currentSupplier.supplier_po || '-'}</span>
                      <button
                        type="button"
                        className="supplier-info-copy-btn"
                        onClick={() => copyToClipboard(currentSupplier.supplier_po, 'PO')}
                        title="Copiar PO"
                      >
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                          <rect x="4" y="8" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.8" fill="none" />
                          <rect x="10" y="4" width="10" height="10" rx="2" stroke="currentColor" strokeWidth="1.8" fill="none" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
                <div className="supplier-info-item">
                  <span className="supplier-info-label">Status:</span>
                  {isEditing ? (
                    <div className="supplier-info-inline-select-wrapper">
                      <select
                        className="supplier-info-inline-select"
                        value={formData.supplier_status || ''}
                        onChange={(e) => handleInputChange('supplier_status', e.target.value)}
                      >
                        <option value="">-</option>
                        <option value="Active">Active</option>
                        <option value="Inactive">Inactive</option>
                      </select>
                      <i className="bi bi-chevron-down"></i>
                    </div>
                  ) : (
                    <span className="supplier-info-value">{currentSupplier.supplier_status || '-'}</span>
                  )}
                </div>
              </div>

              <div className="supplier-info-section-title supplier-info-section-title-contact">Contatos</div>
              <div className="supplier-info-email">
                <div className="supplier-info-email-box">
                  {isEditing ? (
                    <div className="supplier-info-email-chips-box">
                      <div className="supplier-info-email-chips-list">
                        {emailChips.map((email) => (
                          <span key={email} className="supplier-info-email-chip">
                            <span>{email}</span>
                            <button
                              type="button"
                              className="supplier-info-email-chip-remove"
                              onClick={() => removeEmailChip(email)}
                              title="Remover email"
                            >
                              <i className="bi bi-x"></i>
                            </button>
                          </span>
                        ))}
                      </div>
                      <input
                        className="supplier-info-inline-input supplier-info-email-chip-input"
                        value={emailInput}
                        onChange={(e) => setEmailInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ';' || e.key === ',') {
                            e.preventDefault();
                            addEmailChip(emailInput);
                          }

                          if (e.key === 'Backspace' && !emailInput && emailChips.length > 0) {
                            e.preventDefault();
                            removeEmailChip(emailChips[emailChips.length - 1]);
                          }
                        }}
                        onBlur={() => addEmailChip(emailInput)}
                        placeholder="Digite email e pressione Enter"
                      />
                    </div>
                  ) : splitEmails(currentSupplier.supplier_email).length > 0 ? (
                    <div className="supplier-info-email-chips-list-wrapper">
                      <div className="supplier-info-email-chips-list">
                        {splitEmails(currentSupplier.supplier_email).map((email) => (
                          <button
                            key={email}
                            type="button"
                            className="supplier-info-email-chip supplier-info-email-chip-readonly"
                            onClick={() => copyToClipboard(email, 'Email')}
                            title={`Copiar ${email}`}
                          >
                            <span>{email}</span>
                          </button>
                        ))}
                      </div>
                      <button
                        type="button"
                        className="supplier-info-copy-all-btn"
                        onClick={copyAllEmails}
                        title="Copiar todos os emails"
                      >
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                          <rect x="4" y="8" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.6" fill="none" />
                          <rect x="10" y="4" width="10" height="10" rx="2" stroke="currentColor" strokeWidth="1.6" fill="none" />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <span className="supplier-info-email-placeholder">-</span>
                  )}
                </div>
              </div>
            </div>
            </div>
          
            <div className="supplier-info-responsibles">
            <div className="supplier-info-section-title">Responsáveis Cummins</div>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <i className="bi bi-arrow-repeat spin"></i> Carregando...
              </div>
            ) : (
              <div className="responsibles-grid">
                {/* Planner */}
                <div className="responsible-card">
                  <span className="responsible-label">
                    <i className="bi bi-person-badge"></i>
                    Planner
                  </span>
                  {isEditing ? (
                    <div className="supplier-info-inline-select-wrapper">
                      <select
                        className="supplier-info-inline-select"
                        value={formData.planner || ''}
                        onChange={(e) => handleInputChange('planner', e.target.value)}
                      >
                        <option value="">-</option>
                        {plannerList.map((item) => (
                          <option key={item.name} value={item.name}>{item.name}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down"></i>
                    </div>
                  ) : (
                    <div className="responsible-name">{planner?.name || '-'}</div>
                  )}
                  <div className="responsible-divider"></div>
                  <div className="responsible-info">
                    <div>
                      <i className="bi bi-envelope"></i>
                      <span>{planner?.email || '-'}</span>
                    </div>
                    <div>
                      <i className="bi bi-at"></i>
                      <span>{planner?.alias || '-'}</span>
                    </div>
                  </div>
                </div>

                {/* Continuity */}
                <div className="responsible-card">
                  <span className="responsible-label">
                    <i className="bi bi-lightning-charge"></i>
                    Continuity
                  </span>
                  {isEditing ? (
                    <div className="supplier-info-inline-select-wrapper">
                      <select
                        className="supplier-info-inline-select"
                        value={formData.continuity || ''}
                        onChange={(e) => handleInputChange('continuity', e.target.value)}
                      >
                        <option value="">-</option>
                        {continuityList.map((item) => (
                          <option key={item.name} value={item.name}>{item.name}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down"></i>
                    </div>
                  ) : (
                    <div className="responsible-name">{continuity?.name || '-'}</div>
                  )}
                  <div className="responsible-divider"></div>
                  <div className="responsible-info">
                    <div>
                      <i className="bi bi-envelope"></i>
                      <span>{continuity?.email || '-'}</span>
                    </div>
                    <div>
                      <i className="bi bi-at"></i>
                      <span>{continuity?.alias || '-'}</span>
                    </div>
                  </div>
                </div>

                {/* Sourcing */}
                <div className="responsible-card">
                  <span className="responsible-label">
                    <i className="bi bi-cart"></i>
                    Sourcing
                  </span>
                  {isEditing ? (
                    <div className="supplier-info-inline-select-wrapper">
                      <select
                        className="supplier-info-inline-select"
                        value={formData.sourcing || ''}
                        onChange={(e) => handleInputChange('sourcing', e.target.value)}
                      >
                        <option value="">-</option>
                        {sourcingList.map((item) => (
                          <option key={item.name} value={item.name}>{item.name}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down"></i>
                    </div>
                  ) : (
                    <div className="responsible-name">{sourcing?.name || '-'}</div>
                  )}
                  <div className="responsible-divider"></div>
                  <div className="responsible-info">
                    <div>
                      <i className="bi bi-envelope"></i>
                      <span>{sourcing?.email || '-'}</span>
                    </div>
                    <div>
                      <i className="bi bi-at"></i>
                      <span>{sourcing?.alias || '-'}</span>
                    </div>
                  </div>
                </div>

                {/* SQIE */}
                <div className="responsible-card">
                  <span className="responsible-label">
                    <i className="bi bi-patch-check"></i>
                    SQIE
                  </span>
                  {isEditing ? (
                    <div className="supplier-info-inline-select-wrapper">
                      <select
                        className="supplier-info-inline-select"
                        value={formData.sqie || ''}
                        onChange={(e) => handleInputChange('sqie', e.target.value)}
                      >
                        <option value="">-</option>
                        {sqieList.map((item) => (
                          <option key={item.name} value={item.name}>{item.name}</option>
                        ))}
                      </select>
                      <i className="bi bi-chevron-down"></i>
                    </div>
                  ) : (
                    <div className="responsible-name">{sqie?.name || '-'}</div>
                  )}
                  <div className="responsible-divider"></div>
                  <div className="responsible-info">
                    <div>
                      <i className="bi bi-envelope"></i>
                      <span>{sqie?.email || '-'}</span>
                    </div>
                    <div>
                      <i className="bi bi-at"></i>
                      <span>{sqie?.alias || '-'}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            </div>
          </div>
        </div>
      </div>
  </>
  );
};

export default SupplierInfoModal;
