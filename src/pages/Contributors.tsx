import { useState, useEffect } from "react";
import { invoke } from '@tauri-apps/api/tauri';
import "./Contributors.css";

interface Contributor {
  user_wwid: string;
  user_name: string;
  contribution_count: number;
  dailyCounts: Map<string, number>;
}

interface User {
  user_wwid: string;
  user_privilege: string;
}

function Contributors() {
  const [contributors, setContributors] = useState<Contributor[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());

  useEffect(() => {
    loadContributors();
  }, [selectedYear]);

  const parseDateString = (dateString: string) => {
    if (!dateString) return null;
    const rawDate = dateString.split(' ')[0];

    if (rawDate.includes('-')) {
      const [year, month, day] = rawDate.split('-').map(Number);
      if (!year || !month || !day) return null;
      return new Date(year, month - 1, day);
    }

    if (rawDate.includes('/')) {
      const [day, month, year] = rawDate.split('/').map(Number);
      if (!year || !month || !day) return null;
      return new Date(year, month - 1, day);
    }

    return null;
  };

  const formatDateKey = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const buildCalendar = (year: number) => {
    const start = new Date(year, 0, 1);
    const end = new Date(year, 11, 31);

    const startOffset = (start.getDay() + 6) % 7; // segunda-feira como início
    const endOffset = (6 - ((end.getDay() + 6) % 7));

    const calendarStart = new Date(year, 0, 1 - startOffset);
    const calendarEnd = new Date(year, 11, 31 + endOffset);

    const days: Date[] = [];
    const cursor = new Date(calendarStart);

    while (cursor <= calendarEnd) {
      days.push(new Date(cursor));
      cursor.setDate(cursor.getDate() + 1);
    }

    const weeks: Date[][] = [];
    for (let i = 0; i < days.length; i += 7) {
      weeks.push(days.slice(i, i + 7));
    }

    return weeks;
  };

  const getIntensity = (count: number, max: number) => {
    if (!count) return 0;
    if (max <= 4) return Math.min(4, count);
    if (count <= max * 0.25) return 1;
    if (count <= max * 0.5) return 2;
    if (count <= max * 0.75) return 3;
    return 4;
  };

  const normalizePrivilege = (value: string) =>
    value.toLowerCase().replace(/\s|_|-/g, '');

  const loadContributors = async () => {
    try {
      setLoading(true);

      const data = await invoke<[string, string, string, number][]>('get_user_contribution_calendar', {
        year: selectedYear
      });

      const users = await invoke<User[]>('get_all_users');
      const superAdminWwids = new Set(
        users
          .filter((user) => normalizePrivilege(user.user_privilege || '') === 'superadmin')
          .map((user) => user.user_wwid.trim())
          .filter(Boolean)
      );

      const contributorsMap = new Map<string, Contributor>();

      data.forEach(([wwid, name, dateStr, count]) => {
        const parsedDate = parseDateString(dateStr);
        if (!parsedDate) return;
        const key = formatDateKey(parsedDate);
        const contributorKey = wwid.trim();
        if (!contributorKey) return;

        const contributor = contributorsMap.get(contributorKey);
        if (contributor) {
          contributor.contribution_count += count;
          contributor.dailyCounts.set(key, count);
          return;
        }

        contributorsMap.set(contributorKey, {
          user_wwid: wwid,
          user_name: name,
          contribution_count: count,
          dailyCounts: new Map([[key, count]])
        });
      });

      const formattedContributors = Array.from(contributorsMap.values())
        .filter((contributor) => !superAdminWwids.has(contributor.user_wwid.trim()))
        .sort((a, b) => b.contribution_count - a.contribution_count);

      setContributors(formattedContributors);
      setError('');
    } catch (err) {
      console.error('Erro ao carregar contribuições:', err);
      setError('Erro ao carregar dados de contribuições.');
    } finally {
      setLoading(false);
    }
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
    'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
  ];

  const years = [2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040];

  return (
    <div className="contributors-page">
      <div className="contributors-header">
        <div className="header-title">
          <h1>Contribuidores</h1>
          <p>Contribuições por dia</p>
        </div>
        
        <div className="view-controls">
          <div className="month-year-selector">
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
        </div>
      </div>

      <div className="contributors-container">
        {contributors.length === 0 ? (
          <div className="no-data">
            Nenhum dado de contribuição encontrado.
          </div>
        ) : (
          <div className="contributors-heatmap-list">
            {contributors.map((contributor) => {
              const weeks = buildCalendar(selectedYear);
              const maxCount = Math.max(0, ...Array.from(contributor.dailyCounts.values()));

              const monthLabels = weeks.map((week) => {
                const monthStart = week.find(day => day.getDate() === 1 && day.getFullYear() === selectedYear);
                return monthStart ? months[monthStart.getMonth()] : '';
              });

              return (
                <div key={contributor.user_wwid} className="contributor-heatmap-card">
                  <div className="contributor-heatmap-header">
                    <div>
                      <div className="contributor-name">{contributor.user_name}</div>
                      <div className="contributor-wwid">WWID: {contributor.user_wwid}</div>
                    </div>
                    <div className="contributor-total">{contributor.contribution_count} contribuições</div>
                  </div>

                  <div
                    className="contributor-heatmap"
                    style={{ ['--heatmap-weeks' as any]: weeks.length }}
                  >
                    <div className="heatmap-months">
                      <div className="heatmap-month-spacer" />
                      {monthLabels.map((label, index) => (
                        <div key={`${contributor.user_wwid}-month-${index}`} className="heatmap-month">
                          {label}
                        </div>
                      ))}
                    </div>

                    <div className="heatmap-body">
                      <div className="heatmap-weekdays">
                        <span>Seg</span>
                        <span>Ter</span>
                        <span>Qua</span>
                        <span>Qui</span>
                        <span>Sex</span>
                        <span></span>
                        <span></span>
                      </div>
                      <div className="heatmap-grid">
                        {weeks.map((week, weekIndex) => (
                          <div key={`${contributor.user_wwid}-week-${weekIndex}`} className="heatmap-week">
                            {week.map((day) => {
                              const isCurrentYear = day.getFullYear() === selectedYear;
                              const dateKey = formatDateKey(day);
                              const count = isCurrentYear ? (contributor.dailyCounts.get(dateKey) || 0) : 0;
                              const level = isCurrentYear ? getIntensity(count, maxCount) : 0;
                              const title = isCurrentYear
                                ? `${count} contribuição(ões) em ${day.toLocaleDateString('pt-BR')}`
                                : '';

                              return (
                                <span
                                  key={`${contributor.user_wwid}-${dateKey}`}
                                  className={`heatmap-day level-${level} ${!isCurrentYear ? 'out-of-range' : ''}`}
                                  title={title}
                                />
                              );
                            })}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="heatmap-legend">
                      <span>Menos</span>
                      {[0, 1, 2, 3, 4].map((level) => (
                        <span key={level} className={`heatmap-day level-${level}`} />
                      ))}
                      <span>Mais</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default Contributors;
