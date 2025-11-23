import React, { useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { open } from '@tauri-apps/api/dialog';
import { readBinaryFile } from '@tauri-apps/api/fs';
import './ImportSupplierModal.css';

interface ImportSupplierModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const ImportSupplierModal: React.FC<ImportSupplierModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message: string;
    details?: string[];
  } | null>(null);
  const [importResult, setImportResult] = useState<{
    success: boolean;
    message: string;
    updated?: number;
    inserted?: number;
    errors?: number;
  } | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  if (!isOpen) return null;

  const handleSelectFile = async () => {
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
        await validateFile(selected);
      }
    } catch (error) {
      console.error('Erro ao selecionar arquivo:', error);
      setValidationResult({
        valid: false,
        message: 'Erro ao selecionar arquivo: ' + error
      });
    }
  };

  const validateFile = async (filePath: string) => {
    setIsValidating(true);
    try {
      const fileContent = await readBinaryFile(filePath);
      const contentArray = Array.from(fileContent);
      
      const result = await invoke<string>('validate_supplier_import', {
        fileContent: contentArray
      });

      setValidationResult({
        valid: true,
        message: result
      });
    } catch (error: any) {
      setValidationResult({
        valid: false,
        message: error.toString()
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleImport = async () => {
    if (!selectedFile || !validationResult?.valid) return;

    setIsImporting(true);
    setImportResult(null);
    try {
      const fileContent = await readBinaryFile(selectedFile);
      const contentArray = Array.from(fileContent);
      
      const result = await invoke<string>('import_suppliers', {
        fileContent: contentArray
      });

      // Parse do resultado para extrair números
      const updatedMatch = result.match(/Atualizados:\s*(\d+)/i) || result.match(/(\d+)\s*suppliers?\s*atualizados?/i);
      const insertedMatch = result.match(/Inseridos:\s*(\d+)/i) || result.match(/(\d+)\s*inseridos?/i);
      const errorsMatch = result.match(/Erros:\s*(\d+)/i);

      const updated = updatedMatch ? parseInt(updatedMatch[1]) : 0;
      const inserted = insertedMatch ? parseInt(insertedMatch[1]) : 0;
      const errors = errorsMatch ? parseInt(errorsMatch[1]) : 0;

      setImportResult({
        success: true,
        message: result,
        updated,
        inserted,
        errors
      });

      onSuccess();
    } catch (error: any) {
      setImportResult({
        success: false,
        message: error.toString(),
        updated: 0,
        inserted: 0,
        errors: 0
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setValidationResult(null);
    setImportResult(null);
    setIsValidating(false);
    setIsImporting(false);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="import-supplier-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Importar Suppliers</h2>
          <button className="close-button" onClick={handleClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="file-selection">
            <button 
              className="select-file-button" 
              onClick={handleSelectFile}
              disabled={isValidating || isImporting}
            >
              Selecionar Arquivo Excel
            </button>
            {selectedFile && (
              <div className="selected-file">
                <span>{selectedFile.split('\\').pop()}</span>
              </div>
            )}
          </div>

          {isValidating && (
            <div className="validation-status validating">
              <div className="spinner"></div>
              <span>Validando arquivo...</span>
            </div>
          )}

          {validationResult && !importResult && (
            <div className={`validation-status ${validationResult.valid ? 'valid' : 'invalid'}`}>
              <div className="validation-message">
                <strong>{validationResult.valid ? 'Arquivo válido' : 'Arquivo inválido'}</strong>
                <p>{validationResult.message}</p>
                {validationResult.details && (
                  <ul>
                    {validationResult.details.map((detail, idx) => (
                      <li key={idx}>{detail}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {importResult && (
            <div className={`validation-status ${importResult.success ? 'valid' : 'invalid'}`}>
              <div className="validation-message">
                <strong>{importResult.success ? 'Importação Concluída' : 'Erro na Importação'}</strong>
                {importResult.success && (
                  <div className="import-results">
                    <div className="result-item">
                      <span className="result-label">Atualizados:</span>
                      <span className="result-value">{importResult.updated}</span>
                    </div>
                    <div className="result-item">
                      <span className="result-label">Inseridos:</span>
                      <span className="result-value">{importResult.inserted}</span>
                    </div>
                    {importResult.errors! > 0 && (
                      <div className="result-item error">
                        <span className="result-label">Erros:</span>
                        <span className="result-value">{importResult.errors}</span>
                      </div>
                    )}
                  </div>
                )}
                {!importResult.success && (
                  <p style={{ marginTop: '10px' }}>{importResult.message}</p>
                )}
              </div>
            </div>
          )}

          <div className="validation-info">
            <h3>Requisitos do arquivo:</h3>
            <ul>
              <li>Arquivo deve ser exportado pelo sistema</li>
              <li>Não alterar a estrutura das colunas</li>
              <li>Colunas esperadas: Supplier ID, Vendor Name, BU, Supplier PO, Origem, Supplier Status</li>
              <li>Aba de controle "_control" deve estar presente</li>
            </ul>
          </div>
        </div>

        <div className="modal-footer">
          {!importResult ? (
            <>
              <button className="cancel-button" onClick={handleClose} disabled={isImporting}>
                Cancelar
              </button>
              <button 
                className="import-button" 
                onClick={handleImport}
                disabled={!validationResult?.valid || isImporting}
              >
                {isImporting ? 'Importando...' : 'Importar'}
              </button>
            </>
          ) : (
            <button className="import-button" onClick={handleClose}>
              Fechar
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImportSupplierModal;
