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
  overallAverage: number;
  twelveMonthsAverage: number;
  yearAverage: number;
  q1Average: number;
  q2Average: number;
  q3Average: number;
  q4Average: number;
  q1Trend: 'up' | 'down' | 'neutral';
  q2Trend: 'up' | 'down' | 'neutral';
  q3Trend: 'up' | 'down' | 'neutral';
  q4Trend: 'up' | 'down' | 'neutral';
}

const MetricsOverview: React.FC<MetricsOverviewProps> = ({ supplierId, selectedYear }) => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);

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
  }, [supplierId, selectedYear]);

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
    // Usa a média simples dos 4 critérios disponíveis
    const calculateTotalScore = (record: ScoreRecord): number => {
      const scores: number[] = [];
      
      // Nota 0 é válida e deve ser incluída!
      if (record.otif !== null && record.otif !== undefined && !isNaN(record.otif)) scores.push(record.otif);
      if (record.nil !== null && record.nil !== undefined && !isNaN(record.nil)) scores.push(record.nil);
      if (record.quality_pickup !== null && record.quality_pickup !== undefined && !isNaN(record.quality_pickup)) scores.push(record.quality_pickup);
      if (record.quality_package !== null && record.quality_package !== undefined && !isNaN(record.quality_package)) scores.push(record.quality_package);
      
      if (scores.length === 0) return 0;
      return scores.reduce((a, b) => a + b, 0) / scores.length;
    };

    // Usar total_score do banco se disponível
    const getScore = (record: ScoreRecord): number => {
      if (record.total_score !== null && record.total_score !== undefined && !isNaN(record.total_score)) {
        return record.total_score;
      }
      return calculateTotalScore(record);
    };

    const allScores = records.map(r => getScore(r));
    
    // Overall Average (todos os dados)
    const overallAverage = allScores.length > 0
      ? allScores.reduce((a, b) => a + b, 0) / allScores.length
      : 0;

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
    const twelveMonthsAverage = last12MonthsRecords.length > 0
      ? last12MonthsRecords.reduce((sum, r) => sum + getScore(r), 0) / last12MonthsRecords.length
      : 0;

    // Year Average
    const yearRecords = year
      ? records.filter(r => r.year === year)
      : records;
    const yearAverage = yearRecords.length > 0
      ? yearRecords.reduce((sum, r) => sum + getScore(r), 0) / yearRecords.length
      : 0;

    // Calcular médias trimestrais
    const getQuarterRecords = (quarter: number) => {
      const startMonth = (quarter - 1) * 3 + 1;
      const endMonth = startMonth + 2;
      return yearRecords.filter(r => {
        return r.month >= startMonth && r.month <= endMonth;
      });
    };

    const q1Records = getQuarterRecords(1);
    const q2Records = getQuarterRecords(2);
    const q3Records = getQuarterRecords(3);
    const q4Records = getQuarterRecords(4);

    const q1Average = q1Records.length > 0
      ? q1Records.reduce((sum, r) => sum + getScore(r), 0) / q1Records.length
      : 0;
    const q2Average = q2Records.length > 0
      ? q2Records.reduce((sum, r) => sum + getScore(r), 0) / q2Records.length
      : 0;
    const q3Average = q3Records.length > 0
      ? q3Records.reduce((sum, r) => sum + getScore(r), 0) / q3Records.length
      : 0;
    const q4Average = q4Records.length > 0
      ? q4Records.reduce((sum, r) => sum + getScore(r), 0) / q4Records.length
      : 0;

    // Calcular tendências (comparar com trimestre anterior)
    const getTrend = (current: number, previous: number): 'up' | 'down' | 'neutral' => {
      if (previous === 0) return 'neutral';
      const diff = current - previous;
      if (Math.abs(diff) < 0.1) return 'neutral';
      return diff > 0 ? 'up' : 'down';
    };

    const safeFormat = (value: number): number => {
      if (isNaN(value) || !isFinite(value)) return 0;
      return parseFloat(value.toFixed(1));
    };

    return {
      overallAverage: safeFormat(overallAverage),
      twelveMonthsAverage: safeFormat(twelveMonthsAverage),
      yearAverage: safeFormat(yearAverage),
      q1Average: safeFormat(q1Average),
      q2Average: safeFormat(q2Average),
      q3Average: safeFormat(q3Average),
      q4Average: safeFormat(q4Average),
      q1Trend: getTrend(q1Average, yearAverage),
      q2Trend: getTrend(q2Average, q1Average),
      q3Trend: getTrend(q3Average, q2Average),
      q4Trend: getTrend(q4Average, q3Average),
    };
  };

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
                  <div className="metric-value">{metrics.overallAverage}</div>
                  <div className="metric-description">Média Geral</div>
                </div>
              </div>

              <div className={`metrics-carousel-card metric-card ${currentCardIndex === 1 ? 'center' : currentCardIndex === 2 ? 'left' : 'right'}`}>
                <div className="metric-icon">
                  <CalendarRange size={24} />
                </div>
                <div className="metric-content">
                  <div className="metric-label">12 Months Avg</div>
                  <div className="metric-value">{metrics.twelveMonthsAverage}</div>
                  <div className="metric-description">Últimos 12 meses</div>
                </div>
              </div>

              <div className={`metrics-carousel-card metric-card ${currentCardIndex === 2 ? 'center' : currentCardIndex === 0 ? 'left' : 'right'}`}>
                <div className="metric-icon">
                  <CalendarCheck size={24} />
                </div>
                <div className="metric-content">
                  <div className="metric-label">Year Average</div>
                  <div className="metric-value">{metrics.yearAverage}</div>
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
                <div className="metric-value">{metrics.overallAverage}</div>
                <div className="metric-description">Média Geral</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">
                <CalendarRange size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-label">12 Months Avg</div>
                <div className="metric-value">{metrics.twelveMonthsAverage}</div>
                <div className="metric-description">Últimos 12 meses</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">
                <CalendarCheck size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-label">Year Average</div>
                <div className="metric-value">{metrics.yearAverage}</div>
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
            <div className="quarterly-value">{metrics.q1Average}</div>
            <div className="quarterly-period">Jan - Mar</div>
          </div>

          <div className="quarterly-card">
            <div className="quarterly-header">
              <span className="quarter-label">Q2</span>
              {metrics.q2Trend === 'up' && <TrendingUp size={20} className="trend-icon trend-up" />}
              {metrics.q2Trend === 'down' && <TrendingDown size={20} className="trend-icon trend-down" />}
            </div>
            <div className="quarterly-value">{metrics.q2Average}</div>
            <div className="quarterly-period">Apr - Jun</div>
          </div>

          <div className="quarterly-card">
            <div className="quarterly-header">
              <span className="quarter-label">Q3</span>
              {metrics.q3Trend === 'up' && <TrendingUp size={20} className="trend-icon trend-up" />}
              {metrics.q3Trend === 'down' && <TrendingDown size={20} className="trend-icon trend-down" />}
            </div>
            <div className="quarterly-value">{metrics.q3Average}</div>
            <div className="quarterly-period">Jul - Sep</div>
          </div>

          <div className="quarterly-card">
            <div className="quarterly-header">
              <span className="quarter-label">Q4</span>
              {metrics.q4Trend === 'up' && <TrendingUp size={20} className="trend-icon trend-up" />}
              {metrics.q4Trend === 'down' && <TrendingDown size={20} className="trend-icon trend-down" />}
            </div>
            <div className="quarterly-value">{metrics.q4Average}</div>
            <div className="quarterly-period">Oct - Dec</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsOverview;
