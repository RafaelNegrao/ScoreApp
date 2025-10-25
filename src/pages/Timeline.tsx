import React, { useState, useEffect } from "react";
import { Search, Info, BarChart2, Grid3x3, Calendar, TrendingUp } from "lucide-react";
import { invoke } from '@tauri-apps/api/tauri';
import { useLocation } from 'react-router-dom';
import SupplierInfoModal from "../components/SupplierInfoModal";
import { DetailedRecordsTable } from '../components/DetailedRecordsTable.tsx';
import MetricsOverview from "../components/MetricsOverview";
import PerformanceChart from './Timeline/PerformanceChart';
import IndividualMetrics from './Timeline/IndividualMetrics';
import 'bootstrap-icons/font/bootstrap-icons.css';
import "../pages/Page.css";
import "./Timeline.css";

interface Supplier {
  supplier_id: string;
  vendor_name: string;
  supplier_po?: string;
  business_unit?: string;
  supplier_status?: string;
}

/**
 * Página de Timeline Analytics.
 * Exibe análises e métricas de fornecedores ao longo do tempo.
 */
function Timeline() {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState("metricas");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedYear, setSelectedYear] = useState("2025");
  const [searchResults, setSearchResults] = useState<Supplier[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [showSupplierInfo, setShowSupplierInfo] = useState(false);

  // Buscar automaticamente quando vindo de outra página
  useEffect(() => {
    const state = location.state as { searchSupplier?: string } | null;
    if (state?.searchSupplier) {
      const searchAndSelect = async () => {
        try {
          const results = await invoke<Supplier[]>('search_suppliers', { query: state.searchSupplier!.trim() });
          if (results && results.length > 0) {
            // Seleciona o primeiro resultado (geralmente será o exato)
            const supplier = results[0];
            setSelectedSupplier(supplier);
            setSearchTerm(supplier.vendor_name);
            setShowDropdown(false);
          }
        } catch (error) {
          console.error('Erro ao buscar fornecedor:', error);
        }
      };
      searchAndSelect();
    }
  }, [location.state]);

  const tabs = [
    { id: "metricas", label: "Metrics", icon: BarChart2 },
    { id: "performance", label: "Performance Chart", icon: TrendingUp },
    { id: "individual", label: "Individual Metrics", icon: Grid3x3 },
    { id: "detalhado", label: "Detailed Records", icon: Calendar },
  ];

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.search-container')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchTerm(query);

    if (query.trim().length === 0) {
      setShowDropdown(false);
      setSearchResults([]);
      return;
    }

    try {
      const results = await invoke<Supplier[]>('search_suppliers', { query: query.trim() });
      setSearchResults(results);
      setShowDropdown(true);
    } catch (error) {
      console.error('Erro ao buscar fornecedores:', error);
      setSearchResults([]);
      setShowDropdown(true);
    }
  };

  const handleSelectSupplier = (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setSearchTerm(supplier.vendor_name);
    setShowDropdown(false);
  };

  const handleClearSelection = () => {
    setSelectedSupplier(null);
    setSearchTerm("");
    setSearchResults([]);
    setShowDropdown(false);
  };

  const handleOpenSupplierInfo = () => {
    if (selectedSupplier) {
      setShowSupplierInfo(true);
    }
  };

  return (
    <div className="page-container">
      {/* Search and Year Filter */}
      <div className="timeline-filters">
        <div className="search-container">
          <Search size={18} color="var(--text-secondary)" />
          <input
            type="text"
            placeholder="Digite para buscar fornecedor..."
            value={searchTerm}
            onChange={handleSearchInput}
            onFocus={() => searchTerm.trim().length > 0 && setShowDropdown(true)}
            className="timeline-search"
          />

          {selectedSupplier && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={handleClearSelection}
              title="Limpar seleção"
            >
              <i className="bi bi-x"></i>
            </button>
          )}

          {showDropdown && (
            <div className="search-dropdown show">
              {searchResults.length > 0 ? (
                searchResults.map((supplier) => (
                  <div
                    key={supplier.supplier_id}
                    className="dropdown-item"
                    onClick={() => handleSelectSupplier(supplier)}
                  >
                    <div className="dropdown-item-content">
                      <div className="dropdown-item-line1">
                        <strong>{supplier.vendor_name}</strong>
                      </div>
                      <div className="dropdown-item-line2">
                        <span className="dropdown-detail-item">
                          <span className="dropdown-detail-label">ID:</span> {supplier.supplier_id || '—'}
                        </span>
                        <span className="dropdown-detail-separator">•</span>
                        <span className="dropdown-detail-item">
                          <span className="dropdown-detail-label">PO:</span> {supplier.supplier_po || '—'}
                        </span>
                        <span className="dropdown-detail-separator">•</span>
                        <span className="dropdown-detail-item">
                          <span className="dropdown-detail-label">BU:</span> {supplier.business_unit || '—'}
                        </span>
                      </div>
                    </div>
                    {supplier.supplier_status && (
                      <div className={`status-indicator ${supplier.supplier_status.toLowerCase()}`}>
                        <i className="bi bi-circle-fill"></i>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="dropdown-item no-results">
                  <div className="dropdown-item-main">
                    <i className="bi bi-search" style={{ marginRight: '8px', opacity: 0.5 }}></i>
                    <span style={{ color: 'var(--text-secondary)' }}>Nenhum fornecedor encontrado</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="year-select-wrapper">
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="year-select"
          >
            <option value="">Ano</option>
            {Array.from({ length: 6 }, (_, i) => new Date().getFullYear() + i).map((year) => (
              <option key={year} value={year.toString()}>{year}</option>
            ))}
          </select>
          <i className="bi bi-chevron-down year-select-icon"></i>
        </div>

        <div title={selectedSupplier ? "Informações do fornecedor" : "Selecione um fornecedor"}>
          <Info 
            size={20} 
            color="var(--accent-primary)" 
            style={{ cursor: selectedSupplier ? "pointer" : "not-allowed", opacity: selectedSupplier ? 1 : 0.5 }} 
            onClick={handleOpenSupplierInfo}
          />
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="timeline-tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`timeline-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={18} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="timeline-content">
        {activeTab === "metricas" && (
          <MetricsOverview 
            supplierId={selectedSupplier?.supplier_id || null}
            selectedYear={selectedYear}
          />
        )}

        {activeTab === "performance" && (
          <PerformanceChart 
            supplierId={selectedSupplier?.supplier_id || null}
            selectedYear={selectedYear}
          />
        )}

        {activeTab === "individual" && (
          <IndividualMetrics 
            supplierId={selectedSupplier?.supplier_id || null}
            selectedYear={selectedYear}
          />
        )}

        {activeTab === "detalhado" && (
          <DetailedRecordsRealData
            supplierId={selectedSupplier?.supplier_id || null}
            selectedYear={selectedYear}
          />
        )}
      </div>

      {/* Modal de informações do fornecedor */}
      {showSupplierInfo && selectedSupplier && (
        <SupplierInfoModal
          isOpen={showSupplierInfo}
          supplier={selectedSupplier}
          onClose={() => setShowSupplierInfo(false)}
        />
      )}
    </div>
  );
}

export default Timeline;

// Componente auxiliar para buscar e exibir dados reais na tabela detalhada
function DetailedRecordsRealData({ supplierId, selectedYear }: { supplierId: string | null, selectedYear: string }) {
  const [supplier, setSupplier] = React.useState<any>(null);
  const [userPermissions, setUserPermissions] = React.useState<any>(null);

  // Buscar permissões do usuário
  React.useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setUserPermissions({
          otif: user.permissions?.otif || '',
          nil: user.permissions?.nil || '',
          pickup: user.permissions?.pickup || '',
          package: user.permissions?.package || ''
        });
      } catch (error) {
        console.error('Erro ao parsear usuário:', error);
      }
    }
  }, []);

  // Buscar fornecedor
  React.useEffect(() => {
    if (!supplierId) {
      setSupplier(null);
      return;
    }
    const loadSupplier = async () => {
      try {
        const suppliers = await invoke<any[]>('search_suppliers', { query: supplierId });
        if (suppliers && suppliers.length > 0) {
          setSupplier(suppliers[0]);
        }
      } catch (error) {
        console.error('Erro ao carregar fornecedor:', error);
      }
    };
    loadSupplier();
  }, [supplierId]);

  if (!supplierId) {
    return <div className="empty-state"><i className="bi bi-calendar3" style={{ fontSize: '3rem', color: 'var(--text-muted)', opacity: 0.5 }}></i><p style={{ fontSize: '0.95rem', fontWeight: 400, color: 'var(--text-muted)', opacity: 0.85 }}>Selecione um fornecedor</p></div>;
  }

  return (
    <DetailedRecordsTable 
      supplierId={supplierId}
      supplierName={supplier?.vendor_name || supplierId}
      selectedYear={selectedYear}
      userPermissions={userPermissions}
    />
  );
}
