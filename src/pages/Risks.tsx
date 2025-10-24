import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { TrendingUp, TrendingDown, BarChart2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import "../pages/Page.css";
import "./Score.css";
import "./Risks.css";

interface RiskSupplier {
  supplier_id: string;
  ssid: string | null;
  vendor_name: string;
  bu: string | null;
  po: string | null;
  avg_score: number;
  q1: number | null;
  q2: number | null;
  q3: number | null;
  q4: number | null;
}

/**
 * Página de Risks.
 * Lista fornecedores com média abaixo da meta e exibe scores por trimestre.
 */
function Risks() {
  const [suppliers, setSuppliers] = useState<RiskSupplier[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [target, setTarget] = useState(8.7);
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
    loadSuppliersAtRisk();
  }, [selectedYear, target]);

  const loadSuppliersAtRisk = async () => {
    setLoading(true);
    try {
      const data = await invoke<RiskSupplier[]>("get_suppliers_at_risk", {
        year: selectedYear,
        target: target,
      });
      console.log('📊 Fornecedores em risco carregados:', data);
      setSuppliers(data);
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

  const handleViewTimeline = (supplierName: string) => {
    // Navegar para Timeline e passar o nome do fornecedor via state
    navigate('/timeline', { state: { searchSupplier: supplierName } });
  };

  // Gerar anos dinamicamente: ano atual até ano atual + 5
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 6 }, (_, i) => currentYear + i);

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
                    <button 
                      className="chart-button"
                      onClick={() => handleViewTimeline(supplier.vendor_name)}
                      title="Ver Timeline"
                    >
                      <BarChart2 size={18} />
                    </button>
                    <div className="risk-score-large" style={{ color: getScoreColor(supplier.avg_score) }}>
                      {supplier.avg_score.toFixed(2)}
                    </div>
                  </div>
                  <div className="risk-card-info-stacked">
                    <span>BU: {supplier.bu || "N/A"}</span>
                    <span>PO: {supplier.po || "N/A"}</span>
                    <span>SSID: {supplier.ssid || "N/A"}</span>
                    <span>ID: {supplier.supplier_id}</span>
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
                      <div key={quarter.label} className="risk-quarter">
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
    </div>
  );
}

export default Risks;
