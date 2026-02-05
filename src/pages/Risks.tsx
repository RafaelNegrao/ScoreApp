import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { TrendingUp, TrendingDown, BarChart3 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { BarChart, Bar, ReferenceLine, ResponsiveContainer, Cell, XAxis, YAxis } from "recharts";
import ActionsModal from "../components/ActionsModal";
import "../pages/Page.css";
import "./Score.css";
import "./Risks.css";
import { useMemo } from "react";

interface RiskSupplier {
  supplier_id: string;
  ssid: string | null;
  vendor_name: string;
  bu: string | null;
  country?: string | null;
  po: string | null;
  avg_score: number;
  q1: number | null;
  q2: number | null;
  q3: number | null;
  q4: number | null;
  monthly_scores?: (number | null)[];
  worst_metric_label?: string | null;
  worst_metric_value?: number | null;
  metric_averages?: {
    otif: number | null;
    nil: number | null;
    pickup: number | null;
    package: number | null;
  };
  metric_impacts?: {
    otif: number;
    nil: number;
    pickup: number;
    package: number;
  };
}

interface ActionItem {
  id: string;
  text: string;
  createdAt: string;
  done: boolean;
}

interface ScoreRecord {
  supplier_id: string;
  month: number;
  year: string;
  otif: number | null;
  nil: number | null;
  quality_pickup: number | null;
  quality_package: number | null;
  total_score?: number | null;
}

/**
 * Página de Risks.
 * Lista fornecedores com média abaixo da meta e exibe scores por trimestre.
 */
function Risks() {
  const [suppliers, setSuppliers] = useState<RiskSupplier[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedYear, setSelectedYear] = useState(() => {
    const saved = localStorage.getItem('risksSelectedYear');
    const parsed = saved ? Number(saved) : NaN;
    return Number.isFinite(parsed) ? parsed : new Date().getFullYear();
  });
  const [target, setTarget] = useState(8.7);
  const [criteriaWeights, setCriteriaWeights] = useState({
    otif: 0.25,
    nil: 0.25,
    pickup: 0.25,
    package: 0.25,
  });
  const [hoveredQuarter, setHoveredQuarter] = useState<{supplierId: string, quarter: string} | null>(null);
  const [actionsModalOpen, setActionsModalOpen] = useState(false);
  const [actionsSupplier, setActionsSupplier] = useState<RiskSupplier | null>(null);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [actionsVersion, setActionsVersion] = useState(0);
  const navigate = useNavigate();

  // Carregar target do banco ao montar o componente
  useEffect(() => {
    const loadTarget = async () => {
      try {
        const targetValue = await invoke<number>("get_target");
        console.log('🎯 Target carregado:', targetValue);
        setTarget(targetValue);
      } catch (error) {
        console.error("Erro ao carregar target:", error);
        // Mantém o valor padrão 8.7 em caso de erro
      }
    };
    loadTarget();
  }, []);

  useEffect(() => {
    const loadCriteria = async () => {
      try {
        const criteria = await invoke<any[]>("get_criteria");
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

  useEffect(() => {
    loadSuppliersAtRisk();
  }, [selectedYear, target]);

  useEffect(() => {
    localStorage.setItem('risksSelectedYear', String(selectedYear));
  }, [selectedYear]);

  const loadSuppliersAtRisk = async () => {
    setLoading(true);
    try {
      const data = await invoke<RiskSupplier[]>("get_suppliers_at_risk", {
        year: selectedYear,
        target: target,
      });
      console.log('📊 Fornecedores em risco carregados:', data);
      
      // Função auxiliar para calcular total_score de um record
      // Mesma lógica do MetricsOverview - média simples dos critérios disponíveis
      const calculateTotalScore = (record: ScoreRecord): number | null => {
        if (record.total_score !== null && record.total_score !== undefined && Number.isFinite(record.total_score)) {
          return record.total_score;
        }

        const scores: number[] = [];
        
        // Nota 0 é válida e deve ser incluída!
        if (record.otif !== null && record.otif !== undefined && !isNaN(record.otif)) {
          scores.push(record.otif);
        }
        if (record.nil !== null && record.nil !== undefined && !isNaN(record.nil)) {
          scores.push(record.nil);
        }
        if (record.quality_pickup !== null && record.quality_pickup !== undefined && !isNaN(record.quality_pickup)) {
          scores.push(record.quality_pickup);
        }
        if (record.quality_package !== null && record.quality_package !== undefined && !isNaN(record.quality_package)) {
          scores.push(record.quality_package);
        }
        
        if (scores.length === 0) return null;
        return scores.reduce((a, b) => a + b, 0) / scores.length;
      };
      
      // Buscar dados mensais para cada fornecedor e recalcular quarters
      const suppliersWithMonthly = await Promise.all(
        data.map(async (supplier) => {
          try {
            const records = await invoke<ScoreRecord[]>("get_supplier_score_records", {
              supplierId: supplier.supplier_id,
            });
            
            // Filtrar pelo ano selecionado
            const yearRecords = records.filter((r) => r.year === selectedYear.toString());
            
            // Criar array de 12 meses
            const monthlyScores: (number | null)[] = Array(12).fill(null);
            yearRecords.forEach((record) => {
              // month já vem como número do backend
              const monthIndex = record.month - 1;
              const score = calculateTotalScore(record);
              if (monthIndex >= 0 && monthIndex < 12 && score !== null) {
                monthlyScores[monthIndex] = score;
              }
            });

            const averageFromRecords = (values: Array<number | null | undefined>): number | null => {
              const valid = values.filter((value): value is number => value !== null && value !== undefined && !isNaN(value));
              if (valid.length === 0) return null;
              return valid.reduce((a, b) => a + b, 0) / valid.length;
            };

            const metricAverages = {
              otif: averageFromRecords(yearRecords.map((record) => record.otif)),
              nil: averageFromRecords(yearRecords.map((record) => record.nil)),
              pickup: averageFromRecords(yearRecords.map((record) => record.quality_pickup)),
              package: averageFromRecords(yearRecords.map((record) => record.quality_package)),
            };

            const worstMetricCandidates = [
              { label: 'OTIF', value: metricAverages.otif },
              { label: 'NIL', value: metricAverages.nil },
              { label: 'PICKUP', value: metricAverages.pickup },
              { label: 'PACKAGE', value: metricAverages.package },
            ].filter((metric) => metric.value !== null);

            const deficitTotals = {
              otif: Math.max(0, (target - (metricAverages.otif ?? 0))) * criteriaWeights.otif,
              nil: Math.max(0, (target - (metricAverages.nil ?? 0))) * criteriaWeights.nil,
              pickup: Math.max(0, (target - (metricAverages.pickup ?? 0))) * criteriaWeights.pickup,
              package: Math.max(0, (target - (metricAverages.package ?? 0))) * criteriaWeights.package,
            };
            const totalDeficit = Object.values(deficitTotals).reduce((sum, value) => sum + value, 0);
            const metricImpacts = {
              otif: totalDeficit > 0 ? deficitTotals.otif / totalDeficit : 0,
              nil: totalDeficit > 0 ? deficitTotals.nil / totalDeficit : 0,
              pickup: totalDeficit > 0 ? deficitTotals.pickup / totalDeficit : 0,
              package: totalDeficit > 0 ? deficitTotals.package / totalDeficit : 0,
            };

            const worstMetric = worstMetricCandidates.reduce<
              { label: string; value: number } | null
            >((currentWorst, metric) => {
              if (metric.value === null) return currentWorst;
              if (!currentWorst || metric.value < currentWorst.value) {
                return { label: metric.label, value: metric.value };
              }
              return currentWorst;
            }, null);
            
            // Calcular médias trimestrais (mesma lógica do MetricsOverview)
            const getQuarterAverage = (startMonth: number, endMonth: number): number | null => {
              const quarterScores = monthlyScores
                .slice(startMonth - 1, endMonth)
                .filter((s): s is number => s !== null);
              
              if (quarterScores.length === 0) return null;
              return quarterScores.reduce((a, b) => a + b, 0) / quarterScores.length;
            };
            
            const q1 = getQuarterAverage(1, 3);   // Jan-Mar
            const q2 = getQuarterAverage(4, 6);   // Apr-Jun
            const q3 = getQuarterAverage(7, 9);   // Jul-Sep
            const q4 = getQuarterAverage(10, 12); // Oct-Dec
            
            // Recalcular avg_score com base nos quarters disponíveis
            const quarterScores = [q1, q2, q3, q4].filter((s): s is number => s !== null);
            const recalculatedAvg = quarterScores.length > 0
              ? quarterScores.reduce((a, b) => a + b, 0) / quarterScores.length
              : supplier.avg_score;
            
            return { 
              ...supplier, 
              monthly_scores: monthlyScores,
              q1,
              q2,
              q3,
              q4,
              avg_score: recalculatedAvg,
              worst_metric_label: worstMetric?.label ?? null,
              worst_metric_value: worstMetric?.value ?? null,
              metric_averages: metricAverages,
              metric_impacts: metricImpacts
            };
          } catch (error) {
            console.error(`Erro ao buscar dados mensais para ${supplier.supplier_id}:`, error);
            return { ...supplier, monthly_scores: Array(12).fill(null) };
          }
        })
      );
      
      const filteredSuppliers = suppliersWithMonthly.filter((supplier) => {
        const avg = supplier.avg_score;
        return Number.isFinite(avg) && avg < target;
      });

      setSuppliers(filteredSuppliers);
    } catch (error) {
      console.error("Erro ao carregar fornecedores em risco:", error);
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  };

  const getQuarterTrend = (current: number | null, previous: number | null) => {
    if (current === null || previous === null) return null;
    return current > previous ? "up" : "down";
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return "var(--text-muted)";
    if (score >= target) return "var(--accent-primary)"; // Vermelho Cummins
    if (score >= target - 1) return "var(--text-warning)";
    return "var(--text-error)";
  };

  const handleViewTimeline = (supplier: RiskSupplier) => {
    // Navegar para Timeline e passar o supplier_id e o ano selecionado
    navigate('/timeline', { state: { supplierId: supplier.supplier_id, supplier, year: selectedYear } });
  };

  const getActionsKey = (supplierId: string) => `riskActions:${supplierId}`;

  const loadActions = (supplierId: string) => {
    const stored = localStorage.getItem(getActionsKey(supplierId));
    if (!stored) return [] as ActionItem[];
    try {
      const parsed = JSON.parse(stored) as ActionItem[];
      return Array.isArray(parsed)
        ? parsed.map((action) => ({
            ...action,
            done: action.done ?? false,
          }))
        : [];
    } catch {
      return [] as ActionItem[];
    }
  };

  const openActionsModal = (supplier: RiskSupplier) => {
    setActionsSupplier(supplier);
    setActions(loadActions(supplier.supplier_id));
    setActionsModalOpen(true);
  };

  useEffect(() => {
    const handler = () => setActionsVersion((v) => v + 1);
    window.addEventListener('riskActionsChanged', handler as EventListener);
    return () => window.removeEventListener('riskActionsChanged', handler as EventListener);
  }, []);

  const handleAddAction = (text: string) => {
    if (!actionsSupplier) return;
    const newAction: ActionItem = {
      id: `${Date.now()}`,
      text,
      createdAt: new Date().toLocaleString('pt-BR'),
      done: false,
    };
    const updated = [newAction, ...actions];
    setActions(updated);
    localStorage.setItem(getActionsKey(actionsSupplier.supplier_id), JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent('riskActionsChanged', { detail: actionsSupplier.supplier_id }));
  };

  const handleToggleAction = (id: string, done: boolean) => {
    if (!actionsSupplier) return;
    const updated = actions.map((action) =>
      action.id === id ? { ...action, done } : action
    );
    setActions(updated);
    localStorage.setItem(getActionsKey(actionsSupplier.supplier_id), JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent('riskActionsChanged', { detail: actionsSupplier.supplier_id }));
  };

  const handleDeleteAction = (id: string) => {
    if (!actionsSupplier) return;
    const updated = actions.filter((action) => action.id !== id);
    setActions(updated);
    localStorage.setItem(getActionsKey(actionsSupplier.supplier_id), JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent('riskActionsChanged', { detail: actionsSupplier.supplier_id }));
  };

  const handleEditAction = (id: string, newText: string) => {
    if (!actionsSupplier) return;
    const updated = actions.map((action) => action.id === id ? { ...action, text: newText } : action);
    setActions(updated);
    localStorage.setItem(getActionsKey(actionsSupplier.supplier_id), JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent('riskActionsChanged', { detail: actionsSupplier.supplier_id }));
  };

  // Helper para renderizar valores de meta: mostra 'N/A' mas aplica classe para estilizar
  const renderMetaValue = (val?: string | null) => {
    const display = val || "N/A";
    return <span className={`meta-value ${display === 'N/A' ? 'na' : ''}`}>{display}</span>;
  };

  // Lista fixa de anos: 2025 até 2040
  const years = [2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040];

  return (
    <div className="page-container">

      {/* Header - Meta e Controles */}
      <div className="risk-page-header">
        {/* Seletor de Ano */}
        <div className="custom-select-wrapper">
          <select
            className="custom-select"
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
          <i className="bi bi-chevron-down select-icon"></i>
        </div>

        {/* Espaço flexível para empurrar o target para o canto oposto */}
        <div style={{ flex: 1 }} />

        {/* Card de Target no canto oposto */}
        <div className="risk-meta-badge">
          <i className="bi bi-bullseye"></i>
          <span>Meta: <strong>{target.toFixed(2)}</strong></span>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Carregando fornecedores em risco...</p>
        </div>
      )}

      {/* Supplier Cards Grid */}
      {!loading && (
        <div className="risk-cards-grid">
          {suppliers.length === 0 ? (
            <div className="no-results">
              <i className="bi bi-shield-check"></i>
              <p>Nenhum fornecedor abaixo da meta encontrado</p>
            </div>
          ) : (
            suppliers.map((supplier) => (
              <div key={supplier.supplier_id} className="risk-card">
                {/* Card Header */}
                <div className="risk-card-header">
                  <div className="risk-card-title-row">
                    <h3>{supplier.vendor_name.replace(/\.\.\./g, '')}</h3>
                      <div className="risk-card-actions">
                        <button 
                          className="chart-button"
                          onClick={() => handleViewTimeline(supplier)}
                          title="Ver Timeline"
                        >
                          <BarChart3 size={18} />
                        </button>
                        <button
                          className={`chart-button ${localStorage.getItem(`riskActions:${supplier.supplier_id}`) ? 'has-actions' : ''}`}
                          onClick={() => openActionsModal(supplier)}
                          title="Adicionar ações"
                        >
                          <i className="bi bi-list-check" style={{ fontSize: 18 }}></i>
                        </button>
                      </div>
                    <div className="risk-score-large" style={{ color: getScoreColor(supplier.avg_score) }}>
                      {supplier.avg_score.toFixed(2)}
                    </div>
                  </div>

                  <div className="risk-card-content">
                    <div className="risk-card-info-container">
                      <div className="risk-card-info-stacked">
                        <div className="meta-row"><span className="meta-label">BU:</span>{renderMetaValue(supplier.bu)}</div>
                        <div className="meta-row"><span className="meta-label">Origem:</span>{renderMetaValue(supplier.country ?? null)}</div>
                        <div className="meta-row"><span className="meta-label">PO:</span>{renderMetaValue(supplier.po)}</div>
                        <div className="meta-row"><span className="meta-label">SSID:</span>{renderMetaValue(supplier.ssid)}</div>
                        <div className="meta-row"><span className="meta-label">ID:</span><span className="meta-value">{supplier.supplier_id}</span></div>
                      </div>
                    </div>

                    {/* Mini Chart */}
                    <div className="risk-mini-chart">
                      <ResponsiveContainer width="100%" height={152}>
                        <BarChart 
                          data={
                            supplier.monthly_scores 
                              ? supplier.monthly_scores.map((score, index) => ({
                                  month: ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'][index],
                                  monthIndex: index,
                                  score: score
                                }))
                              : []
                          }
                          margin={{ top: 5, right: 5, left: 5, bottom: 18 }}
                        >
                          <XAxis 
                            dataKey="month"
                            interval={0}
                            tick={(props) => {
                              const { x, y, payload } = props;
                              const monthIndex = payload.index;
                              const quarter = Math.floor(monthIndex / 3) + 1;
                              const isHovered = hoveredQuarter?.supplierId === supplier.supplier_id && 
                                                hoveredQuarter?.quarter === `Q${quarter}`;
                              
                              return (
                                <text 
                                  x={x} 
                                  y={y + 4} 
                                  textAnchor="middle" 
                                  fill={isHovered ? 'var(--accent-primary)' : 'var(--text-muted)'} 
                                  fontSize={9}
                                >
                                  {payload.value}
                                </text>
                              );
                            }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis domain={[0, 10]} hide />
                          <ReferenceLine y={target} stroke="var(--target-line-color, rgba(234, 179, 8, 0.45))" strokeDasharray="3 3" strokeWidth={1} />
                          <Bar dataKey="score" radius={[2, 2, 0, 0]}>
                            {supplier.monthly_scores?.map((score, index) => {
                              // Determinar o quarter do mês
                              const quarter = Math.floor(index / 3) + 1;
                              const isHovered = hoveredQuarter?.supplierId === supplier.supplier_id && 
                                                hoveredQuarter?.quarter === `Q${quarter}`;
                              const baseOpacity = isHovered ? 0.8 : 0.5;
                              
                              return (
                                <Cell 
                                  key={`cell-${index}`} 
                                  fill={score !== null && score >= target 
                                    ? `rgba(34, 197, 94, ${baseOpacity})` 
                                    : `rgba(239, 68, 68, ${baseOpacity})`
                                  } 
                                />
                              );
                            })}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                <div className="risk-metric-container">
                  <div className="risk-metric-container-header">
                    <span>Impacto na média</span>
                    <i
                      className="bi bi-info-circle"
                      title="Mostra o quanto cada critério puxou o score para baixo (0 a 1)."
                    ></i>
                  </div>
                  <div className="risk-metric-bars">
                    {[
                      { label: 'OTIF', impact: supplier.metric_impacts?.otif ?? 0 },
                      { label: 'NIL', impact: supplier.metric_impacts?.nil ?? 0 },
                      { label: 'PICKUP', impact: supplier.metric_impacts?.pickup ?? 0 },
                      { label: 'PACKAGE', impact: supplier.metric_impacts?.package ?? 0 },
                    ].map((metric) => {
                      const normalized = Math.min(1, Math.max(0, metric.impact));
                      const maxImpact = Math.max(
                        supplier.metric_impacts?.otif ?? 0,
                        supplier.metric_impacts?.nil ?? 0,
                        supplier.metric_impacts?.pickup ?? 0,
                        supplier.metric_impacts?.package ?? 0
                      );
                      const isImpactful = normalized === maxImpact && maxImpact > 0;

                      return (
                        <div key={metric.label} className={`risk-metric-row ${isImpactful ? 'impactful' : ''}`}>
                          <span className="risk-metric-label">{metric.label}</span>
                          <div className="risk-metric-bar">
                            <div
                              className="risk-metric-fill"
                              style={{ width: `${normalized * 100}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>



                {/* Quarters */}
                <div className="risk-quarters">
                  {[
                    { label: "Q1", value: supplier.q1, prev: null },
                    { label: "Q2", value: supplier.q2, prev: supplier.q1 },
                    { label: "Q3", value: supplier.q3, prev: supplier.q2 },
                    { label: "Q4", value: supplier.q4, prev: supplier.q3 },
                  ].map((quarter) => {
                    const trend = getQuarterTrend(quarter.value, quarter.prev);
                    return (
                      <div 
                        key={quarter.label} 
                        className="risk-quarter"
                        onMouseEnter={() => setHoveredQuarter({supplierId: supplier.supplier_id, quarter: quarter.label})}
                        onMouseLeave={() => setHoveredQuarter(null)}
                      >
                        <span className="quarter-label">{quarter.label}</span>
                        <div className="quarter-value-row">
                          <span
                            className="quarter-value"
                            style={{ color: getScoreColor(quarter.value) }}
                          >
                            {quarter.value !== null ? quarter.value.toFixed(2) : "-"}
                          </span>
                          {trend === "up" && (
                            <TrendingUp size={12} className="trend-icon trend-up" />
                          )}
                          {trend === "down" && (
                            <TrendingDown size={12} className="trend-icon trend-down" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {actionsSupplier && (
        <ActionsModal
          isOpen={actionsModalOpen}
          onClose={() => setActionsModalOpen(false)}
          supplierName={actionsSupplier.vendor_name}
          actions={actions}
          onAddAction={handleAddAction}
          onToggleDone={handleToggleAction}
          onDeleteAction={handleDeleteAction}
          onEditAction={handleEditAction}
        />
      )}
    </div>
  );
}

export default Risks;
