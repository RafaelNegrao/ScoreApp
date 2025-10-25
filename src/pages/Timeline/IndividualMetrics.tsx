import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Info, ChevronLeft, ChevronRight } from 'lucide-react';
import RegressionModal from '../../components/RegressionModal';
import './IndividualMetrics.css';

interface ScoreRecord {
  supplier_id: string;
  year: string;
  month: number;
  otif?: number;
  nil?: number;
  quality_pickup?: number;
  quality_package?: number;
}

interface IndividualMetricsProps {
  supplierId: string | null;
  selectedYear: string;
}

interface RegressionData {
  slope: number;
  intercept: number;
  r2: number;
  trend: 'Crescente' | 'Decrescente' | 'Estável';
  equation: string;
  monthsAnalyzed: number;
  averageScore: number;
  realVsPredicted: { month: string; real: number; predicted: number; difference: number }[];
}

const months = [
  'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
];

const IndividualMetrics: React.FC<IndividualMetricsProps> = ({ supplierId, selectedYear }) => {
  const [otifData, setOtifData] = useState<{ month: string; score: number }[]>([]);
  const [nilData, setNilData] = useState<{ month: string; score: number }[]>([]);
  const [pickupData, setPickupData] = useState<{ month: string; score: number }[]>([]);
  const [packageData, setPackageData] = useState<{ month: string; score: number }[]>([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [currentMetric, setCurrentMetric] = useState<string>('');
  const [currentRegression, setCurrentRegression] = useState<RegressionData | null>(null);
  const [isMobileCarousel, setIsMobileCarousel] = useState(false);
  const [isCompactCarousel, setIsCompactCarousel] = useState(false);
  const [currentCarouselIndex, setCurrentCarouselIndex] = useState(0);
  const [targetValue, setTargetValue] = useState<number | null>(null);
  const [zoomLevel, setZoomLevel] = useState(100);

  // Detectar zoom do sistema Windows
  useEffect(() => {
    const detectZoom = () => {
      const zoom = Math.round((window.outerWidth / window.innerWidth) * 100);
      console.log('Zoom detectado:', zoom, '%');
      setZoomLevel(zoom);
    };
    
    detectZoom();
    window.addEventListener('resize', detectZoom);
    
    return () => window.removeEventListener('resize', detectZoom);
  }, []);

  // Calcular altura do gráfico baseado no zoom e modo de exibição
  const getChartHeight = () => {
    console.log('Aplicando altura para zoom:', zoomLevel);
    // Se estiver no modo compacto (2 cards), aumenta a altura
    if (isCompactCarousel) {
      return 'clamp(200px, 28vh, 300px)';
    }
    if (zoomLevel >= 140) return 'clamp(130px, 16vh, 170px)';
    if (zoomLevel >= 120) return 'clamp(145px, 18vh, 190px)';
    return 'clamp(160px, 20vh, 220px)';
  };

  // Calcular tamanho de fonte baseado no zoom
  const getFontSize = () => {
    if (zoomLevel >= 140) return { axis: '8px', tooltip: '9px' };
    if (zoomLevel >= 120) return { axis: '9px', tooltip: '10px' };
    return { axis: '12px', tooltip: '13px' };
  };

  // Carrega o target da tabela criteria_table
  useEffect(() => {
    const loadTarget = async () => {
      try {
        const target = await invoke<number>('get_target');
        setTargetValue(target);
      } catch (e) {
        console.error('Erro ao carregar target:', e);
        setTargetValue(null);
      }
    };
    loadTarget();
  }, []);

  useEffect(() => {
    if (!supplierId) {
      setOtifData([]);
      setNilData([]);
      setPickupData([]);
      setPackageData([]);
      return;
    }
    loadData();
  }, [supplierId, selectedYear]);

  useEffect(() => {
    const detectMobile = () => {
      if (typeof window === 'undefined') {
        return;
      }
      const width = window.innerWidth;
      setIsMobileCarousel(width <= 920);
      // Modo compacto: mostra 2 cards quando a largura for menor que 1600px (para caber 4 gráficos confortavelmente)
      setIsCompactCarousel(width < 1600 && width > 920);
    };

    detectMobile();
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', detectMobile);
      return () => window.removeEventListener('resize', detectMobile);
    }
  }, []);

  useEffect(() => {
    setCurrentCarouselIndex(0);
  }, [supplierId, selectedYear, isMobileCarousel]);

  const calculateLinearRegression = (dataPoints: { month: string; score: number }[]): RegressionData => {
    // Filtra apenas pontos com score > 0
    const validPoints = dataPoints.filter(d => d.score > 0);
    const n = validPoints.length;

    if (n === 0) {
      return {
        slope: 0,
        intercept: 0,
        r2: 0,
        trend: 'Estável',
        equation: 'y = 0',
        monthsAnalyzed: 0,
        averageScore: 0,
        realVsPredicted: []
      };
    }

    // Converte meses para números (1-12)
    const points = validPoints.map((d, idx) => ({
      x: idx + 1,
      y: d.score,
      month: d.month
    }));

    // Calcula médias
    const sumX = points.reduce((sum, p) => sum + p.x, 0);
    const sumY = points.reduce((sum, p) => sum + p.y, 0);
    const meanX = sumX / n;
    const meanY = sumY / n;

    // Calcula slope (m) e intercept (b)
    const numerator = points.reduce((sum, p) => sum + (p.x - meanX) * (p.y - meanY), 0);
    const denominator = points.reduce((sum, p) => sum + Math.pow(p.x - meanX, 2), 0);
    const slope = denominator !== 0 ? numerator / denominator : 0;
    const intercept = meanY - slope * meanX;

    // Calcula R²
    const yPredicted = points.map(p => slope * p.x + intercept);
    const ssRes = points.reduce((sum, p, i) => sum + Math.pow(p.y - yPredicted[i], 2), 0);
    const ssTot = points.reduce((sum, p) => sum + Math.pow(p.y - meanY, 2), 0);
    const r2 = ssTot !== 0 ? 1 - (ssRes / ssTot) : 0;

    // Determina tendência
    let trend: 'Crescente' | 'Decrescente' | 'Estável' = 'Estável';
    if (Math.abs(slope) > 0.01) {
      trend = slope > 0 ? 'Crescente' : 'Decrescente';
    }

    // Formata equação
    const slopeStr = slope >= 0 ? `${slope.toFixed(2)}x` : `${slope.toFixed(2)}x`;
    const interceptStr = intercept >= 0 ? `+ ${intercept.toFixed(2)}` : `${intercept.toFixed(2)}`;
    const equation = `y = ${slopeStr} ${interceptStr}`;

    // Cria comparação real vs previsto
    const realVsPredicted = points.map((p, i) => ({
      month: p.month,
      real: p.y,
      predicted: yPredicted[i],
      difference: p.y - yPredicted[i]
    }));

    return {
      slope,
      intercept,
      r2: Math.max(0, r2), // Garante que R² não seja negativo
      trend,
      equation,
      monthsAnalyzed: n,
      averageScore: meanY,
      realVsPredicted
    };
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const records = await invoke<ScoreRecord[]>('get_supplier_score_records', { supplierId });
      console.log('📈 Individual Metrics - ALL Records:', records);
      console.log('📈 Individual Metrics - Supplier ID:', supplierId);
      console.log('📈 Individual Metrics - Selected Year:', selectedYear);
      
      // Processar dados para cada métrica
      const processMetric = (metricField: keyof ScoreRecord) => {
        return months.map((m, idx) => {
          const monthNumber = idx + 1; // Mês de 1 a 12
          // Busca registros que correspondem ao ano e mês específico
          const monthRecords = records.filter(r => r.year === selectedYear && r.month === monthNumber);
          
          const scores = monthRecords.map(r => r[metricField] as number).filter(s => s !== undefined && s !== null && s > 0);
          const avg = scores.length > 0 ? scores.reduce((sum, s) => sum + s, 0) / scores.length : 0;
          return { month: m, score: parseFloat(avg.toFixed(2)) };
        });
      };

      setOtifData(processMetric('otif'));
      setNilData(processMetric('nil'));
      setPickupData(processMetric('quality_pickup'));
      setPackageData(processMetric('quality_package'));
    } catch (error) {
      console.error('Erro ao carregar métricas individuais:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!supplierId) {
    return (
      <div className="empty-state">
        <i className="bi bi-grid-3x3" style={{ fontSize: '3rem', color: 'var(--text-muted)', opacity: 0.5 }}></i>
        <p style={{ fontSize: '0.95rem', fontWeight: 400, color: 'var(--text-muted)', opacity: 0.85 }}>
          Selecione um fornecedor para visualizar as métricas individuais
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner"></div>
        <p style={{ fontSize: '0.95rem', fontWeight: 400, color: 'var(--text-muted)', opacity: 0.85 }}>
          Carregando métricas...
        </p>
      </div>
    );
  }

  const renderChart = (data: { month: string; score: number }[], title: string, color: string) => {
    const regression = calculateLinearRegression(data);
    
    // Adiciona linha de tendência aos dados
    const dataWithTrend = data.map((item, index) => ({
      ...item,
      trend: parseFloat((regression.slope * (index + 1) + regression.intercept).toFixed(1))
    }));
    
    const handleOpenModal = () => {
      setCurrentMetric(title);
      setCurrentRegression(regression);
      setShowModal(true);
    };

    // Target dinâmico - mesmo valor para todas as métricas
    const targetLine = targetValue !== null ? data.map(d => ({ month: d.month, target: targetValue })) : [];
    return (
      <div className="metric-chart-card" key={title}>
        <div className="metric-chart-header">
          <h3 className="metric-chart-title">{title}</h3>
          <div className="metric-chart-info">
            <span className="metric-chart-label">Média:</span>
            <span className="metric-chart-value" style={{ color }}>
              {data.length > 0 ? (data.reduce((sum, d) => sum + d.score, 0) / data.filter(d => d.score > 0).length || 0).toFixed(1) : '0.0'}
            </span>
          </div>
        </div>
        <div style={{ width: '100%', height: getChartHeight(), boxSizing: 'border-box' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={dataWithTrend.map((d, i) => ({ ...d, target: targetLine[i]?.target }))} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="rgba(148, 163, 184, 0.15)" 
                vertical={true}
                horizontal={true}
              />
              <XAxis dataKey="month" stroke="var(--text-secondary)" style={{ fontSize: getFontSize().axis }} />
              <YAxis domain={[0, 10]} stroke="var(--text-secondary)" style={{ fontSize: getFontSize().axis }} />
              <Tooltip
                contentStyle={{
                  background: 'var(--card-bg)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '8px 12px'
                }}
                formatter={(value: any, name: string) => {
                  if (typeof value === 'number') {
                    return value.toFixed(1);
                  }
                  return value;
                }}
              />
              {/* Linha de Target */}
              {targetValue !== null && (
                <Line
                  type="monotone"
                  dataKey="target"
                  stroke="#FFD600"
                  strokeWidth={2}
                  dot={false}
                  legendType="none"
                  name="Target"
                  strokeDasharray="2 2"
                />
              )}
              {/* Linha de tendência da regressão */}
              <Line
                type="monotone"
                dataKey="trend"
                stroke={color}
                strokeWidth={1.5}
                strokeDasharray="5 5"
                dot={false}
                opacity={0.3}
                legendType="none"
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke={color}
                strokeWidth={2.5}
                dot={{ r: 4, stroke: color, strokeWidth: 2, fill: 'var(--card-bg)' }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Barra de Informações de Regressão */}
        <div className="regression-info-bar">
          <div className="regression-info-content">
            <div className="regression-info-item">
              <span className="regression-info-label">y={regression.slope.toFixed(2)}x{regression.intercept >= 0 ? '+' : ''}{regression.intercept.toFixed(1)}</span>
            </div>
            <div className="regression-info-item">
              <span className={`regression-trend ${regression.trend.toLowerCase()}`}>
                {regression.trend === 'Crescente' && '↗'}
                {regression.trend === 'Decrescente' && '↘'}
                {regression.trend === 'Estável' && '→'}
              </span>
            </div>
            <div className="regression-info-item">
              <span className="regression-info-label">R²={regression.r2.toFixed(2)}</span>
            </div>
          </div>
          <button className="regression-info-button" onClick={handleOpenModal}>
            <Info size={14} />
          </button>
        </div>
      </div>
    );
  };

  const metricsConfig = [
    { key: 'otif', title: 'OTIF', color: '#ff6b35', data: otifData },
    { key: 'nil', title: 'NIL', color: '#8b5cf6', data: nilData },
    { key: 'pickup', title: 'Quality Pickup', color: '#06b6d4', data: pickupData },
    { key: 'package', title: 'Quality Package', color: '#ec4899', data: packageData }
  ];

  const handlePrevMetric = () => {
    if (isCompactCarousel) {
      // Para modo compacto (2 cards), retrocede de 2 em 2
      setCurrentCarouselIndex(prev => {
        if (prev === 0) return metricsConfig.length - 2;
        return Math.max(0, prev - 2);
      });
    } else {
      // Para modo mobile (1 card), retrocede de 1 em 1
      setCurrentCarouselIndex(prev => (prev === 0 ? metricsConfig.length - 1 : prev - 1));
    }
  };

  const handleNextMetric = () => {
    if (isCompactCarousel) {
      // Para modo compacto (2 cards), avança de 2 em 2
      setCurrentCarouselIndex(prev => {
        if (prev >= metricsConfig.length - 2) return 0;
        return prev + 2;
      });
    } else {
      // Para modo mobile (1 card), avança de 1 em 1
      setCurrentCarouselIndex(prev => (prev === metricsConfig.length - 1 ? 0 : prev + 1));
    }
  };

  // Adicionar classe de zoom ao container
  const getZoomClass = () => {
    if (zoomLevel >= 140) return 'zoom-150';
    if (zoomLevel >= 120) return 'zoom-125';
    return 'zoom-100';
  };

  return (
    <>
      {isMobileCarousel ? (
        <div className="individual-metrics-carousel">
          <button
            type="button"
            className="individual-carousel-button prev"
            onClick={handlePrevMetric}
            aria-label="Métrica anterior"
          >
            <ChevronLeft size={18} />
          </button>

          <div className="individual-carousel-track">
            <div className="individual-carousel-slide" key={`mobile-${currentCarouselIndex}`}>
              {renderChart(
                metricsConfig[currentCarouselIndex].data,
                metricsConfig[currentCarouselIndex].title,
                metricsConfig[currentCarouselIndex].color
              )}
            </div>
          </div>

          <button
            type="button"
            className="individual-carousel-button next"
            onClick={handleNextMetric}
            aria-label="Próxima métrica"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      ) : isCompactCarousel ? (
        <div className="individual-metrics-compact-carousel">
          <button
            type="button"
            className="individual-carousel-button prev"
            onClick={handlePrevMetric}
            aria-label="Métrica anterior"
          >
            <ChevronLeft size={20} />
          </button>

          <div className="individual-compact-grid" key={`compact-${currentCarouselIndex}`}>
            {metricsConfig.slice(currentCarouselIndex, currentCarouselIndex + 2).map(metric => 
              renderChart(metric.data, metric.title, metric.color)
            )}
          </div>

          <button
            type="button"
            className="individual-carousel-button next"
            onClick={handleNextMetric}
            aria-label="Próxima métrica"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      ) : (
        <div className={`individual-metrics-container ${getZoomClass()}`}>
          {metricsConfig.map(metric => renderChart(metric.data, metric.title, metric.color))}
        </div>
      )}

      {(isMobileCarousel || isCompactCarousel) && (
        <div className="individual-carousel-indicators" role="tablist" aria-label="Métricas Individuais">
          {isCompactCarousel ? (
            // Modo compacto: 2 páginas (0-1, 2-3)
            Array.from({ length: 2 }).map((_, pageIndex) => (
              <button
                type="button"
                key={`page-${pageIndex}`}
                className={`individual-carousel-dot ${currentCarouselIndex === pageIndex * 2 ? 'active' : ''}`}
                onClick={() => setCurrentCarouselIndex(pageIndex * 2)}
                aria-label={`Exibir página ${pageIndex + 1}`}
                aria-selected={currentCarouselIndex === pageIndex * 2}
              />
            ))
          ) : (
            // Modo mobile: 4 páginas (uma para cada métrica)
            metricsConfig.map((metric, index) => (
              <button
                type="button"
                key={metric.key}
                className={`individual-carousel-dot ${index === currentCarouselIndex ? 'active' : ''}`}
                onClick={() => setCurrentCarouselIndex(index)}
                aria-label={`Exibir métrica ${metric.title}`}
                aria-selected={index === currentCarouselIndex}
              />
            ))
          )}
        </div>
      )}

      {/* Modal de Regressão */}
      {currentRegression && (
        <RegressionModal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          data={currentRegression}
          metricName={currentMetric}
        />
      )}
    </>
  );
};

export default IndividualMetrics;
