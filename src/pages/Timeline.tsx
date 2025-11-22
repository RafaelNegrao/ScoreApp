import React, { useState, useEffect } from "react";
import { Search, Info, BarChart2, Grid3x3, TrendingUp, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import { invoke } from '@tauri-apps/api/tauri';
import { useLocation } from 'react-router-dom';
import SupplierInfoModal from "../components/SupplierInfoModal";
import MetricsOverview from "../components/MetricsOverview";
import PerformanceChart from './Timeline/PerformanceChart';
import IndividualMetrics from './Timeline/IndividualMetrics';
import { useTimelineContext } from '../contexts/TimelineContext';
import 'bootstrap-icons/font/bootstrap-icons.css';
import "../pages/Page.css";
import "./Timeline.css";

interface Supplier {
  supplier_id: string;
  vendor_name: string;
  supplier_po?: string;
  bu?: string;
  supplier_status?: string;
}

/**
 * Página de Timeline Analytics.
 * Exibe análises e métricas de fornecedores ao longo do tempo.
 */
function Timeline() {
  const location = useLocation();
  const {
    selectedSupplier,
    setSelectedSupplier,
    searchTerm,
    setSearchTerm,
    selectedYear,
    setSelectedYear,
    activeTab,
    setActiveTab,
  } = useTimelineContext();

  const [searchResults, setSearchResults] = useState<Supplier[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showSupplierInfo, setShowSupplierInfo] = useState(false);
  const [carouselPage, setCarouselPage] = useState(0);
  const [isUnifiedCarousel, setIsUnifiedCarousel] = useState(false);
  const [unifiedCarouselIndex, setUnifiedCarouselIndex] = useState(0);
  const [isSmallHeight, setIsSmallHeight] = useState(false);

  // Detectar altura pequena da tela
  useEffect(() => {
    const checkHeight = () => {
      setIsSmallHeight(window.innerHeight < 700);
    };
    
    checkHeight();
    window.addEventListener('resize', checkHeight);
    return () => window.removeEventListener('resize', checkHeight);
  }, []);

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
    { id: "graficos", label: "Charts", icon: TrendingUp },
  ];

  // Detectar tamanho de tela para carousel unificado
  useEffect(() => {
    const detectScreenSize = () => {
      if (typeof window === 'undefined') return;
      const width = window.innerWidth;
      setIsUnifiedCarousel(width < 1200);
    };

    detectScreenSize();
    window.addEventListener('resize', detectScreenSize);
    return () => window.removeEventListener('resize', detectScreenSize);
  }, []);

  // Resetar índice do carousel ao mudar de fornecedor ou ano
  useEffect(() => {
    setUnifiedCarouselIndex(0);
  }, [selectedSupplier, selectedYear]);

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
                          <span className="dropdown-detail-label">BU:</span> {supplier.bu || '—'}
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

        {activeTab === "graficos" && (
          !selectedSupplier ? (
            <div className="empty-state">
              <i className="bi bi-graph-up" style={{ fontSize: '3rem', color: 'var(--text-muted)', opacity: 0.5 }}></i>
              <p style={{ fontSize: '0.95rem', fontWeight: 400, color: 'var(--text-muted)', opacity: 0.85 }}>Selecione um fornecedor para visualizar o gráfico de performance</p>
            </div>
          ) : isUnifiedCarousel ? (
            <>
              <div className="unified-charts-carousel">
                <button
                  type="button"
                  className="unified-carousel-button prev"
                  onClick={() => setUnifiedCarouselIndex(prev => (prev === 0 ? 4 : prev - 1))}
                  aria-label="Gráfico anterior"
                >
                  <ChevronLeft size={24} />
                </button>

                <div className="unified-carousel-track">
                  <div className="unified-carousel-slide" key={`unified-${unifiedCarouselIndex}`}>
                    {unifiedCarouselIndex === 0 && (
                      <div className="metric-chart-card unified-chart-card">
                        <PerformanceChart 
                          supplierId={selectedSupplier?.supplier_id || null}
                          selectedYear={selectedYear}
                        />
                      </div>
                    )}
                    {unifiedCarouselIndex > 0 && (
                      <IndividualMetrics 
                        supplierId={selectedSupplier?.supplier_id || null}
                        selectedYear={selectedYear}
                        carouselPage={unifiedCarouselIndex - 1}
                        singleMetricIndex={unifiedCarouselIndex - 1}
                      />
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  className="unified-carousel-button next"
                  onClick={() => setUnifiedCarouselIndex(prev => (prev === 4 ? 0 : prev + 1))}
                  aria-label="Próximo gráfico"
                >
                  <ChevronRight size={24} />
                </button>
              </div>
              
              <div className="unified-carousel-indicators">
                {['Performance', 'OTIF', 'NIL', 'Pickup', 'Package'].map((label, index) => (
                  <button
                    key={index}
                    type="button"
                    className={`unified-carousel-dot ${index === unifiedCarouselIndex ? 'active' : ''}`}
                    onClick={() => setUnifiedCarouselIndex(index)}
                    aria-label={`Exibir gráfico ${label}`}
                    title={label}
                  />
                ))}
              </div>
            </>
          ) : (
            <div className="charts-unified-layout">
              <div className="chart-main">
                <PerformanceChart 
                  supplierId={selectedSupplier?.supplier_id || null}
                  selectedYear={selectedYear}
                />
              </div>
              <div className="charts-carousel-container">
                <div className="charts-grid">
                  <IndividualMetrics 
                    supplierId={selectedSupplier?.supplier_id || null}
                    selectedYear={selectedYear}
                    carouselPage={carouselPage}
                    isSmallHeight={isSmallHeight}
                  />
                </div>
                <div className="carousel-indicators-vertical">
                  {isSmallHeight ? (
                    // Modo altura pequena: 4 páginas (1 gráfico por página)
                    <>
                      <button
                        className={`carousel-indicator-vertical ${carouselPage === 0 ? 'active' : ''}`}
                        onClick={() => setCarouselPage(0)}
                        aria-label="OTIF"
                      />
                      <button
                        className={`carousel-indicator-vertical ${carouselPage === 1 ? 'active' : ''}`}
                        onClick={() => setCarouselPage(1)}
                        aria-label="NIL"
                      />
                      <button
                        className={`carousel-indicator-vertical ${carouselPage === 2 ? 'active' : ''}`}
                        onClick={() => setCarouselPage(2)}
                        aria-label="Pickup"
                      />
                      <button
                        className={`carousel-indicator-vertical ${carouselPage === 3 ? 'active' : ''}`}
                        onClick={() => setCarouselPage(3)}
                        aria-label="Package"
                      />
                    </>
                  ) : (
                    // Modo altura normal: 2 páginas (2 gráficos por página)
                    <>
                      <button
                        className={`carousel-indicator-vertical ${carouselPage === 0 ? 'active' : ''}`}
                        onClick={() => setCarouselPage(0)}
                        aria-label="Página 1"
                      />
                      <button
                        className={`carousel-indicator-vertical ${carouselPage === 1 ? 'active' : ''}`}
                        onClick={() => setCarouselPage(1)}
                        aria-label="Página 2"
                      />
                    </>
                  )}
                </div>
              </div>
            </div>
          )
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
