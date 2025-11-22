import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { open } from '@tauri-apps/api/dialog';
import { Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import { useToastContext } from '../contexts/ToastContext';
import './ImportScoreModal.css';

interface ImportScoreModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: () => void;
}

interface ValidationResult {
  valid: boolean;
  criteria: string;
  month: number;
  year: number;
  total_records: number;
  export_date: string;
  error?: string;
}

const ImportScoreModal: React.FC<ImportScoreModalProps> = ({ isOpen, onClose, onImportSuccess }) => {
  const { showToast } = useToastContext();
  const [selectedCriteria, setSelectedCriteria] = useState<string>('otif');
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [isImporting, setIsImporting] = useState<boolean>(false);
  const [importProgress, setImportProgress] = useState<number>(0);
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

  // Reseta os campos quando o modal fecha
  useEffect(() => {
    if (!isOpen) {
      setSelectedCriteria('otif');
      setSelectedFile('');
      setValidationResult(null);
      setIsValidating(false);
      setIsImporting(false);
    }
  }, [isOpen]);

  const handleFileSelect = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'Excel',
          extensions: ['xlsx']
        }]
      });

      if (selected && typeof selected === 'string') {
        setSelectedFile(selected);
        setValidationResult(null);
        
        // Valida automaticamente após selecionar o arquivo
        await validateFile(selected);
      }
    } catch (error) {
      console.error('Erro ao selecionar arquivo:', error);
    }
  };

  const validateFile = async (filePath: string) => {
    setIsValidating(true);
    try {
      console.log('🔍 Validando arquivo:', filePath, 'Critério:', selectedCriteria);
      
      const result = await invoke<ValidationResult>('validate_import_file', {
        filePath,
        expectedCriteria: selectedCriteria,
      });

      console.log('✅ Resultado da validação:', result);
      setValidationResult(result);
    } catch (error) {
      console.error('❌ Erro ao validar arquivo:', error);
      setValidationResult({
        valid: false,
        criteria: '',
        month: 0,
        year: 0,
        total_records: 0,
        export_date: '',
        error: String(error),
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleImport = async () => {
    if (!validationResult?.valid || !selectedFile) return;

    setIsImporting(true);
    setImportProgress(0);
    
    try {
      console.log('📥 Importando arquivo:', selectedFile);
      
      // Simula progresso enquanto importa
      const progressInterval = setInterval(() => {
        setImportProgress(prev => {
          if (prev >= 90) return prev;
          return prev + 10;
        });
      }, 200);

      const result = await invoke<string>('import_scores_from_file', {
        filePath: selectedFile,
        criteria: selectedCriteria,
      });

      clearInterval(progressInterval);
      setImportProgress(100);

      console.log('✅ Importação concluída com sucesso!');
      
      showToast(result || 'Notas importadas com sucesso!', 'success');
      
      // Chama o callback de sucesso mas NÃO fecha o modal
      onImportSuccess();
      
      // Reseta o estado após um tempo para permitir nova importação
      setTimeout(() => {
        setSelectedFile('');
        setValidationResult(null);
        setImportProgress(0);
      }, 2000);
      
    } catch (error) {
      console.error('❌ Erro ao importar:', error);
      showToast(`Erro ao importar notas: ${error}`, 'error');
      setImportProgress(0);
    } finally {
      setIsImporting(false);
    }
  };

  if (!isOpen) return null;

  const canImport = validationResult?.valid && !isValidating && !isImporting;

  return (
    <>
      <div className="modal-overlay" onClick={onClose} />
      <div className="import-score-modal" onClick={(e) => e.stopPropagation()}>
        <div className="import-score-header">
          <h2>
            <Upload size={24} />
            Importar Notas
          </h2>
          <button 
            className="close-modal-btn"
            onClick={onClose}
            disabled={isImporting}
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="import-score-content">
          <p className="import-score-description">
            Selecione o arquivo Excel com as notas preenchidas para importar.
          </p>

          {/* Seletor de Critério */}
          <div className="form-group">
            <label htmlFor="criteria-select">Critério de Avaliação</label>
            <select 
              id="criteria-select"
              value={selectedCriteria}
              onChange={(e) => {
                setSelectedCriteria(e.target.value);
                setValidationResult(null);
                // Revalida se já tem arquivo selecionado
                if (selectedFile) {
                  validateFile(selectedFile);
                }
              }}
              disabled={isImporting || isValidating}
              className="form-select"
            >
              {isPermissionActive(userPermissions.otif) && <option value="otif">OTIF</option>}
              {isPermissionActive(userPermissions.nil) && <option value="nil">NIL</option>}
              {isPermissionActive(userPermissions.pickup) && <option value="pickup">Pickup</option>}
              {isPermissionActive(userPermissions.package) && <option value="package">Package</option>}
            </select>
          </div>

          {/* Seletor de Arquivo */}
          <div className="form-group">
            <label>Arquivo Excel</label>
            <div className="file-select-container">
              <button
                className="btn-file-select"
                onClick={handleFileSelect}
                disabled={isImporting || isValidating}
              >
                <Upload size={18} />
                {selectedFile ? 'Alterar Arquivo' : 'Selecionar Arquivo'}
              </button>
              {selectedFile && (
                <span className="selected-file-name">
                  {selectedFile.split('\\').pop()}
                </span>
              )}
            </div>
          </div>

          {/* Status da Validação */}
          {isValidating && (
            <div className="validation-status validating">
              <i className="bi bi-arrow-repeat spinning-icon"></i>
              <span>Validando arquivo...</span>
            </div>
          )}

          {validationResult && !isValidating && (
            <div className={`validation-status ${validationResult.valid ? 'valid' : 'invalid'}`}>
              {validationResult.valid ? (
                <>
                  <CheckCircle size={20} />
                  <div className="validation-details">
                    <strong>Arquivo válido!</strong>
                    <ul>
                      <li>Critério: {validationResult.criteria.toUpperCase()}</li>
                      <li>Período: {validationResult.month}/{validationResult.year}</li>
                      <li>Total de registros: {validationResult.total_records}</li>
                      <li>Exportado em: {validationResult.export_date}</li>
                    </ul>
                  </div>
                </>
              ) : (
                <>
                  <AlertCircle size={20} />
                  <div className="validation-details">
                    <strong>Arquivo inválido</strong>
                    <p>{validationResult.error}</p>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Barra de Progresso */}
          {isImporting && (
            <div className="import-progress">
              <div className="import-progress-header">
                <span>Importando notas...</span>
                <span>{importProgress}%</span>
              </div>
              <div className="import-progress-bar">
                <div 
                  className="import-progress-fill" 
                  style={{ width: `${importProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Informações */}
          {!isImporting && (
            <div className="import-info">
              <i className="bi bi-info-circle"></i>
              <div className="import-info-content">
                <strong>Instruções:</strong>
                <ul>
                  <li>Selecione o critério que foi exportado</li>
                  <li>Escolha o arquivo Excel preenchido</li>
                  <li>O sistema validará automaticamente</li>
                  <li>Se válido, o botão de importar será habilitado</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="import-score-footer">
          <button 
            className="btn-cancel"
            onClick={(e) => {
              e.stopPropagation();
              if (!isImporting) onClose();
            }}
            disabled={isImporting}
          >
            Cancelar
          </button>
          <button 
            className="btn-import"
            onClick={(e) => {
              e.stopPropagation();
              handleImport();
            }}
            disabled={!canImport}
          >
            {isImporting ? (
              <>
                <i className="bi bi-arrow-repeat spinning-icon"></i>
                Importando...
              </>
            ) : (
              <>
                <Upload size={18} />
                Importar
              </>
            )}
          </button>
        </div>
      </div>
    </>
  );
};

export default ImportScoreModal;
