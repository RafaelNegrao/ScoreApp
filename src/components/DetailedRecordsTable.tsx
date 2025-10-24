import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { CommentModal } from './CommentModal';
import '../pages/Score.css';

interface MonthRecord {
  month: string;
  monthNumber: number;
  otif: number | null;
  nil: number | null;
  pickup: number | null;
  package: number | null;
  total: number | null;
  comment: string | null;
  hasData: boolean;
}

interface DetailedRecordsTableProps {
  supplierId: string;
  supplierName: string;
  selectedYear: string;
  userPermissions: any;
}

interface UserPermissions {
  otif: string;
  nil: string;
  pickup: string;
  package: string;
}

interface CriteriaWeights {
  otif: number;
  nil: number;
  pickup: number;
  package: number;
}

export const DetailedRecordsTable: React.FC<DetailedRecordsTableProps> = ({ 
  supplierId, 
  supplierName, 
  selectedYear,
  userPermissions 
}) => {
  const [records, setRecords] = useState<MonthRecord[]>([]);
  const [inputValues, setInputValues] = useState<Map<string, any>>(new Map());
  const [modifiedRows, setModifiedRows] = useState<Set<string>>(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [autoSave, setAutoSave] = useState(false);
  const [criteriaWeights, setCriteriaWeights] = useState<CriteriaWeights>({
    otif: 0.25,
    nil: 0.25,
    pickup: 0.25,
    package: 0.25,
  });
  const [permissions, setPermissions] = useState<UserPermissions>({
    otif: '',
    nil: '',
    pickup: '',
    package: '',
  });
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<{ monthNumber: number; monthName: string } | null>(null);

  // Carregar permissões do sessionStorage
  useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setPermissions({
          otif: user.permissions?.otif || '',
          nil: user.permissions?.nil || '',
          pickup: user.permissions?.pickup || '',
          package: user.permissions?.package || '',
        });
      } catch (error) {
        console.error('Erro ao parsear usuário:', error);
      }
    }
  }, []);

  // Carregar critérios
  useEffect(() => {
    const loadCriteria = async () => {
      try {
        const criteria = await invoke<any[]>('get_criteria');
        const weights: any = {};
        
        criteria.forEach((crit: any) => {
          const name = crit.criteria_name.toLowerCase();
          if (name.includes('package')) {
            weights.package = crit.criteria_weight;
          } else if (name.includes('pick')) {
            weights.pickup = crit.criteria_weight;
          } else if (name.includes('nil')) {
            weights.nil = crit.criteria_weight;
          } else if (name.includes('otif')) {
            weights.otif = crit.criteria_weight;
          }
        });

        setCriteriaWeights({
          otif: weights.otif || 0.25,
          nil: weights.nil || 0.25,
          pickup: weights.pickup || 0.25,
          package: weights.package || 0.25,
        });
      } catch (error) {
        console.error('Erro ao carregar critérios:', error);
      }
    };

    loadCriteria();
  }, []);

  // Carregar autoSave do localStorage
  useEffect(() => {
    const storedAutoSave = localStorage.getItem('autoSave');
    setAutoSave(storedAutoSave === null || storedAutoSave === 'true');

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'autoSave') {
        const newValue = e.newValue === null || e.newValue === 'true';
        setAutoSave(newValue);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // Carregar dados quando supplierId ou selectedYear mudarem - IGUAL AO SCORE.TSX
  useEffect(() => {
    const loadRecords = async () => {
      if (!supplierId || !selectedYear) return;

      try {
        const year = parseInt(selectedYear);
        const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
        const newInputValues = new Map<string, any>();
        const monthRecords: MonthRecord[] = [];
        
        // Carregar scores para cada mês do ano (IGUAL AO SCORE.TSX)
        for (let monthIdx = 0; monthIdx < 12; monthIdx++) {
          const monthNumber = monthIdx + 1;
          const monthName = months[monthIdx];
          
          try {
            const loadedScores = await invoke<any[]>('get_supplier_scores', {
              supplierIds: [supplierId],
              month: monthNumber,
              year: year,
            });

            if (loadedScores && loadedScores.length > 0) {
              const score = loadedScores[0];
              const rowKey = `${monthNumber}`;
              
              console.log(`📦 Mês ${monthNumber} - Score completo:`, JSON.stringify(score, null, 2));
              console.log(`📦 Campos disponíveis:`, Object.keys(score));
              
              // Extrair valores (IGUAL AO SCORE.TSX)
              const otif = score.otif_score || '';
              const nil = score.nil_score || '';
              const pickup = score.pickup_score || '';
              const pack = score.package_score || '';
              const total = score.total_score || '';
              const comment = score.comment || '';
              
              console.log(`💬 Comentário extraído: "${comment}"`);
              
              // Verificar se tem dados
              const hasData = otif !== '' || nil !== '' || pickup !== '' || pack !== '' || comment !== '';
              
              if (hasData) {
                // Inicializar inputValues (IGUAL AO SCORE.TSX)
                newInputValues.set(`${rowKey}-otif`, otif);
                newInputValues.set(`${rowKey}-nil`, nil);
                newInputValues.set(`${rowKey}-pickup`, pickup);
                newInputValues.set(`${rowKey}-package`, pack);
                newInputValues.set(`${rowKey}-comments`, comment);
                
                // Calcular total se não existir
                if (total) {
                  newInputValues.set(`${rowKey}-total`, total);
                } else {
                  const calculatedTotal = calculateTotalScore(monthNumber, newInputValues);
                  newInputValues.set(`${rowKey}-total`, calculatedTotal);
                }
                
                monthRecords.push({
                  month: `${monthName}/${selectedYear}`,
                  monthNumber,
                  otif: parseFloat(otif) || null,
                  nil: parseFloat(nil) || null,
                  pickup: parseFloat(pickup) || null,
                  package: parseFloat(pack) || null,
                  total: parseFloat(total) || null,
                  comment: comment || null,
                  hasData: true
                });
              }
            }
          } catch (error) {
            console.error(`Erro ao carregar mês ${monthNumber}:`, error);
          }
        }

        setRecords(monthRecords);
        setInputValues(newInputValues);
        
        console.log('📊 Dados carregados - Total de registros:', monthRecords.length);
        console.log('📝 InputValues após carregar:', Array.from(newInputValues.entries()).filter(([key]) => key.includes('comment')));
      } catch (error) {
        console.error('❌ Erro ao carregar dados:', error);
      }
    };

    loadRecords();
  }, [supplierId, selectedYear, criteriaWeights]);

  // Verifica se o usuário tem permissão para editar um campo específico
  const canEdit = (field: 'otif' | 'nil' | 'pickup' | 'package'): boolean => {
    const permission = permissions[field];
    return permission === 'Sim' || permission === 'sim' || permission === 'SIM' || permission === '1' || permission === 'true';
  };

  // Formata o valor para sempre ter uma casa decimal
  const formatScoreValue = (value: string): string => {
    if (!value || value.trim() === '') return '';
    
    const normalized = value.replace(',', '.');
    const numValue = parseFloat(normalized);
    
    if (isNaN(numValue)) return '';
    
    const clamped = Math.max(0, Math.min(10, numValue));
    
    return clamped.toFixed(1);
  };

  // Função para calcular o total score
  const calculateTotalScore = (monthNumber: number, values: Map<string, any>) => {
    const rowKey = `${monthNumber}`;
    const otif = parseFloat(values.get(`${rowKey}-otif`) || '0') || 0;
    const nil = parseFloat(values.get(`${rowKey}-nil`) || '0') || 0;
    const pickup = parseFloat(values.get(`${rowKey}-pickup`) || '0') || 0;
    const packageScore = parseFloat(values.get(`${rowKey}-package`) || '0') || 0;
    
    const total = 
      (otif * criteriaWeights.otif) +
      (nil * criteriaWeights.nil) +
      (pickup * criteriaWeights.pickup) +
      (packageScore * criteriaWeights.package);
    
    return total.toFixed(1);
  };

  // Função para salvar um score individual
  const saveScore = async (monthNumber: number, updatedValues?: Map<string, any>) => {
    if (!selectedYear || isSaving) return;
    
    try {
      setIsSaving(true);

      const storedUser = sessionStorage.getItem('user');
      const userName = storedUser ? JSON.parse(storedUser).user_name : 'Unknown';

      const month = monthNumber;
      const year = parseInt(selectedYear);

      // Usar valores atualizados se fornecidos, caso contrário usar inputValues
      const valuesToUse = updatedValues || inputValues;

      const rowKey = `${monthNumber}`;
      const otif = valuesToUse.get(`${rowKey}-otif`) || null;
      const nil = valuesToUse.get(`${rowKey}-nil`) || null;
      const pickup = valuesToUse.get(`${rowKey}-pickup`) || null;
      const packageScore = valuesToUse.get(`${rowKey}-package`) || null;
      const comments = valuesToUse.get(`${rowKey}-comments`) || null;
      const totalScore = calculateTotalScore(monthNumber, valuesToUse);

      console.log('💾 Salvando score:', { supplierId, month, year, otif, nil, pickup, packageScore, totalScore, comments });

      await invoke('save_supplier_score', {
        supplierId: supplierId,
        supplierName: supplierName,
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
        newSet.delete(`${monthNumber}`);
        return newSet;
      });
    } catch (error) {
      console.error('❌ Erro ao salvar score:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Função para abrir modal de comentário
  const openCommentModal = (monthNumber: number, monthName: string) => {
    const rowKey = `${monthNumber}`;
    const currentComment = inputValues.get(`${rowKey}-comments`) || '';
    console.log(`🔍 Abrindo modal para mês ${monthNumber}:`, {
      rowKey,
      comment: currentComment,
      allInputValues: Array.from(inputValues.entries())
    });
    setSelectedMonth({ monthNumber, monthName });
    setCommentModalOpen(true);
  };

  // Função para salvar comentário do modal
  const handleSaveComment = async (comment: string) => {
    if (!selectedMonth) return;
    
    const rowKey = `${selectedMonth.monthNumber}`;
    const newValues = new Map(inputValues);
    newValues.set(`${rowKey}-comments`, comment);
    
    console.log('💾 Salvando comentário:', { month: selectedMonth.monthNumber, comment });
    
    setInputValues(newValues);
    
    // SEMPRE salvar o comentário no banco quando o modal for salvo
    // Passar os valores atualizados diretamente para evitar problemas de timing
    try {
      await saveScore(selectedMonth.monthNumber, newValues);
      console.log('✅ Comentário salvo com sucesso!');
      
      // Remover da lista de modificados após salvar
      setModifiedRows(prev => {
        const newSet = new Set(prev);
        newSet.delete(rowKey);
        return newSet;
      });
    } catch (error) {
      console.error('❌ Erro ao salvar comentário:', error);
      // Se der erro, marcar como modificado para poder salvar depois
      setModifiedRows(prev => new Set(prev).add(rowKey));
    }
  };

  return (
    <>
      <CommentModal
        isOpen={commentModalOpen}
        onClose={() => setCommentModalOpen(false)}
        month={selectedMonth ? selectedMonth.monthName : ''}
        comment={selectedMonth ? (inputValues.get(`${selectedMonth.monthNumber}-comments`) || '') : ''}
        onSave={handleSaveComment}
      />
      
      <div className="table-container" style={{
      overflowX: 'auto',
      overflowY: 'auto',
      maxHeight: 'calc(100vh - 280px)',
      position: 'relative'
    }}>
      <table className="suppliers-table" style={{width:'100%'}}>
        <thead style={{
          position: 'sticky',
          top: 0,
          backgroundColor: 'var(--bg-primary)',
          zIndex: 100,
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <tr>
            <th style={{position: 'sticky', top: 0, backgroundColor: 'var(--bg-primary)'}}>Período</th>
            <th style={{position: 'sticky', top: 0, backgroundColor: 'var(--bg-primary)'}}>OTIF</th>
            <th style={{position: 'sticky', top: 0, backgroundColor: 'var(--bg-primary)'}}>NIL</th>
            <th style={{position: 'sticky', top: 0, backgroundColor: 'var(--bg-primary)'}}>Pickup</th>
            <th style={{position: 'sticky', top: 0, backgroundColor: 'var(--bg-primary)'}}>Package</th>
            <th style={{position: 'sticky', top: 0, backgroundColor: 'var(--bg-primary)'}}>Total</th>
            <th style={{position: 'sticky', top: 0, backgroundColor: 'var(--bg-primary)', width: '100px', textAlign: 'center'}}>Comentário</th>
            {!autoSave && <th style={{width: '60px', position: 'sticky', top: 0, backgroundColor: 'var(--bg-primary)'}}>Ações</th>}
          </tr>
        </thead>
        <tbody>
          {records.length === 0 ? (
            <tr>
              <td colSpan={!autoSave ? 8 : 7} style={{
                textAlign: 'center',
                padding: '2rem',
                color: 'var(--text-muted)',
                fontStyle: 'italic'
              }}>
                Nenhum dado disponível para o ano selecionado
              </td>
            </tr>
          ) : (
            records.map((rec) => {
              const rowKey = `${rec.monthNumber}`;
              
              return (
                <tr key={rec.month}>
                  <td>{rec.month}</td>
                  <td>
                  <input 
                    type="number" 
                    className={`score-input ${!canEdit('otif') ? 'readonly' : ''}`}
                    min="0" 
                    max="10" 
                    step="0.1"
                    value={inputValues.get(`${rowKey}-otif`) || ''}
                    readOnly={!canEdit('otif')}
                    disabled={!canEdit('otif')}
                    onChange={(e) => {
                      if (!canEdit('otif')) return;
                      let value = e.target.value;
                      const numValue = parseFloat(value);
                      if (numValue > 10) value = '10';
                      if (numValue < 0) value = '0';
                      const newValues = new Map(inputValues);
                      newValues.set(`${rowKey}-otif`, value);
                      
                      const totalScore = calculateTotalScore(rec.monthNumber, newValues);
                      newValues.set(`${rowKey}-total`, totalScore);
                      
                      setModifiedRows(prev => new Set(prev).add(rowKey));
                      
                      setInputValues(newValues);
                    }}
                    onBlur={(e) => {
                      if (!canEdit('otif')) return;
                      const formatted = formatScoreValue(e.target.value);
                      if (formatted !== '') {
                        const newValues = new Map(inputValues);
                        newValues.set(`${rowKey}-otif`, formatted);
                        
                        const totalScore = calculateTotalScore(rec.monthNumber, newValues);
                        newValues.set(`${rowKey}-total`, totalScore);
                        
                        setInputValues(newValues);
                      }
                      if (autoSave) {
                        saveScore(rec.monthNumber);
                      }
                    }}
                  />
                </td>
                <td>
                  <input 
                    type="number" 
                    className={`score-input ${!canEdit('nil') ? 'readonly' : ''}`}
                    min="0" 
                    max="10" 
                    step="0.1"
                    value={inputValues.get(`${rowKey}-nil`) || ''}
                    readOnly={!canEdit('nil')}
                    disabled={!canEdit('nil')}
                    onChange={(e) => {
                      if (!canEdit('nil')) return;
                      let value = e.target.value;
                      const numValue = parseFloat(value);
                      if (numValue > 10) value = '10';
                      if (numValue < 0) value = '0';
                      const newValues = new Map(inputValues);
                      newValues.set(`${rowKey}-nil`, value);
                      
                      const totalScore = calculateTotalScore(rec.monthNumber, newValues);
                      newValues.set(`${rowKey}-total`, totalScore);
                      
                      setModifiedRows(prev => new Set(prev).add(rowKey));
                      
                      setInputValues(newValues);
                    }}
                    onBlur={(e) => {
                      if (!canEdit('nil')) return;
                      const formatted = formatScoreValue(e.target.value);
                      if (formatted !== '') {
                        const newValues = new Map(inputValues);
                        newValues.set(`${rowKey}-nil`, formatted);
                        
                        const totalScore = calculateTotalScore(rec.monthNumber, newValues);
                        newValues.set(`${rowKey}-total`, totalScore);
                        
                        setInputValues(newValues);
                      }
                      if (autoSave) {
                        saveScore(rec.monthNumber);
                      }
                    }}
                  />
                </td>
                <td>
                  <input 
                    type="number" 
                    className={`score-input ${!canEdit('pickup') ? 'readonly' : ''}`}
                    min="0" 
                    max="10" 
                    step="0.1"
                    value={inputValues.get(`${rowKey}-pickup`) || ''}
                    readOnly={!canEdit('pickup')}
                    disabled={!canEdit('pickup')}
                    onChange={(e) => {
                      if (!canEdit('pickup')) return;
                      let value = e.target.value;
                      const numValue = parseFloat(value);
                      if (numValue > 10) value = '10';
                      if (numValue < 0) value = '0';
                      const newValues = new Map(inputValues);
                      newValues.set(`${rowKey}-pickup`, value);
                      
                      const totalScore = calculateTotalScore(rec.monthNumber, newValues);
                      newValues.set(`${rowKey}-total`, totalScore);
                      
                      setModifiedRows(prev => new Set(prev).add(rowKey));
                      
                      setInputValues(newValues);
                    }}
                    onBlur={(e) => {
                      if (!canEdit('pickup')) return;
                      const formatted = formatScoreValue(e.target.value);
                      if (formatted !== '') {
                        const newValues = new Map(inputValues);
                        newValues.set(`${rowKey}-pickup`, formatted);
                        
                        const totalScore = calculateTotalScore(rec.monthNumber, newValues);
                        newValues.set(`${rowKey}-total`, totalScore);
                        
                        setInputValues(newValues);
                      }
                      if (autoSave) {
                        saveScore(rec.monthNumber);
                      }
                    }}
                  />
                </td>
                <td>
                  <input 
                    type="number" 
                    className={`score-input ${!canEdit('package') ? 'readonly' : ''}`}
                    min="0" 
                    max="10" 
                    step="0.1"
                    value={inputValues.get(`${rowKey}-package`) || ''}
                    readOnly={!canEdit('package')}
                    disabled={!canEdit('package')}
                    onChange={(e) => {
                      if (!canEdit('package')) return;
                      let value = e.target.value;
                      const numValue = parseFloat(value);
                      if (numValue > 10) value = '10';
                      if (numValue < 0) value = '0';
                      const newValues = new Map(inputValues);
                      newValues.set(`${rowKey}-package`, value);
                      
                      const totalScore = calculateTotalScore(rec.monthNumber, newValues);
                      newValues.set(`${rowKey}-total`, totalScore);
                      
                      setModifiedRows(prev => new Set(prev).add(rowKey));
                      
                      setInputValues(newValues);
                    }}
                    onBlur={(e) => {
                      if (!canEdit('package')) return;
                      const formatted = formatScoreValue(e.target.value);
                      if (formatted !== '') {
                        const newValues = new Map(inputValues);
                        newValues.set(`${rowKey}-package`, formatted);
                        
                        const totalScore = calculateTotalScore(rec.monthNumber, newValues);
                        newValues.set(`${rowKey}-total`, totalScore);
                        
                        setInputValues(newValues);
                      }
                      if (autoSave) {
                        saveScore(rec.monthNumber);
                      }
                    }}
                  />
                </td>
                <td>
                  <b style={{color:'#3fa6ff'}}>
                    {inputValues.get(`${rowKey}-total`) || ''}
                  </b>
                </td>
                <td style={{textAlign: 'center'}}>
                  <button
                    onClick={() => openCommentModal(rec.monthNumber, rec.month)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '4px 8px',
                      fontSize: '1.1rem',
                      transition: 'all 0.2s',
                      color: inputValues.get(`${rowKey}-comments`) ? '#4ade80' : 'var(--text-muted)',
                      opacity: inputValues.get(`${rowKey}-comments`) ? 1 : 0.5
                    }}
                    title={inputValues.get(`${rowKey}-comments`) ? 'Ver/editar comentário' : 'Adicionar comentário'}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'scale(1.15)';
                      e.currentTarget.style.opacity = '1';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                      e.currentTarget.style.opacity = inputValues.get(`${rowKey}-comments`) ? '1' : '0.5';
                    }}
                  >
                    <i className="bi bi-chat-left-text-fill"></i>
                  </button>
                </td>
                {!autoSave && (
                  <td style={{textAlign: 'center'}}>
                    {modifiedRows.has(rowKey) && (
                      <button
                        className="save-button"
                        onClick={() => saveScore(rec.monthNumber)}
                        disabled={isSaving}
                        title="Salvar alterações"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: isSaving ? 'not-allowed' : 'pointer',
                          padding: '4px 8px',
                          color: '#3fa6ff',
                          fontSize: '1.2rem',
                          transition: 'all 0.2s',
                          opacity: isSaving ? 0.5 : 1
                        }}
                        onMouseEnter={(e) => {
                          if (!isSaving) {
                            e.currentTarget.style.transform = 'scale(1.1)';
                            e.currentTarget.style.color = '#5ab9ff';
                          }
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'scale(1)';
                          e.currentTarget.style.color = '#3fa6ff';
                        }}
                      >
                        <i className="bi bi-floppy" style={{pointerEvents: 'none'}}></i>
                      </button>
                    )}
                  </td>
                )}
              </tr>
            );
          })
          )}
        </tbody>
      </table>
    </div>
    </>
  );
};

export default DetailedRecordsTable;
