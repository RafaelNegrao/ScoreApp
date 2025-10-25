import React, { useState, useEffect } from 'react';
import DeleteModal from '../utils/DeleteModal';
import { invoke } from '@tauri-apps/api/tauri';
import './LogsTable.css';

interface LogEntry {
  log_id: number;
  date: string;
  time: string;
  user: string;
  event: string;
  wwid: string;
  place: string;
  supplier: string | null;
  score_date: string | null;
  old_value: string | null;
  new_value: string | null;
}

const LogsTable: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteCode, setDeleteCode] = useState('');
  const [deleteInput, setDeleteInput] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);
  // Gera código aleatório de 5 letras maiúsculas
  function generateDeleteCode() {
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    let code = '';
    for (let i = 0; i < 5; i++) {
      code += letters.charAt(Math.floor(Math.random() * letters.length));
    }
    return code;
  }

  const openDeleteModal = () => {
    setDeleteCode(generateDeleteCode());
    setDeleteInput('');
    setShowDeleteModal(true);
  };

  const handleDeleteAllLogs = async () => {
    setDeleteLoading(true);
    try {
      await invoke('delete_all_logs');
      setShowDeleteModal(false);
      setDeleteInput('');
      loadLogs();
    } catch (err) {
      alert('Erro ao excluir logs: ' + err);
    } finally {
      setDeleteLoading(false);
    }
  };

  // Função para retornar ícone baseado no tipo de evento
  const getEventIcon = (event: string) => {
    const eventLower = event.toLowerCase();
    if (eventLower.includes('create')) return 'bi-plus-circle';
    if (eventLower.includes('update') || eventLower.includes('edit')) return 'bi-arrow-repeat';
    if (eventLower.includes('delete')) return 'bi-trash';
    if (eventLower.includes('login')) return 'bi-box-arrow-in-right';
    if (eventLower.includes('logout')) return 'bi-box-arrow-right';
    return 'bi-info-circle';
  };
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 50;

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await invoke<LogEntry[]>('get_all_logs');
      setLogs(data);
    } catch (error) {
      console.error('Erro ao carregar logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    const searchLower = searchTerm.toLowerCase();
    return (
      log.user.toLowerCase().includes(searchLower) ||
      log.event.toLowerCase().includes(searchLower) ||
      log.wwid.toLowerCase().includes(searchLower) ||
      log.place.toLowerCase().includes(searchLower) ||
      (log.supplier && log.supplier.toLowerCase().includes(searchLower)) ||
      (log.score_date && log.score_date.includes(searchLower))
    );
  });

  // Paginação
  const indexOfLastLog = currentPage * logsPerPage;
  const indexOfFirstLog = indexOfLastLog - logsPerPage;
  const currentLogs = filteredLogs.slice(indexOfFirstLog, indexOfLastLog);
  const totalPages = Math.ceil(filteredLogs.length / logsPerPage);

  const handlePageChange = (pageNumber: number) => {
    setCurrentPage(pageNumber);
  };

  const renderPagination = () => {
    const pages = [];
    const maxPagesToShow = 5;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
    
    if (endPage - startPage < maxPagesToShow - 1) {
      startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    if (startPage > 1) {
      pages.push(
        <button key="first" onClick={() => handlePageChange(1)} className="pagination-btn">
          1
        </button>
      );
      if (startPage > 2) {
        pages.push(<span key="dots1" className="pagination-dots">...</span>);
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`pagination-btn ${currentPage === i ? 'active' : ''}`}
        >
          {i}
        </button>
      );
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        pages.push(<span key="dots2" className="pagination-dots">...</span>);
      }
      pages.push(
        <button key="last" onClick={() => handlePageChange(totalPages)} className="pagination-btn">
          {totalPages}
        </button>
      );
    }

    return pages;
  };

  return (
    <div className="logs-table-container">

      <div className="logs-header">
        <h2>Registro de Atividades</h2>
        <div className="logs-controls">
          <input
            type="text"
            placeholder="Buscar em logs..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="logs-search"
          />
          <button className="logs-delete-btn" onClick={openDeleteModal} title="Excluir todos os logs">
            <i className="bi bi-trash"></i>
          </button>
        </div>
      </div>
      <DeleteModal
        isOpen={showDeleteModal}
        title="Excluir todos os logs?"
        description="Esta ação irá remover TODOS os registros da tabela de logs. Esta ação não pode ser desfeita."
        confirmationCode={deleteCode}
        userInput={deleteInput}
        onInputChange={setDeleteInput}
        onCancel={() => setShowDeleteModal(false)}
        onConfirm={handleDeleteAllLogs}
        confirmLabel={deleteLoading ? 'Excluindo...' : 'Excluir'}
        cancelLabel="Cancelar"
        disabled={deleteInput.toUpperCase() !== deleteCode || deleteLoading}
      />

      {loading ? (
        <div className="logs-loading">Carregando logs...</div>
      ) : (
        <>
          <div className="logs-table-wrapper">
            <table className="logs-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Data</th>
                  <th>Hora</th>
                  <th>Usuário</th>
                  <th>WWID</th>
                  <th>Evento</th>
                  <th>Campo</th>
                  <th>Fornecedor</th>
                  <th>Mês/Ano</th>
                  <th>Valor Anterior</th>
                  <th>Valor Novo</th>
                </tr>
              </thead>
              <tbody>
                {currentLogs.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="no-logs">
                      {searchTerm ? 'Nenhum log encontrado com os critérios de busca' : 'Nenhum log disponível'}
                    </td>
                  </tr>
                ) : (
                  currentLogs.map((log) => (
                    <tr key={log.log_id}>
                      <td>{log.log_id}</td>
                      <td>{log.date}</td>
                      <td>{log.time}</td>
                      <td>{log.user}</td>
                      <td>{log.wwid}</td>
                      <td>
                        <div className="event-cell">
                          <i className={`bi ${getEventIcon(log.event)} event-icon`}></i>
                          <span>{log.event}</span>
                        </div>
                      </td>
                      <td>{log.place}</td>
                      <td>{log.supplier || '—'}</td>
                      <td>{log.score_date || '—'}</td>
                      <td className="log-value">{log.old_value || '—'}</td>
                      <td className="log-value">{log.new_value || '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="logs-pagination">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="pagination-nav"
              >
                ← Anterior
              </button>
              
              {renderPagination()}
              
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="pagination-nav"
              >
                Próximo →
              </button>
            </div>
          )}

          <div className="logs-info">
            Mostrando {indexOfFirstLog + 1} - {Math.min(indexOfLastLog, filteredLogs.length)} de {filteredLogs.length} logs
          </div>
        </>
      )}
    </div>
  );
};

export default LogsTable;
