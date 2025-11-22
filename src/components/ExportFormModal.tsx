import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { Download, X } from 'lucide-react';
import { useToastContext } from '../contexts/ToastContext';
import './ExportFormModal.css';

interface ExportFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (criteria: string, includeScore: boolean, month?: string, year?: string) => void;
}

const ExportFormModal: React.FC<ExportFormModalProps> = ({ isOpen, onClose, onExport }) => {
  const { showToast } = useToastContext();
  const [selectedCriteria, setSelectedCriteria] = useState<string>('otif');
  const [selectedMonth, setSelectedMonth] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [userPermissions, setUserPermissions] = useState<{otif: string, nil: string, pickup: string, package: string}>({otif: '', nil: '', pickup: '', package: ''});

  const isPermissionActive = (permission: string): boolean => {
    return permission === 'Sim' || permission === 'Yes' || permission === '1' || permission === 'true' || permission === 'read' || permission === 'write';
  };

  // Buscar permissões do usuário
  useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        const permissions = {
          otif: user.permissions?.otif || '',
          nil: user.permissions?.nil || '',
          pickup: user.permissions?.pickup || '',
          package: user.permissions?.package || ''
        };
        console.log('🔑 Permissões carregadas:', permissions);
        setUserPermissions(permissions);
        
        // Define o primeiro critério disponível como selecionado
        if (permissions.otif !== '') setSelectedCriteria('otif');
        else if (permissions.nil !== '') setSelectedCriteria('nil');
        else if (permissions.pickup !== '') setSelectedCriteria('pickup');
        else if (permissions.package !== '') setSelectedCriteria('package');
      } catch (error) {
        console.error('Erro ao parsear usuário:', error);
      }
    }
  }, []);

  // Reseta os campos quando o modal fecha e define mês/ano atual quando abre
  useEffect(() => {
    if (!isOpen) {
      setSelectedCriteria('otif');
      setSelectedMonth('');
      setSelectedYear('');
      setIsExporting(false);
    } else {
      // Define mês e ano atual quando o modal abre
      const today = new Date();
      setSelectedMonth(String(today.getMonth() + 1));
      setSelectedYear(String(today.getFullYear()));
    }
  }, [isOpen]);

  const handleExport = async () => {
    if (!selectedMonth || !selectedYear) {
      showToast('Por favor, selecione o mês e ano.', 'warning');
      return;
    }

    setIsExporting(true);
    try {
      await onExport(selectedCriteria, true, selectedMonth, selectedYear);
    } finally {
      setIsExporting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="modal-overlay" onClick={onClose} />
      <div className="export-form-modal" onClick={(e) => e.stopPropagation()}>
        <div className="export-form-header">
          <h2>
            <Download size={24} />
            Exportar Formulário
          </h2>
          <button 
            className="close-modal-btn"
            onClick={onClose}
            disabled={isExporting}
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="export-form-content">
          <p className="export-form-description">
            Exporte um formulário com os dados dos fornecedores e um campo para preenchimento de notas.
          </p>

          {/* Seletor de Critério */}
          <div className="form-group">
            <label htmlFor="criteria-select">Critério de Avaliação</label>
            <select 
              id="criteria-select"
              value={selectedCriteria}
              onChange={(e) => setSelectedCriteria(e.target.value)}
              disabled={isExporting}
              className="form-select"
            >
              {isPermissionActive(userPermissions.otif) && <option value="otif">OTIF</option>}
              {isPermissionActive(userPermissions.nil) && <option value="nil">NIL</option>}
              {isPermissionActive(userPermissions.pickup) && <option value="pickup">Pickup</option>}
              {isPermissionActive(userPermissions.package) && <option value="package">Package</option>}
            </select>
          </div>

          {/* Seletores de Mês e Ano */}
          <div className="date-selectors">
            <div className="form-group half-width">
              <label htmlFor="month-select">Mês</label>
              <select 
                id="month-select"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                disabled={isExporting}
                className="form-select"
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

            <div className="form-group half-width">
              <label htmlFor="year-select">Ano</label>
              <select 
                id="year-select"
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
                disabled={isExporting}
                className="form-select"
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

          {/* Informações do que será exportado */}
          <div className="export-info">
            <i className="bi bi-info-circle"></i>
            <div className="export-info-content">
              <strong>O arquivo conterá:</strong>
              <ul>
                <li>Record ID (se existir)</li>
                <li>Supplier ID</li>
                <li>Vendor Name</li>
                <li>BU</li>
                <li>Supplier PO</li>
                <li>Coluna para nota de {selectedCriteria.toUpperCase()}</li>
                {selectedMonth && selectedYear && (
                  <li className="highlight">
                    Notas existentes de {getMonthName(selectedMonth)}/{selectedYear}
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>

        <div className="export-form-footer">
          <button 
            className="btn-cancel"
            onClick={(e) => {
              e.stopPropagation();
              if (!isExporting) onClose();
            }}
            disabled={isExporting}
          >
            Cancelar
          </button>
          <button 
            className="btn-export"
            onClick={(e) => {
              e.stopPropagation();
              handleExport();
            }}
            disabled={isExporting || !selectedMonth || !selectedYear}
          >
            {isExporting ? (
              <>
                <i className="bi bi-arrow-repeat spinning-icon"></i>
                Exportando...
              </>
            ) : (
              <>
                <Download size={18} />
                Exportar
              </>
            )}
          </button>
        </div>
      </div>
    </>
  );
};

const getMonthName = (month: string): string => {
  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];
  return months[parseInt(month) - 1] || month;
};

export default ExportFormModal;
