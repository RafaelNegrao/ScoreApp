import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import SupplierEditModal from './SupplierEditModal';
import { usePermissions } from '../contexts/PermissionsContext';
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

const SupplierInfoModal: React.FC<SupplierInfoModalProps> = ({ isOpen, supplier, onClose, onEdit }) => {
  const { permissions } = usePermissions();
  const [planner, setPlanner] = useState<ListItemThreeFields | null>(null);
  const [continuity, setContinuity] = useState<ListItemThreeFields | null>(null);
  const [sourcing, setSourcing] = useState<ListItemThreeFields | null>(null);
  const [sqie, setSqie] = useState<ListItemThreeFields | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [currentSupplier, setCurrentSupplier] = useState(supplier);
  const [allowSupplierEdit, setAllowSupplierEdit] = useState<boolean>(() => {
    return localStorage.getItem('allowSupplierEdit') === 'true';
  });

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

    setCurrentSupplier(supplier);

    const loadResponsibles = async () => {
      try {
        setLoading(true);

        // Carregar TODAS as listas de responsáveis
        const [plannerList, continuityList, sourcingList, sqieList] = await Promise.all([
          invoke<ListItemThreeFields[]>('get_planner_list'),
          invoke<ListItemThreeFields[]>('get_continuity_list'),
          invoke<ListItemThreeFields[]>('get_sourcing_list'),
          invoke<ListItemThreeFields[]>('get_sqie_list'),
        ]);

        // Buscar os responsáveis específicos do fornecedor pelos nomes
        const foundPlanner = plannerList.find(p => p.name === supplier.planner) || null;
        const foundContinuity = continuityList.find(c => c.name === supplier.continuity) || null;
        const foundSourcing = sourcingList.find(s => s.name === supplier.sourcing) || null;
        const foundSqie = sqieList.find(sq => sq.name === supplier.sqie) || null;

        setPlanner(foundPlanner);
        setContinuity(foundContinuity);
        setSourcing(foundSourcing);
        setSqie(foundSqie);

      } catch (error) {
        console.error('Erro ao carregar responsáveis:', error);
        // Em caso de erro, deixa tudo null
        setPlanner(null);
        setContinuity(null);
        setSourcing(null);
        setSqie(null);
      } finally {
        setLoading(false);
      }
    };

    loadResponsibles();
  }, [isOpen, supplier]);

  const handleOpenEditModal = () => {
    // Adicionar os responsáveis ao supplier antes de abrir o modal de edição
    const supplierWithResponsibles = {
      ...currentSupplier,
      planner: planner?.name || currentSupplier.planner || '',
      continuity: continuity?.name || currentSupplier.continuity || '',
      sourcing: sourcing?.name || currentSupplier.sourcing || '',
      sqie: sqie?.name || currentSupplier.sqie || ''
    };
    setCurrentSupplier(supplierWithResponsibles);
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
  };

  const handleSaveSupplier = async (updatedSupplier: any) => {
    setCurrentSupplier(updatedSupplier);
    
    // Recarregar os dados dos responsáveis após salvar
    try {
      const [plannerList, continuityList, sourcingList, sqieList] = await Promise.all([
        invoke<ListItemThreeFields[]>('get_planner_list'),
        invoke<ListItemThreeFields[]>('get_continuity_list'),
        invoke<ListItemThreeFields[]>('get_sourcing_list'),
        invoke<ListItemThreeFields[]>('get_sqie_list'),
      ]);

      const foundPlanner = plannerList.find(p => p.name === updatedSupplier.planner) || null;
      const foundContinuity = continuityList.find(c => c.name === updatedSupplier.continuity) || null;
      const foundSourcing = sourcingList.find(s => s.name === updatedSupplier.sourcing) || null;
      const foundSqie = sqieList.find(sq => sq.name === updatedSupplier.sqie) || null;

      setPlanner(foundPlanner);
      setContinuity(foundContinuity);
      setSourcing(foundSourcing);
      setSqie(foundSqie);
    } catch (error) {
      console.error('Erro ao recarregar responsáveis:', error);
    }
    
    if (onEdit) {
      onEdit();
    }
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Fecha o modal apenas se clicar no overlay, não no conteúdo
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen || !supplier) return null;

  return (
    <>
      <div className="supplier-info-modal-overlay" onClick={handleOverlayClick}>
        <div className="supplier-info-modal" onClick={(e) => e.stopPropagation()}>
          <div className="supplier-info-header">
            <span className="supplier-info-title">
              <i className="bi bi-buildings"></i> {currentSupplier.vendor_name}
            </span>
            <div className="supplier-info-header-actions">
              {(permissions.canManageSuppliers || allowSupplierEdit) && (
                <button className="supplier-info-edit" onClick={handleOpenEditModal} title="Editar">
                  <i className="bi bi-pencil"></i>
                </button>
              )}
              <button className="supplier-info-close" onClick={onClose}>
                <i className="bi bi-x-lg"></i>
              </button>
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
                  <span className="supplier-info-label">Categoria:</span>
                  <span className="supplier-info-value">{currentSupplier.supplier_category || '-'}</span>
                </div>
              </div>

              <div className="supplier-info-row">
                <div className="supplier-info-item">
                  <span className="supplier-info-label">BU:</span>
                  <span className="supplier-info-value">{currentSupplier.bu || currentSupplier.business_unit || '-'}</span>
                </div>
                <div className="supplier-info-item">
                  <span className="supplier-info-label">Origem:</span>
                  <span className="supplier-info-value">{currentSupplier.country || '-'}</span>
                </div>
              </div>

              <div className="supplier-info-row">
                <div className="supplier-info-item">
                  <span className="supplier-info-label">SSID:</span>
                  <span className="supplier-info-value">{currentSupplier.ssid || '-'}</span>
                </div>
                <div className="supplier-info-item">
                  <span className="supplier-info-label">PO:</span>
                  <span className="supplier-info-value">{currentSupplier.supplier_po || '-'}</span>
                </div>
              </div>

              <div className="supplier-info-row">
                <div className="supplier-info-item">
                  <span className="supplier-info-label">Status:</span>
                  <span className="supplier-info-value">{currentSupplier.supplier_status || '-'}</span>
                </div>
              </div>

              <div className="supplier-info-email">
                <span className="supplier-info-label supplier-info-email-label">Email</span>
                <div className="supplier-info-email-box">
                  {currentSupplier.supplier_email ? (
                    <span className="supplier-info-email-value">{currentSupplier.supplier_email}</span>
                  ) : (
                    <span className="supplier-info-email-placeholder">-</span>
                  )}
                </div>
              </div>
            </div>
            </div>
          
            <div className="supplier-info-responsibles">
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
                  <div className="responsible-name">{planner?.name || '-'}</div>
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
                  <div className="responsible-name">{continuity?.name || '-'}</div>
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
                  <div className="responsible-name">{sourcing?.name || '-'}</div>
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
                  <div className="responsible-name">{sqie?.name || '-'}</div>
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

    <SupplierEditModal
      isOpen={isEditModalOpen}
      supplier={currentSupplier}
      onClose={handleCloseEditModal}
      onSave={handleSaveSupplier}
    />
  </>
  );
};

export default SupplierInfoModal;
