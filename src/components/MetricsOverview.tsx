import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { TrendingUp, TrendingDown, Calendar, CalendarRange, CalendarCheck, ChevronLeft, ChevronRight } from 'lucide-react';
import './MetricsOverview.css';

interface MetricsOverviewProps {
  supplierId: string | null;
  selectedYear: string;
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

interface MetricsData {
  overallAverage: number | null;
  twelveMonthsAverage: number | null;
  yearAverage: number | null;
  q1Average: number | null;
  q2Average: number | null;
  q3Average: number | null;
  q4Average: number | null;
  q1Trend: 'up' | 'down' | 'neutral';
  q2Trend: 'up' | 'down' | 'neutral';
  q3Trend: 'up' | 'down' | 'neutral';
  q4Trend: 'up' | 'down' | 'neutral';
  metricImpacts: {
    otif: number;
    nil: number;
    pickup: number;
    package: number;
  };
}

const MetricsOverview: React.FC<MetricsOverviewProps> = ({ supplierId, selectedYear }) => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [target, setTarget] = useState(8.7);
  const [criteriaWeights, setCriteriaWeights] = useState({
    otif: 0.25,
    nil: 0.25,
    pickup: 0.25,
    package: 0.25,
  });

  // Detectar zoom do sistema Windows
  useEffect(() => {
    const detectZoom = () => {
      const zoom = Math.round((window.outerWidth / window.innerWidth) * 100);
      console.log('MetricsOverview - Zoom detectado:', zoom, '%');
      setZoomLevel(zoom);
    };
    
    detectZoom();
    window.addEventListener('resize', detectZoom);
    
    return () => window.removeEventListener('resize', detectZoom);
  }, []);

  useEffect(() => {
    if (!supplierId) {
      setMetrics(null);
      return;
    }

    loadMetrics();
  }, [supplierId, selectedYear, target, criteriaWeights.otif, criteriaWeights.nil, criteriaWeights.pickup, criteriaWeights.package]);

  useEffect(() => {
    const loadTargetAndCriteria = async () => {
      try {
        const targetValue = await invoke<number>('get_target');
        setTarget(targetValue);
      } catch (error) {
        console.error('Erro ao carregar target:', error);
      }

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

    loadTargetAndCriteria();
  }, []);

  const loadMetrics = async () => {
    if (!supplierId) return;

    setLoading(true);
    try {
      const records = await invoke<ScoreRecord[]>('get_supplier_score_records', {
        supplierId: supplierId
      });

      const calculatedMetrics = calculateMetrics(records, selectedYear);
      setMetrics(calculatedMetrics);
    } catch (error) {
  console.error('Erro ao carregar metrics:', error);
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  };

  const calculateMetrics = (records: ScoreRecord[], year: string): MetricsData => {
    // Função auxiliar para calcular total_score de um record
    // Mesma lógica do Risks.tsx - retorna null se não houver dados
    const calculateTotalScore = (record: ScoreRecord): number | null => {
      if (record.total_score !== null && record.total_score !== undefined && Number.isFinite(record.total_score)) {
        return record.total_score;
      }

      const scores: number[] = [];

      // Nota 0 é válida e deve ser incluída!
      if (record.otif !== null && record.otif !== undefined && !isNaN(record.otif)) scores.push(record.otif);
      if (record.nil !== null && record.nil !== undefined && !isNaN(record.nil)) scores.push(record.nil);
      if (record.quality_pickup !== null && record.quality_pickup !== undefined && !isNaN(record.quality_pickup)) scores.push(record.quality_pickup);
      if (record.quality_package !== null && record.quality_package !== undefined && !isNaN(record.quality_package)) scores.push(record.quality_package);

      if (scores.length === 0) return null;
      return scores.reduce((a, b) => a + b, 0) / scores.length;
    };

    // Usar cálculo baseado nos critérios individuais (mesma lógica do Risks)
    const getScore = (record: ScoreRecord): number | null => {
      return calculateTotalScore(record);
    };

    // Filtrar apenas registros com scores válidos
    const allScores = records.map(r => getScore(r)).filter((s): s is number => s !== null);
    
    // Overall Average (todos os dados)
    const overallAverage = allScores.length > 0
      ? allScores.reduce((a, b) => a + b, 0) / allScores.length
      : null;

    // Últimos 12 meses
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1; // getMonth() retorna 0-11
    const last12MonthsRecords = records.filter(r => {
      const recordYear = parseInt(r.year);
      const recordMonth = r.month;
      const monthsDiff = (currentYear - recordYear) * 12 + (currentMonth - recordMonth);
      return monthsDiff <= 12 && monthsDiff >= 0;
    });
    const last12MonthsScores = last12MonthsRecords.map(r => getScore(r)).filter((s): s is number => s !== null);
    const twelveMonthsAverage = last12MonthsScores.length > 0
      ? last12MonthsScores.reduce((a, b) => a + b, 0) / last12MonthsScores.length
      : null;

    // Year Average
    const yearRecords = year
      ? records.filter(r => r.year === year)
      : records;

    // Montar scores mensais (mesma lógica da aba Risks)
    const monthlyScores: (number | null)[] = Array(12).fill(null);
    yearRecords.forEach((record) => {
      const monthIndex = record.month - 1;
      const score = getScore(record);
      if (monthIndex >= 0 && monthIndex < 12 && score !== null) {
        monthlyScores[monthIndex] = score;
      }
    });

    // Calcular médias trimestrais com base nos meses disponíveis
    const getQuarterAverage = (quarter: number): number | null => {
      const startMonth = (quarter - 1) * 3;
      const endMonth = startMonth + 3;
      const quarterScores = monthlyScores
        .slice(startMonth, endMonth)
        .filter((s): s is number => s !== null);

      if (quarterScores.length === 0) return null;
      return quarterScores.reduce((a, b) => a + b, 0) / quarterScores.length;
    };

    const q1Average = getQuarterAverage(1);
    const q2Average = getQuarterAverage(2);
    const q3Average = getQuarterAverage(3);
    const q4Average = getQuarterAverage(4);

    // Buscar último quarter disponível do ano anterior para comparar com Q1
    const previousYear = year ? (parseInt(year) - 1).toString() : null;
    let lastQuarterPreviousYear: number | null = null;
    
    if (previousYear) {
      const previousYearRecords = records.filter(r => r.year === previousYear);
      const previousYearMonthlyScores: (number | null)[] = Array(12).fill(null);
      
      previousYearRecords.forEach((record) => {
        const monthIndex = record.month - 1;
        const score = getScore(record);
        if (monthIndex >= 0 && monthIndex < 12 && score !== null) {
          previousYearMonthlyScores[monthIndex] = score;
        }
      });
      
      // Calcular quarters do ano anterior
      const getPreviousYearQuarterAverage = (quarter: number): number | null => {
        const startMonth = (quarter - 1) * 3;
        const endMonth = startMonth + 3;
        const quarterScores = previousYearMonthlyScores
          .slice(startMonth, endMonth)
          .filter((s): s is number => s !== null);

        if (quarterScores.length === 0) return null;
        return quarterScores.reduce((a, b) => a + b, 0) / quarterScores.length;
      };
      
      // Pegar o último quarter disponível do ano anterior (Q4 -> Q3 -> Q2 -> Q1)
      const prevQ4 = getPreviousYearQuarterAverage(4);
      const prevQ3 = getPreviousYearQuarterAverage(3);
      const prevQ2 = getPreviousYearQuarterAverage(2);
      const prevQ1 = getPreviousYearQuarterAverage(1);
      
      lastQuarterPreviousYear = prevQ4 ?? prevQ3 ?? prevQ2 ?? prevQ1;
    }

    // Mesma lógica do Risks: média anual baseada nos trimestres disponíveis
    const yearQuarterScores = [q1Average, q2Average, q3Average, q4Average]
      .filter((s): s is number => s !== null);
    const yearAverage = yearQuarterScores.length > 0
      ? yearQuarterScores.reduce((a, b) => a + b, 0) / yearQuarterScores.length
      : null;

    // Calcular tendências (comparar com trimestre anterior)
    // Q1 compara com último quarter disponível do ano anterior
    const getTrend = (current: number | null, previous: number | null): 'up' | 'down' | 'neutral' => {
      if (current === null || previous === null) return 'neutral';
      if (previous === 0) return 'neutral';
      const diff = current - previous;
      if (Math.abs(diff) < 0.1) return 'neutral';
      return diff > 0 ? 'up' : 'down';
    };

    const safeFormat = (value: number | null): number | null => {
      if (value === null || isNaN(value) || !isFinite(value)) return null;
      return parseFloat(value.toFixed(2));
    };

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

    return {
      overallAverage: safeFormat(overallAverage),
      twelveMonthsAverage: safeFormat(twelveMonthsAverage),
      yearAverage: safeFormat(yearAverage),
      q1Average: safeFormat(q1Average),
      q2Average: safeFormat(q2Average),
      q3Average: safeFormat(q3Average),
      q4Average: safeFormat(q4Average),
      q1Trend: getTrend(q1Average, lastQuarterPreviousYear),
      q2Trend: getTrend(q2Average, q1Average),
      q3Trend: getTrend(q3Average, q2Average),
      q4Trend: getTrend(q4Average, q3Average),
      metricImpacts,
    };
  };

  const formatMetric = (value: number | null) => (value === null ? '-' : value.toFixed(2));

  const handlePrevCard = () => {
    setCurrentCardIndex((prev) => (prev === 0 ? 2 : prev - 1));
  };

  const handleNextCard = () => {
    setCurrentCardIndex((prev) => (prev === 2 ? 0 : prev + 1));
  };

  if (!supplierId) {
    return (
      <div className="metrics-empty-state">
        <i className="bi bi-bar-chart-fill" style={{ fontSize: '3rem', color: 'var(--text-muted)', opacity: 0.5 }}></i>
  <p>Selecione um fornecedor para visualizar as metrics</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="metrics-loading">
        <div className="spinner"></div>
  <p>Carregando metrics...</p>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="metrics-empty-state">
        <i className="bi bi-inbox" style={{ fontSize: '3rem', color: 'var(--text-muted)', opacity: 0.5 }}></i>
        <p>Nenhum dado disponível para este fornecedor</p>
      </div>
    );
  }

  return (
    <div className="metrics-overview">
      <div className="metrics-section">
        <h2 className="metrics-title">
          <i className="bi bi-bar-chart-fill"></i>
          Visão Geral das Metrics
        </h2>
        
        {/* Cards superiores - Médias gerais */}
        {zoomLevel >= 120 ? (
          // Modo Carousel para zoom >= 120%
          <div className="metrics-carousel-section">
            <button className="metrics-carousel-btn" onClick={handlePrevCard}>
              <ChevronLeft size={24} />
            </button>
            
            <div className="metrics-carousel-wrapper">
              <div className={`metrics-carousel-card metric-card ${currentCardIndex === 0 ? 'center' : currentCardIndex === 1 ? 'left' : 'right'}`}>
                <div className="metric-icon">
                  <i className="bi bi-bar-chart-fill"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-label">Overall Average</div>
                  <div className="metric-value">{formatMetric(metrics.overallAverage)}</div>
                  <div className="metric-description">Média Geral</div>
                </div>
              </div>

              <div className={`metrics-carousel-card metric-card ${currentCardIndex === 1 ? 'center' : currentCardIndex === 2 ? 'left' : 'right'}`}>
                <div className="metric-icon">
                  <CalendarRange size={24} />
                </div>
                <div className="metric-content">
                  <div className="metric-label">12 Months Avg</div>
                  <div className="metric-value">{formatMetric(metrics.twelveMonthsAverage)}</div>
                  <div className="metric-description">Últimos 12 meses</div>
                </div>
              </div>

              <div className={`metrics-carousel-card metric-card ${currentCardIndex === 2 ? 'center' : currentCardIndex === 0 ? 'left' : 'right'}`}>
                <div className="metric-icon">
                  <CalendarCheck size={24} />
                </div>
                <div className="metric-content">
                  <div className="metric-label">Year Average</div>
                  <div className="metric-value">{formatMetric(metrics.yearAverage)}</div>
                  <div className="metric-description">Média do ano</div>
                </div>
              </div>
            </div>
            
            <button className="metrics-carousel-btn" onClick={handleNextCard}>
              <ChevronRight size={24} />
            </button>
          </div>
        ) : (
          // Modo Grid normal
          <div className="metrics-top-cards">
            <div className="metric-card">
              <div className="metric-icon">
                <i className="bi bi-bar-chart-fill"></i>
              </div>
              <div className="metric-content">
                <div className="metric-label">Overall Average</div>
                <div className="metric-value">{formatMetric(metrics.overallAverage)}</div>
                <div className="metric-description">Média Geral</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">
                <CalendarRange size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-label">12 Months Avg</div>
                <div className="metric-value">{formatMetric(metrics.twelveMonthsAverage)}</div>
                <div className="metric-description">Últimos 12 meses</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">
                <CalendarCheck size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-label">Year Average</div>
                <div className="metric-value">{formatMetric(metrics.yearAverage)}</div>
                <div className="metric-description">Média do ano</div>
              </div>
            </div>
          </div>
        )}

  {/* Cards inferiores - Metrics trimestrais */}
        <div className="metrics-section-title">
          <h3>Metrics Trimestrais</h3>
        </div>

        <div className="metrics-quarterly-cards">
          <div className="quarterly-card">
            <div className="quarterly-header">
              <span className="quarter-label">Q1</span>
              {metrics.q1Trend === 'up' && <TrendingUp size={20} className="trend-icon trend-up" />}
              {metrics.q1Trend === 'down' && <TrendingDown size={20} className="trend-icon trend-down" />}
            </div>
            <div className="quarterly-value">{formatMetric(metrics.q1Average)}</div>
            <div className="quarterly-period">Jan - Mar</div>
          </div>

          <div className="quarterly-card">
            <div className="quarterly-header">
              <span className="quarter-label">Q2</span>
              {metrics.q2Trend === 'up' && <TrendingUp size={20} className="trend-icon trend-up" />}
              {metrics.q2Trend === 'down' && <TrendingDown size={20} className="trend-icon trend-down" />}
            </div>
            <div className="quarterly-value">{formatMetric(metrics.q2Average)}</div>
            <div className="quarterly-period">Apr - Jun</div>
          </div>

          <div className="quarterly-card">
            <div className="quarterly-header">
              <span className="quarter-label">Q3</span>
              {metrics.q3Trend === 'up' && <TrendingUp size={20} className="trend-icon trend-up" />}
              {metrics.q3Trend === 'down' && <TrendingDown size={20} className="trend-icon trend-down" />}
            </div>
            <div className="quarterly-value">{formatMetric(metrics.q3Average)}</div>
            <div className="quarterly-period">Jul - Sep</div>
          </div>

          <div className="quarterly-card">
            <div className="quarterly-header">
              <span className="quarter-label">Q4</span>
              {metrics.q4Trend === 'up' && <TrendingUp size={20} className="trend-icon trend-up" />}
              {metrics.q4Trend === 'down' && <TrendingDown size={20} className="trend-icon trend-down" />}
            </div>
            <div className="quarterly-value">{formatMetric(metrics.q4Average)}</div>
            <div className="quarterly-period">Oct - Dec</div>
          </div>
        </div>

        <div className="metrics-section-title metrics-impact-title">
          <h3>Impacto na média</h3>
          <i
            className="bi bi-info-circle"
            title="Mostra o quanto cada critério puxou o score para baixo (0 a 1)."
          ></i>
        </div>
        <div className="metrics-impact-container">
          <div className="metrics-impact-bars">
            {[
              { label: 'OTIF', impact: metrics.metricImpacts.otif },
              { label: 'NIL', impact: metrics.metricImpacts.nil },
              { label: 'PICKUP', impact: metrics.metricImpacts.pickup },
              { label: 'PACKAGE', impact: metrics.metricImpacts.package },
            ].map((metric) => {
              const normalized = Math.min(1, Math.max(0, metric.impact));
              const maxImpact = Math.max(
                metrics.metricImpacts.otif,
                metrics.metricImpacts.nil,
                metrics.metricImpacts.pickup,
                metrics.metricImpacts.package
              );
              const isImpactful = normalized === maxImpact && maxImpact > 0;

              return (
                <div key={metric.label} className={`metrics-impact-row ${isImpactful ? 'impactful' : ''}`}>
                  <span className="metrics-impact-label">{metric.label}</span>
                  <div className="metrics-impact-bar">
                    <div
                      className="metrics-impact-fill"
                      style={{ width: `${normalized * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsOverview;
