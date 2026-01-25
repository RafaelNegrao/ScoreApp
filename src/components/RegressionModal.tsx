import { X } from 'lucide-react';
import './RegressionModal.css';

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

interface RegressionModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: RegressionData;
  metricName: string;
}

const RegressionModal: React.FC<RegressionModalProps> = ({ isOpen, onClose, data, metricName }) => {
  if (!isOpen) return null;

  const getRegressionQuality = (r2: number): string => {
    if (r2 >= 0.8) return 'Explicação forte';
    if (r2 >= 0.5) return 'Explicação moderada';
    if (r2 >= 0.3) return 'Explicação fraca';
    return 'Explicação muito fraca';
  };

  const getTrendColor = (trend: string): string => {
    if (trend === 'Crescente') return '#4ade80';
    if (trend === 'Decrescente') return '#f87171';
    return '#fbbf24';
  };

  return (
    <div className="regression-modal-overlay" onClick={onClose}>
      <div className="regression-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="regression-modal-header">
          <h2>
            <i className="bi bi-graph-up" style={{ marginRight: '8px' }}></i>
            Análise de Regressão Linear - {metricName}
          </h2>
          <button className="regression-modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="regression-modal-body">
          {/* Resumo */}
          <div className="regression-section">
            <h3>
              <i className="bi bi-arrow-right" style={{ marginRight: '8px' }}></i>
              Resumo:
            </h3>
            <p className="regression-summary" style={{ color: getTrendColor(data.trend) }}>
              Os scores estão <strong>{data.trend.toLowerCase()}</strong>
            </p>
          </div>

          {/* R² */}
          <div className="regression-section">
            <h3>R² (Coeficiente de Determinação): {(data.r2 * 100).toFixed(1)}%</h3>
            <p className="regression-explanation">
              <i className="bi bi-pencil" style={{ marginRight: '8px' }}></i>
              Mede o quanto a equação consegue explicar a variação dos dados
            </p>
            <p className="regression-note">A equação não explica quase nada da variação dos dados observados</p>
            
            <ul className="regression-list">
              <li>R² = 1 (100%) → a equação explica toda a variação</li>
              <li>R² = 0 (0%) → a equação não explica nada</li>
            </ul>

            <div className="regression-indicator">
              <p>Indicador de R²:</p>
              <div className="regression-bar">
                <div className="regression-bar-fill" style={{ width: `${data.r2 * 100}%` }}></div>
                <span className="regression-bar-value" style={{ left: `${data.r2 * 100}%` }}>{data.r2.toFixed(3)}</span>
              </div>
              <div className="regression-bar-labels">
                <span>0.0<br/>Nenhuma explicação</span>
                <span>0.25</span>
                <span>0.50</span>
                <span>0.75</span>
                <span>1.0<br/>Explicação perfeita</span>
              </div>
            </div>

            <p className="regression-quality">{getRegressionQuality(data.r2)}</p>
          </div>

          {/* Como funciona */}
          <div className="regression-section">
            <h3>
              <i className="bi bi-lightbulb" style={{ marginRight: '8px' }}></i>
              Como funciona:
            </h3>
            <p>Traçamos uma linha que passa o mais perto possível de todos os pontos.</p>
            <p>Essa linha mostra a direção geral dos scores.</p>
          </div>

          {/* Equação */}
          <div className="regression-section">
            <h3>
              <i className="bi bi-calculator" style={{ marginRight: '8px' }}></i>
              Equação da Linha de Tendência:
            </h3>
            <div className="regression-equation">
              {data.equation}
            </div>
            <p className="regression-where">Onde:</p>
            <ul className="regression-list">
              <li>y = score previsto</li>
              <li>x = período (mês)</li>
              <li>m = {data.slope.toFixed(3)} (inclinação da linha)</li>
              <li>b = {data.intercept.toFixed(2)} (ponto inicial)</li>
            </ul>
          </div>

          {/* Inclinação */}
          <div className="regression-section">
            <h3>
              <i className="bi bi-activity" style={{ marginRight: '8px' }}></i>
              Inclinação da linha: {data.slope.toFixed(4)}
            </h3>
            <p className="regression-trend-info">
              {data.slope > 0 && 'Positivo = subindo | '}
              {data.slope < 0 && 'Negativo = descendo | '}
              {Math.abs(data.slope) < 0.01 && 'Perto de zero = estável'}
            </p>
          </div>

          {/* Estatísticas */}
          <div className="regression-section">
            <h3>
              <i className="bi bi-bar-chart" style={{ marginRight: '8px' }}></i>
              Estatísticas:
            </h3>
            <ul className="regression-list">
              <li>Quantidade de meses analisados: {data.monthsAnalyzed}</li>
              <li>Score médio no período: {data.averageScore.toFixed(2)}</li>
            </ul>
          </div>

          {/* Comparação Real vs Previsto */}
          <div className="regression-section">
            <h3>
              <i className="bi bi-clipboard-data" style={{ marginRight: '8px' }}></i>
              Comparação: Real vs Previsto
            </h3>
            <p className="regression-note">Veja como o score real de cada mês se compara com o que a linha previu:</p>
            
            <div className="regression-table-wrapper">
              <table className="regression-table">
                <thead>
                  <tr>
                    <th>Mês</th>
                    <th>Score Real</th>
                    <th>Previsão</th>
                    <th>Diferença</th>
                  </tr>
                </thead>
                <tbody>
                  {data.realVsPredicted.map((row, idx) => (
                    <tr key={idx}>
                      <td>{row.month}</td>
                      <td>{row.real.toFixed(2)}</td>
                      <td>{row.predicted.toFixed(2)}</td>
                      <td style={{ color: row.difference >= 0 ? '#4ade80' : '#f87171' }}>
                        {row.difference >= 0 ? '+' : ''}{row.difference.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegressionModal;
