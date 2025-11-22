import { useState, useEffect } from "react";
import { invoke } from '@tauri-apps/api/tauri';
import "./Contributors.css";

interface Contributor {
  user_wwid: string;
  user_name: string;
  contribution_count: number;
  last_input_date: string;
}

function Contributors() {
  const [contributors, setContributors] = useState<Contributor[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [viewMode, setViewMode] = useState<'all' | 'monthly'>('all');
  const [selectedMonth, setSelectedMonth] = useState<number>(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());

  useEffect(() => {
    loadContributors();
  }, [viewMode, selectedMonth, selectedYear]);

  const loadContributors = async () => {
    try {
      setLoading(true);
      let data: [string, string, number, string][];
      
      if (viewMode === 'all') {
        data = await invoke<[string, string, number, string][]>('get_user_contributions');
      } else {
        data = await invoke<[string, string, number, string][]>('get_user_contributions_by_month', {
          month: selectedMonth,
          year: selectedYear
        });
      }
      
      const formattedContributors: Contributor[] = data.map(([wwid, name, count, lastDate]) => ({
        user_wwid: wwid,
        user_name: name,
        contribution_count: count,
        last_input_date: lastDate
      }));
      setContributors(formattedContributors);
      setError('');
    } catch (err) {
      console.error('Erro ao carregar contribuições:', err);
      setError('Erro ao carregar dados de contribuições.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Nunca';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="contributors-page">
        <div className="contributors-header">
          <h1>Contribuidores</h1>
          <p>Carregando dados...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="contributors-page">
        <div className="contributors-header">
          <h1>Contribuidores</h1>
          <p className="error-message">{error}</p>
        </div>
      </div>
    );
  }

  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  const years = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i);

  return (
    <div className="contributors-page">
      <div className="contributors-header">
        <div className="header-title">
          <h1>Contribuidores</h1>
          <p>Ranking de usuários por número de contribuições</p>
        </div>
        
        <div className="view-controls">
          <div className="view-tabs">
            <button 
              className={`view-tab ${viewMode === 'all' ? 'active' : ''}`}
              onClick={() => setViewMode('all')}
            >
              Geral
            </button>
            <button 
              className={`view-tab ${viewMode === 'monthly' ? 'active' : ''}`}
              onClick={() => setViewMode('monthly')}
            >
              Mensal
            </button>
          </div>
          
          {viewMode === 'monthly' && (
            <div className="month-year-selector">
              <select 
                value={selectedMonth} 
                onChange={(e) => setSelectedMonth(Number(e.target.value))}
                className="month-select"
              >
                {months.map((month, index) => (
                  <option key={index} value={index + 1}>{month}</option>
                ))}
              </select>
              <select 
                value={selectedYear} 
                onChange={(e) => setSelectedYear(Number(e.target.value))}
                className="year-select"
              >
                {years.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="contributors-container">
        <div className="contributors-table-wrapper">
          <table className="contributors-table">
            <thead>
              <tr>
                <th>#</th>
                <th>WWID</th>
                <th>Nome</th>
                <th>Contribuições</th>
                <th>Último Input</th>
              </tr>
            </thead>
            <tbody>
              {contributors.length === 0 ? (
                <tr>
                  <td colSpan={5} className="no-data">
                    Nenhum dado de contribuição encontrado.
                  </td>
                </tr>
              ) : (
                contributors.map((contributor, index) => (
                  <tr key={contributor.user_wwid}>
                    <td className="rank-cell">
                      <span className={`rank-badge rank-${index + 1}`}>
                        {index + 1}
                      </span>
                    </td>
                    <td className="wwid-cell">{contributor.user_wwid}</td>
                    <td className="name-cell">{contributor.user_name}</td>
                    <td className="count-cell">
                      <span className="contribution-badge">
                        {contributor.contribution_count}
                      </span>
                    </td>
                    <td className="date-cell">{formatDate(contributor.last_input_date)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Contributors;
