import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { Send } from "lucide-react";
import 'bootstrap-icons/font/bootstrap-icons.css';
import "../pages/Page.css";
import "./Email.css";

interface Supplier {
  supplier_id: string;
  vendor_name: string;
  supplier_po?: string;
  business_unit?: string;
  supplier_status?: string;
  supplier_email?: string;
  sqie?: string;
  planner?: string;
  continuity?: string;
  sourcing?: string;
}

interface ResponsibleInfo {
  alias?: string;
  name?: string;
  email?: string;
}

interface SupplierResponsibles {
  sqie: ResponsibleInfo;
  planner: ResponsibleInfo;
  continuity: ResponsibleInfo;
  sourcing: ResponsibleInfo;
}

/**
 * Página de Email.
 * Interface para envio de emails individuais para fornecedores.
 */
function Email() {
  // Estados para Envio Individual
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Supplier[]>([]);
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [emailComments, setEmailComments] = useState<string>('Performance consistente ao longo do ano. Destaque para os meses de maio e julho com notas máximas. Recomenda-se manter o padrão de qualidade e pontualidade.');
  const [responsibles, setResponsibles] = useState<SupplierResponsibles | null>(null);
  
  // Template de Email
  const [emailSubject, setEmailSubject] = useState<string>('Avaliação de Performance - {ANO}');
  const [emailBody, setEmailBody] = useState<string>(`Prezado(a) {FORNECEDOR},

Segue abaixo a avaliação de performance referente ao ano de {ANO}:

{TABELA_SCORES}

{COMENTARIOS}

Atenciosamente,
Equipe de Qualidade`);

  // Busca de fornecedores (Individual)
  const handleSearchInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);

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
    setSearchQuery(supplier.vendor_name);
    setShowDropdown(false);
  };

  // Buscar responsáveis quando um fornecedor é selecionado
  useEffect(() => {
    if (selectedSupplier) {
      const loadResponsibles = async () => {
        try {
          const [sqieList, plannerList, continuityList, sourcingList] = await Promise.all([
            invoke<Array<{name: string, alias: string, email: string}>>('get_sqie_list'),
            invoke<Array<{name: string, alias: string, email: string}>>('get_planner_list'),
            invoke<Array<{name: string, alias: string, email: string}>>('get_continuity_list'),
            invoke<Array<{name: string, alias: string, email: string}>>('get_sourcing_list'),
          ]);

          const sqie = sqieList.find(item => item.alias === selectedSupplier.sqie);
          const planner = plannerList.find(item => item.alias === selectedSupplier.planner);
          const continuity = continuityList.find(item => item.alias === selectedSupplier.continuity);
          const sourcing = sourcingList.find(item => item.alias === selectedSupplier.sourcing);

          setResponsibles({
            sqie: sqie || { alias: selectedSupplier.sqie, name: '', email: '' },
            planner: planner || { alias: selectedSupplier.planner, name: '', email: '' },
            continuity: continuity || { alias: selectedSupplier.continuity, name: '', email: '' },
            sourcing: sourcing || { alias: selectedSupplier.sourcing, name: '', email: '' },
          });
        } catch (error) {
          console.error('Erro ao buscar responsáveis:', error);
          setResponsibles(null);
        }
      };
      
      loadResponsibles();
    } else {
      setResponsibles(null);
    }
  }, [selectedSupplier]);

  const handleClearSupplier = () => {
    setSelectedSupplier(null);
    setSearchQuery('');
    setSearchResults([]);
  };

  // Gera gráfico visual simples usando barras (compatível com Outlook)
  const generateChartVisual = (data: number[], label: string, color: string) => {
    const maxValue = 10;
    const monthNames = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
    
    let html = `<div style="border: 2px solid #ddd; border-radius: 8px; padding: 15px; background: #ffffff;">`;
    html += `<div style="text-align: center; font-weight: 700; color: #333; margin-bottom: 12px; font-size: 14px;">${label}</div>`;
    html += `<table style="width: 100%; border-collapse: collapse;">`;
    html += `<tr>`;
    
    data.forEach((value, index) => {
      const heightPercent = (value / maxValue) * 100;
      html += `<td style="vertical-align: bottom; text-align: center; padding: 0 2px;">`;
      html += `<div style="background: ${color}; height: ${heightPercent}px; border-radius: 3px 3px 0 0; margin-bottom: 3px;"></div>`;
      html += `<div style="font-size: 9px, color: #666;">${monthNames[index]}</div>`;
      html += `</td>`;
    });
    
    html += `</tr></table></div>`;
    return html;
  };

  // Gera tabela de scores (exemplo com dados mockados)
  const generateScoresTable = () => {
    const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    
    // Dados mockados - em produção, isso viria do backend
    const mockScores = [
      { otif: 8.5, nil: 10, pickup: 10, package: 8.0, total: 9.1 },
      { otif: 9.0, nil: 10, pickup: 5, package: 10, total: 8.5 },
      { otif: 7.5, nil: 10, pickup: 10, package: 10, total: 9.4 },
      { otif: 8.8, nil: 5, pickup: 10, package: 10, total: 8.5 },
      { otif: 9.2, nil: 10, pickup: 10, package: 10, total: 9.8 },
      { otif: 8.0, nil: 10, pickup: 10, package: 5, total: 8.3 },
      { otif: 9.5, nil: 10, pickup: 10, package: 10, total: 9.9 },
      { otif: 8.7, nil: 10, pickup: 5, package: 10, total: 8.4 },
      { otif: 9.0, nil: 10, pickup: 10, package: 10, total: 9.8 },
      { otif: 8.5, nil: 10, pickup: 10, package: 10, total: 9.6 },
      { otif: 9.3, nil: 10, pickup: 10, package: 10, total: 9.8 },
      { otif: 8.9, nil: 10, pickup: 10, package: 10, total: 9.7 },
    ];

    // Extrair dados para os gráficos
    const otifData = mockScores.map(s => s.otif);
    const nilData = mockScores.map(s => s.nil);
    const pickupData = mockScores.map(s => s.pickup);
    const packageData = mockScores.map(s => s.package);

    let html = '<html><body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; margin: 0;">';
    html += '<div style="max-width: 800px; margin: 0 auto; background: #ffffff; padding: 30px;">';
    
    // Header com logo/título
    html += '<div style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #CE1126; padding-bottom: 20px;">';
    html += '<h1 style="color: #CE1126; margin: 0; font-size: 28px; letter-spacing: 1px;">Avaliação de Performance - 2025</h1>';
    html += '<p style="color: #666; margin: 10px 0 0 0; font-size: 14px;">Relatório Anual de Qualidade do Fornecedor</p>';
    html += '</div>';

    // Seção de Responsáveis (dados reais do backend) - usando tabela para compatibilidade com Outlook
    if (responsibles) {
      html += '<div style="background: #f8f9fa; padding: 20px; margin-bottom: 30px;">';
      html += '<h2 style="color: #333; font-size: 18px; margin: 0 0 15px 0; font-weight: 600;">Responsáveis</h2>';
      html += '<table style="width: 100%; border-collapse: collapse;"><tr>';
      
      // SQIE
      html += '<td style="width: 48%; padding: 8px; vertical-align: top;">';
      html += '<div style="background: white; padding: 12px; border: 1px solid #ddd;">';
      html += '<div style="font-size: 11px; color: #666; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">SQIE</div>';
      html += `<div style="font-size: 14px; color: #333; font-weight: 600;">${responsibles.sqie.name || 'N/A'}</div>`;
      html += `<div style="font-size: 12px; color: #666; margin-top: 3px;">${responsibles.sqie.email || 'N/A'}</div>`;
      html += '</div></td>';
      
      html += '<td style="width: 4%;"></td>';
      
      // Planner
      html += '<td style="width: 48%; padding: 8px; vertical-align: top;">';
      html += '<div style="background: white; padding: 12px; border: 1px solid #ddd;">';
      html += '<div style="font-size: 11px; color: #666; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Planner</div>';
      html += `<div style="font-size: 14px; color: #333; font-weight: 600;">${responsibles.planner.name || 'N/A'}</div>`;
      html += `<div style="font-size: 12px, color: #666; margin-top: 3px;">${responsibles.planner.email || 'N/A'}</div>`;
      html += '</div></td>';
      
      html += '</tr><tr>';
      
      // Continuity
      html += '<td style="width: 48%; padding: 8px; vertical-align: top;">';
      html += '<div style="background: white; padding: 12px; border: 1px solid #ddd;">';
      html += '<div style="font-size: 11px; color: #666; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Continuity</div>';
      html += `<div style="font-size: 14px; color: #333; font-weight: 600;">${responsibles.continuity.name || 'N/A'}</div>`;
      html += `<div style="font-size: 12px; color: #666; margin-top: 3px;">${responsibles.continuity.email || 'N/A'}</div>`;
      html += '</div></td>';
      
      html += '<td style="width: 4%;"></td>';
      
      // Sourcing
      html += '<td style="width: 48%; padding: 8px; vertical-align: top;">';
      html += '<div style="background: white; padding: 12px; border: 1px solid #ddd;">';
      html += '<div style="font-size: 11px; color: #666; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Sourcing</div>';
      html += `<div style="font-size: 14px; color: #333; font-weight: 600;">${responsibles.sourcing.name || 'N/A'}</div>`;
      html += `<div style="font-size: 12px; color: #666; margin-top: 3px;">${responsibles.sourcing.email || 'N/A'}</div>`;
      html += '</div></td>';
      
      html += '</tr></table></div>';
    }

    // Tabela de scores
    html += '<table style="width: 100%; border-collapse: collapse; margin: 20px 0; border: 1px solid #ddd;">';
    html += '<thead><tr style="background: #CE1126; color: white;">';
    html += '<th style="padding: 14px; border: 1px solid #ddd; text-align: center; font-size: 12px; text-transform: uppercase;">Mês</th>';
    html += '<th style="padding: 14px, border: 1px solid #ddd; text-align: center; font-size: 12px; text-transform: uppercase;">OTIF</th>';
    html += '<th style="padding: 14px, border: 1px solid #ddd; text-align: center; font-size: 12px; text-transform: uppercase;">NIL</th>';
    html += '<th style="padding: 14px, border: 1px solid #ddd; text-align: center; font-size: 12px; text-transform: uppercase;">Pickup</th>';
    html += '<th style="padding: 14px, border: 1px solid #ddd; text-align: center; font-size: 12px; text-transform: uppercase;">Package</th>';
    html += '<th style="padding: 14px, border: 1px solid #ddd; text-align: center; font-size: 12px; text-transform: uppercase;">Total</th>';
    html += '</tr></thead><tbody>';

    mockScores.forEach((score, index) => {
      const rowBg = index % 2 === 0 ? '#f8f9fa' : '#ffffff';
      html += `<tr style="background: ${rowBg};">`;
      html += `<td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; font-weight: 600; color: #333;">${monthNames[index]}</td>`;
      html += `<td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; color: #555;">${score.otif.toFixed(1)}</td>`;
      html += `<td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; color: #555;">${score.nil.toFixed(1)}</td>`;
      html += `<td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; color: #555;">${score.pickup.toFixed(1)}</td>`;
      html += `<td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; color: #555;">${score.package.toFixed(1)}</td>`;
      html += `<td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; font-weight: 700; color: #CE1126; font-size: 15px;">${score.total.toFixed(1)}</td>`;
      html += '</tr>';
    });

    html += '</tbody></table>';

    // Gráficos usando tabela (compatível com Outlook)
    html += '<div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #e0e0e0;">';
    html += '<h2 style="color: #333; font-size: 20px; margin-bottom: 25px; text-align: center;">Evolução dos Indicadores</h2>';
    html += '<table style="width: 100%; border-collapse: collapse;"><tr>';
    html += `<td style="width: 48%; padding: 10px; vertical-align: top;">${generateChartVisual(otifData, 'OTIF', '#2563eb')}</td>`;
    html += `<td style="width: 4%;"></td>`;
    html += `<td style="width: 48%; padding: 10px; vertical-align: top;">${generateChartVisual(nilData, 'NIL', '#10b981')}</td>`;
    html += '</tr><tr>';
    html += `<td style="width: 48%; padding: 10px; vertical-align: top;">${generateChartVisual(pickupData, 'Pickup', '#f59e0b')}</td>`;
    html += `<td style="width: 4%;"></td>`;
    html += `<td style="width: 48%; padding: 10px; vertical-align: top;">${generateChartVisual(packageData, 'Package', '#8b5cf6')}</td>`;
    html += '</tr></table>';

    html += '</div></div></body></html>';
    return html;
  };

  // Gera preview do email
  const generateEmailPreview = (supplier: Supplier, month: string, year: string) => {
    const scoresTable = generateScoresTable();
    
    // Formatar comentários com estilo
    const commentsHtml = `
      <div style="background: #fff9e6; border-left: 4px solid #f59e0b; padding: 20px; border-radius: 8px; margin-top: 25px;">
        <h3 style="color: #333; font-size: 16px; margin: 0 0 10px 0; font-weight: 600;">Comentários</h3>
        <p style="color: #555; font-size: 14px; line-height: 1.6; margin: 0;">${emailComments}</p>
      </div>
    `;
    
    let preview = emailBody
      .replace(/{FORNECEDOR}/g, supplier.vendor_name)
      .replace(/{ANO}/g, year)
      .replace(/{TABELA_SCORES}/g, scoresTable)
      .replace(/{COMENTARIOS}/g, commentsHtml);
    
    return preview;
  };

  const generateSubjectPreview = (supplier: Supplier, month: string, year: string) => {
    return emailSubject
      .replace(/{FORNECEDOR}/g, supplier.vendor_name)
      .replace(/{ANO}/g, year);
  };

  // Meses e Anos
  const months = [
    { value: '1', label: 'Janeiro' },
    { value: '2', label: 'Fevereiro' },
    { value: '3', label: 'Março' },
    { value: '4', label: 'Abril' },
    { value: '5', label: 'Maio' },
    { value: '6', label: 'Junho' },
    { value: '7', label: 'Julho' },
    { value: '8', label: 'Agosto' },
    { value: '9', label: 'Setembro' },
    { value: '10', label: 'Outubro' },
    { value: '11', label: 'Novembro' },
    { value: '12', label: 'Dezembro' },
  ];

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => (currentYear - i).toString());

  // Função para enviar email via Outlook
  const handleSendEmail = async () => {
    console.log('=== BOTÃO DE ENVIO CLICADO ===');
    console.log('selectedSupplier:', selectedSupplier);
    console.log('selectedYear:', selectedYear);
    
    if (!selectedSupplier || !selectedYear) {
      console.log('ERRO: Faltam dados - fornecedor ou ano');
      alert('Selecione um fornecedor e o ano para enviar.');
      return;
    }
    
    console.log('Email do fornecedor:', selectedSupplier.supplier_email);
    if (!selectedSupplier.supplier_email) {
      console.log('ERRO: Fornecedor sem email');
      alert('O fornecedor selecionado não possui email cadastrado.');
      return;
    }
    try {
      const emailTo = selectedSupplier.supplier_email || '';
      const emailSubject = generateSubjectPreview(selectedSupplier, '', selectedYear);
      const emailBodyHtml = generateEmailPreview(selectedSupplier, '', selectedYear);
      console.log('Enviando email:', { to: emailTo, subject: emailSubject, bodyHtml: emailBodyHtml });
      await invoke('send_email_via_outlook', {
        to: emailTo,
        subject: emailSubject,
        bodyHtml: emailBodyHtml,
      });
      alert('Email enviado com sucesso!');
    } catch (error) {
      console.error('Erro ao enviar email:', error);
      alert('Erro ao enviar email: ' + String(error));
    }
  };

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.search-container-inline')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="email-page">
      {/* Conteúdo */}
      <div className="email-content">
        <div className="email-tab-content">
          {/* Barra de Pesquisa e Ano - Uma linha */}
          <div className="email-filters">
              {/* Busca de Fornecedor */}
              <div className="search-container-inline">
                <i className="bi bi-search search-icon"></i>
                <input
                  type="text"
                  placeholder="Buscar fornecedor..."
                  value={searchQuery}
                  onChange={handleSearchInput}
                  className="search-input-inline"
                  onFocus={() => searchQuery && setShowDropdown(true)}
                />
                {selectedSupplier && (
                  <button className="clear-btn-inline" onClick={handleClearSupplier}>
                    <i className="bi bi-x-lg"></i>
                  </button>
                )}

                {/* Dropdown Overlay */}
                {showDropdown && searchQuery && (
                  <div className="search-dropdown-overlay show">
                    {searchResults.length > 0 ? (
                      searchResults.map((supplier) => (
                        <div
                          key={supplier.supplier_id}
                          className="dropdown-item-overlay"
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
                                <span className="dropdown-detail-label">Email:</span> {supplier.supplier_email || '—'}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="dropdown-item-overlay no-results">
                        <div className="dropdown-item-content">
                          <i className="bi bi-inbox"></i>
                          <p>Nenhum fornecedor encontrado</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {/* Ano */}
              <div className="custom-select-wrapper">
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value)}
                  className="filter-select"
                >
                  <option value="">Selecione o ano</option>
                  {years.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
                <i className="bi bi-chevron-down select-icon"></i>
              </div>
            </div>



            {/* Template e Preview */}
            <div className="email-main">
              <h2>Template de Email</h2>
                
                {/* Editor do Template */}
                <div className="template-editor">
                  <div className="form-group">
                    <label>Assunto do Email</label>
                    <input
                      type="text"
                      value={emailSubject}
                      onChange={(e) => setEmailSubject(e.target.value)}
                      className="form-input"
                      placeholder="Assunto do email"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Corpo do Email</label>
                    <textarea
                      value={emailBody}
                      onChange={(e) => setEmailBody(e.target.value)}
                      className="form-textarea"
                      rows={12}
                      placeholder="Corpo do email..."
                    />
                  </div>

                  <div className="form-group">
                    <label>Comentários</label>
                    <textarea
                      value={emailComments}
                      onChange={(e) => setEmailComments(e.target.value)}
                      className="form-textarea"
                      rows={4}
                      placeholder="Comentários sobre a performance do fornecedor..."
                    />
                  </div>
                  
                  <div className="template-variables">
                    <strong>Variáveis disponíveis:</strong>
                    <div className="variables-list">
                      <span className="variable">{'{{FORNECEDOR}}'}</span>
                      <span className="variable">{'{{ANO}}'}</span>
                      <span className="variable">{'{{TABELA_SCORES}}'}</span>
                      <span className="variable">{'{{COMENTARIOS}}'}</span>
                    </div>
                  </div>
                </div>

                {/* Preview */}
                {selectedSupplier && selectedYear && (
                  <div className="email-preview">
                    <h3>Preview do Email</h3>
                    <div className="preview-container">
                      <div className="preview-header">
                        <div className="preview-field">
                          <strong>Para:</strong> {selectedSupplier.supplier_email || 'email@fornecedor.com'}
                        </div>
                        <div className="preview-field">
                          <strong>Assunto:</strong> {generateSubjectPreview(selectedSupplier, '', selectedYear)}
                        </div>
                      </div>
                      <div className="preview-body" dangerouslySetInnerHTML={{ __html: generateEmailPreview(selectedSupplier, '', selectedYear) }}>
                      </div>
                    </div>
                  </div>
                )}

                {/* Botão Enviar */}
                <button 
                  className="btn-send" 
                  disabled={!selectedSupplier || !selectedYear}
                  onClick={handleSendEmail}
                >
                  <Send size={18} />
                  Enviar Email via Outlook
                </button>
              </div>
        </div>
      </div>
    </div>
  );
}

export default Email;
