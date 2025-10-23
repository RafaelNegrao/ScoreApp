import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Info } from 'lucide-react';
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

    return (
      <div className="metric-chart-card">
        <div className="metric-chart-header">
          <h3 className="metric-chart-title">{title}</h3>
          <div className="metric-chart-info">
            <span className="metric-chart-label">Média:</span>
            <span className="metric-chart-value" style={{ color }}>
              {data.length > 0 ? (data.reduce((sum, d) => sum + d.score, 0) / data.filter(d => d.score > 0).length || 0).toFixed(1) : '0.0'}
            </span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={dataWithTrend} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" opacity={0.3} />
            <XAxis dataKey="month" stroke="var(--text-secondary)" style={{ fontSize: '12px' }} />
            <YAxis domain={[0, 10]} stroke="var(--text-secondary)" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{
                background: 'var(--card-bg)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '8px 12px'
              }}
              formatter={(value: any) => {
                if (typeof value === 'number') {
                  return value.toFixed(1);
                }
                return value;
              }}
            />
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

  return (
    <>
      <div className="individual-metrics-container">
        {renderChart(otifData, 'OTIF', '#ff6b35')}
        {renderChart(nilData, 'NIL', '#8b5cf6')}
        {renderChart(pickupData, 'Quality Pickup', '#06b6d4')}
        {renderChart(packageData, 'Quality Package', '#ec4899')}
      </div>

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
