import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Info } from 'lucide-react';
import RegressionModal from '../../components/RegressionModal';
import '../../components/RegressionModal.css';

interface ScoreRecord {
  supplier_id: string;
  year: string;
  month: number;
  otif?: number;
  nil?: number;
  quality_pickup?: number;
  quality_package?: number;
  total_score?: number;
}

interface PerformanceChartProps {
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
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

const PerformanceChart: React.FC<PerformanceChartProps> = ({ supplierId, selectedYear }) => {
  const [data, setData] = useState<{ month: string; score: number }[]>([]);
  const [loading, setLoading] = useState(false);
  const [regressionData, setRegressionData] = useState<RegressionData | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [target, setTarget] = useState<number | null>(null);

  // Carrega o target da tabela criteria_table
  useEffect(() => {
    const loadTarget = async () => {
      try {
        const targetVal = await invoke<number>('get_target');
        setTarget(targetVal);
      } catch (e) {
        console.error('Erro ao carregar target:', e);
        setTarget(null);
      }
    };
    loadTarget();
  }, []);

  useEffect(() => {
    if (!supplierId) {
      setData([]);
      setRegressionData(null);
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
      console.log('📊 Performance Chart - ALL Records:', records);
      console.log('📊 Performance Chart - Supplier ID:', supplierId);
      console.log('📊 Performance Chart - Selected Year:', selectedYear);
      
      // Filtra por ano e agrupa por mês
      const monthlyScores = months.map((m, idx) => {
        const monthNumber = idx + 1; // Mês de 1 a 12
        // Busca registros que correspondem ao ano e mês específico
        const monthRecords = records.filter(r => r.year === selectedYear && r.month === monthNumber);
        
        console.log(`📊 Mês ${monthNumber} (${m}):`, monthRecords.length, 'registros encontrados', monthRecords);
        
        // Usa o total_score diretamente
        if (monthRecords.length > 0) {
          const totalScores: number[] = [];
          monthRecords.forEach(r => {
            if (r.total_score !== undefined && r.total_score !== null) {
              totalScores.push(r.total_score);
            }
          });
          
          const avg = totalScores.length > 0 ? totalScores.reduce((sum, s) => sum + s, 0) / totalScores.length : 0;
          console.log(`📊 Mês ${monthNumber} (${m}) - Total Scores:`, totalScores, '| Média:', avg);
          return { month: m, score: parseFloat(avg.toFixed(1)) };
        }
        
        return { month: m, score: 0 };
      });
      
      console.log('📊 Performance Chart - Final Monthly Scores:', monthlyScores);
      setData(monthlyScores);
      
      // Calcula regressão linear
      const regression = calculateLinearRegression(monthlyScores);
      setRegressionData(regression);
      
      // Adiciona linha de tendência aos dados
      const dataWithTrend = monthlyScores.map((item, index) => ({
        ...item,
        trend: parseFloat((regression.slope * (index + 1) + regression.intercept).toFixed(1))
      }));
      setData(dataWithTrend);
    } catch (error) {
      console.error('❌ Erro ao carregar dados:', error);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  // Só renderiza se houver fornecedor
  if (!supplierId) {
    return (
      <div className="empty-state">
        <i className="bi bi-graph-up" style={{ fontSize: '3rem', color: 'var(--text-muted)', opacity: 0.5 }}></i>
        <p style={{ fontSize: '0.95rem', fontWeight: 400, color: 'var(--text-muted)', opacity: 0.85 }}>Selecione um fornecedor para visualizar o gráfico de performance</p>
      </div>
    );
  }

  return (
    <>
      <div className="metric-chart-card performance-chart-centered" style={{ 
        width: '100%', 
        maxWidth: '100%'
      }}>
        <div className="metric-chart-header">
          <h3 className="metric-chart-title">Performance</h3>
          <div className="metric-chart-info">
            <span className="metric-chart-label">Média:</span>
            <span className="metric-chart-value" style={{ color: 'var(--accent-primary)' }}>
              {data.length > 0 ? (data.reduce((sum, d) => sum + d.score, 0) / data.filter(d => d.score > 0).length || 0).toFixed(1) : '0.0'}
            </span>
          </div>
        </div>
        <div style={{ 
          width: '100%', 
          height: '100%',
          minHeight: 'clamp(240px, 30vh, 300px)',
          padding: '0 clamp(0.5rem, 2vw, 1.5rem)',
          boxSizing: 'border-box'
        }}>
          {loading ? (
            <div style={{ color: 'var(--text-secondary)' }}>Carregando...</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={target !== null ? data.map(d => ({ ...d, target })) : data} margin={{ top: 20, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="rgba(148, 163, 184, 0.15)" 
                  vertical={true}
                  horizontal={true}
                />
                <XAxis dataKey="month" stroke="var(--text-secondary)" style={{ fontSize: '14px' }} />
                <YAxis domain={[0, 10]} stroke="var(--text-secondary)" style={{ fontSize: '14px' }} />
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
                {target !== null && (
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
                {regressionData && (
                  <Line
                    type="monotone"
                    dataKey="trend"
                    stroke="var(--accent-primary)"
                    strokeWidth={1.5}
                    strokeDasharray="5 5"
                    dot={false}
                    opacity={0.4}
                    legendType="none"
                  />
                )}
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="var(--accent-primary)" 
                  strokeWidth={3} 
                  dot={{ r: 6, stroke: 'var(--accent-primary)', strokeWidth: 2, fill: 'var(--card-bg)' }}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Barra de Informações de Regressão */}
        {regressionData && (
          <div className="regression-info-bar">
            <div className="regression-info-content">
              <div className="regression-info-item">
                <span className="regression-info-label">y={regressionData.slope.toFixed(2)}x{regressionData.intercept >= 0 ? '+' : ''}{regressionData.intercept.toFixed(1)}</span>
              </div>
              <div className="regression-info-item">
                <span className={`regression-trend ${regressionData.trend.toLowerCase()}`}>
                  {regressionData.trend === 'Crescente' && '↗ Crescente'}
                  {regressionData.trend === 'Decrescente' && '↘ Decrescente'}
                  {regressionData.trend === 'Estável' && '→ Estável'}
                </span>
              </div>
              <div className="regression-info-item">
                <span className="regression-info-label">R²={regressionData.r2.toFixed(2)}</span>
              </div>
            </div>
            <button className="regression-info-button" onClick={() => setShowModal(true)}>
              <Info size={14} />
            </button>
          </div>
        )}
      </div>

      {/* Modal de Regressão */}
      {regressionData && (
        <RegressionModal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          data={regressionData}
          metricName="Performance"
        />
      )}
    </>
  );
};

export default PerformanceChart;
