import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
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
  carouselPage?: number;
  singleMetricIndex?: number;
  isSmallHeight?: boolean;
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

interface ChartDataPoint {
  month: string;
  score: number | null;
}

const months = [
  'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
];

const IndividualMetrics: React.FC<IndividualMetricsProps> = ({ supplierId, selectedYear, carouselPage = 0, singleMetricIndex, isSmallHeight = false }) => {
  const [otifData, setOtifData] = useState<ChartDataPoint[]>([]);
  const [nilData, setNilData] = useState<ChartDataPoint[]>([]);
  const [pickupData, setPickupData] = useState<ChartDataPoint[]>([]);
  const [packageData, setPackageData] = useState<ChartDataPoint[]>([]);
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
      return 'clamp(230px, 32vh, 350px)';
    }
    if (zoomLevel >= 140) return 'clamp(160px, 20vh, 210px)';
    if (zoomLevel >= 120) return 'clamp(180px, 22vh, 230px)';
    return 'clamp(200px, 24vh, 270px)';
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
      // Modo compacto: mostra 2 cards quando a largura for menor que 1000px
      setIsCompactCarousel(width < 1000 && width > 920);
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

  const calculateLinearRegression = (dataPoints: ChartDataPoint[]): RegressionData => {
    // Filtra apenas pontos com score válido (incluindo 0) e não-null
    const validPoints = dataPoints.filter(d => d.score !== null && d.score !== undefined && !isNaN(d.score as number));
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

    // Converte meses para números (1-12) e garante que score não seja null
    const points = validPoints.map((d, idx) => ({
      x: idx + 1,
      y: d.score as number, // Safe porque filtramos null acima
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
      const processMetric = (metricField: keyof ScoreRecord): ChartDataPoint[] => {
        return months.map((m, idx) => {
          const monthNumber = idx + 1; // Mês de 1 a 12
          // Busca registros que correspondem ao ano e mês específico
          const monthRecords = records.filter(r => r.year === selectedYear && r.month === monthNumber);
          
          const scores = monthRecords.map(r => r[metricField] as number).filter(s => s !== undefined && s !== null);
          if (scores.length > 0) {
            const avg = scores.reduce((sum, s) => sum + s, 0) / scores.length;
            return { month: m, score: parseFloat(avg.toFixed(2)) };
          }
          return { month: m, score: null };
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

  const renderChart = (data: ChartDataPoint[], title: string, color: string) => {
    const regression = calculateLinearRegression(data);
    
    const handleOpenModal = () => {
      setCurrentMetric(title);
      setCurrentRegression(regression);
      setShowModal(true);
    };

    return (
      <div className="metric-chart-card" key={title}>
        <div className="metric-chart-header">
          <h3 className="metric-chart-title">{title}</h3>
          <div className="metric-chart-info">
            <span className="metric-chart-label">Média:</span>
            <span className="metric-chart-value" style={{ color }}>
              {data.length > 0 ? (() => {
                const validData = data.filter(d => d.score !== null && d.score !== undefined && !isNaN(d.score as number));
                return validData.length > 0 ? (validData.reduce((sum, d) => sum + (d.score as number), 0) / validData.length).toFixed(1) : '0.0';
              })() : '0.0'}
            </span>
          </div>
        </div>
        <div style={{ width: '100%', height: getChartHeight(), boxSizing: 'border-box' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 25, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid 
                strokeDasharray="2 6" 
                stroke="rgba(148, 163, 184, 0.3)" 
                vertical={false}
                horizontal={true}
              />
              <XAxis dataKey="month" stroke="var(--text-secondary)" style={{ fontSize: getFontSize().axis }} />
              <YAxis
                domain={[0, 10]}
                ticks={[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
                allowDecimals={false}
                stroke="var(--text-secondary)"
                style={{ fontSize: getFontSize().axis }}
              />
              <Tooltip
                active={false}
                contentStyle={{
                  background: 'var(--card-bg)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '8px 12px'
                }}
                formatter={(value: any, name: string) => {
                  if (value === null || value === undefined) {
                    return 'Sem dados';
                  }
                  if (typeof value === 'number') {
                    return value.toFixed(1);
                  }
                  return value;
                }}
              />
              <Bar 
                dataKey="score" 
                radius={[4, 4, 0, 0]} 
                label={(props: any) => {
                  const { x, y, width, value } = props;
                  if (value === null || value === undefined) return null;
                  return (
                    <text 
                      x={x + width / 2} 
                      y={y - 5} 
                      fill="var(--text-secondary)" 
                      textAnchor="middle" 
                      fontSize={10}
                    >
                      {value.toFixed(1)}
                    </text>
                  );
                }}
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={
                      entry.score === null ? 'transparent' : 
                      entry.score === 0 ? '#fbbf24' : 
                      (targetValue !== null && entry.score < targetValue ? '#ef4444' : '#22c55e')
                    }
                  />
                ))}
              </Bar>
              {/* Linha de Target - renderizada após as barras para ficar sobreposta */}
              {targetValue !== null && (
                <ReferenceLine
                  y={targetValue}
                  stroke="var(--accent-primary)"
                  strokeWidth={2.5}
                  strokeDasharray="5 5"
                />
              )}
            </BarChart>
          </ResponsiveContainer>
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

  // Determinar quais métricas mostrar baseado na página do carousel
  const getVisibleMetrics = () => {
    // Modo de métrica única (carousel unificado)
    if (singleMetricIndex !== undefined) {
      return [metricsConfig[singleMetricIndex]];
    }
    if (carouselPage !== undefined) {
      if (isSmallHeight) {
        // Modo altura pequena: mostra 1 métrica por página
        return metricsConfig.slice(carouselPage, carouselPage + 1);
      } else {
        // Modo carousel normal: mostra 2 métricas por página
        const startIndex = carouselPage * 2;
        return metricsConfig.slice(startIndex, startIndex + 2);
      }
    }
    // Modo normal: mostra todas as 4 métricas
    return metricsConfig;
  };

  return (
    <>
      {singleMetricIndex !== undefined ? (
        // Modo de métrica única para carousel unificado
        renderChart(
          metricsConfig[singleMetricIndex].data,
          metricsConfig[singleMetricIndex].title,
          metricsConfig[singleMetricIndex].color
        )
      ) : isMobileCarousel ? (
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
          {getVisibleMetrics().map(metric => renderChart(metric.data, metric.title, metric.color))}
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
