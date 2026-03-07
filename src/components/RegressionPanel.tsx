import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import './RegressionPanel.css';

interface RegressionData {
    slope: number;
    intercept: number;
    r2: number;
    cv: number;
    trend: 'Crescente' | 'Decrescente' | 'Estável';
    equation: string;
    monthsAnalyzed: number;
    averageScore: number;
    realVsPredicted: { month: string; real: number; predicted: number; difference: number }[];
}

interface RegressionPanelProps {
    data: RegressionData | null;
    metricName: string;
}

/* ── Info modal ──────────────────────────────────────────── */
const InfoModal: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => {
    const [open, setOpen] = useState(false);
    return (
        <>
            <button
                className="reg-info-btn"
                onClick={() => setOpen(true)}
                type="button"
                aria-label="Informação"
            >
                <i className="bi bi-info-circle"></i>
            </button>
            {open && (
                <div className="reg-modal-overlay" onClick={() => setOpen(false)}>
                    <div className="reg-modal" onClick={e => e.stopPropagation()}>
                        <div className="reg-modal__header">
                            <span className="reg-modal__title">{title}</span>
                            <button className="reg-modal__close" onClick={() => setOpen(false)} type="button">×</button>
                        </div>
                        <div className="reg-modal__body">
                            {children}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

/* ── Compact SVG Speedometer ───────────────────────────────── */
const CVGauge: React.FC<{ cv: number }> = ({ cv }) => {
    const cx = 65, cy = 55;
    const r = 40;
    const sw = 8;
    const clamped = Math.min(Math.max(cv, 0), 100);
    const cvOk = clamped <= 25;

    const px = (deg: number) => cx + r * Math.cos((deg * Math.PI) / 180);
    const py = (deg: number) => cy - r * Math.sin((deg * Math.PI) / 180);

    const arc = (a1: number, a2: number) => {
        const la = (a1 - a2) > 180 ? 1 : 0;
        return `M ${px(a1).toFixed(1)} ${py(a1).toFixed(1)} A ${r} ${r} 0 ${la} 1 ${px(a2).toFixed(1)} ${py(a2).toFixed(1)}`;
    };

    const g = 3;
    const ndeg = 180 - (clamped / 100) * 180;
    const nrad = (ndeg * Math.PI) / 180;
    const nlen = r - sw / 2 - 3;
    const nx = cx + nlen * Math.cos(nrad);
    const ny = cy - nlen * Math.sin(nrad);
    const ncolor = clamped <= 25 ? '#4ade80' : clamped <= 50 ? '#fbbf24' : '#f87171';

    return (
        <div style={{ display: 'flex', justifyContent: 'center', width: '100%', margin: '-4px 0' }}>
            <svg viewBox="0 0 130 90" width="160px" height="100px" style={{ display: 'block' }}>
                <path d={arc(180, 0)} stroke="rgba(128,128,128,0.12)" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                <path d={arc(180, 135 + g)} stroke="#00A34F" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                <path d={arc(135 - g, 90 + g)} stroke="#FFB81C" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                <path d={arc(90 - g, 45 + g)} stroke="#f97316" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                <path d={arc(45 - g, 0)} stroke="#CE1126" strokeWidth={sw} fill="none" strokeLinecap="butt" />

                <line x1={cx} y1={cy} x2={nx.toFixed(1)} y2={ny.toFixed(1)}
                    stroke={ncolor} strokeWidth="2" strokeLinecap="round" />
                <circle cx={cx} cy={cy} r={3} fill="var(--card-bg)" stroke={ncolor} strokeWidth={1.5} />

                <text x={cx - r - 2} y={cy + 10} textAnchor="middle" fontSize="6" fill="rgba(148,163,184,0.4)">0</text>
                <text x={cx + r + 2} y={cy + 10} textAnchor="middle" fontSize="6" fill="rgba(148,163,184,0.4)">100</text>

                <text x={cx} y={cy + 15} textAnchor="middle" fontSize="14" fontWeight="800" fill={ncolor}>
                    {clamped.toFixed(1)}%
                </text>
                <text x={cx} y={cy + 29} textAnchor="middle" fontSize="11" fill="rgba(148,163,184,0.6)">
                    {cvOk ? '✓ OK' : '⚠ Ruim'}
                </text>
            </svg>
        </div>
    );
};

/* ── Main Panel ────────────────────────────────────────────── */
const RegressionPanel: React.FC<RegressionPanelProps> = ({ data, metricName }) => {
    const [target, setTarget] = useState<number | null>(null);

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

    if (!data) {
        return (
            <aside className="regression-panel regression-panel--empty">
                <div className="regression-panel__placeholder">
                    <i className="bi bi-graph-up" />
                    <span>Selecione um fornecedor para ver a análise de regressão</span>
                </div>
            </aside>
        );
    }

    const getTrendColor = (t: string) => t === 'Crescente' ? '#00A34F' : t === 'Decrescente' ? '#CE1126' : '#FFB81C';
    const getTrendIcon = (t: string) => t === 'Crescente' ? '↗' : t === 'Decrescente' ? '↘' : '→';
    const getR2Quality = (r2: number) => r2 >= 0.8 ? 'Forte' : r2 >= 0.5 ? 'Moderada' : r2 >= 0.3 ? 'Fraca' : 'Muito fraca';

    return (
        <aside className="regression-panel">
            {/* Header */}
            <div className="regression-panel__header">
                <i className="bi bi-graph-up" />
                <span className="regression-panel__title">Regressão — <strong>{metricName}</strong></span>
            </div>

            {/* Body */}
            <div className="regression-panel__body">

                {/* Tendência */}
                <div className="reg-section">
                    <div className="reg-label-row">
                        <span className="reg-label">Tendência</span>
                        <InfoModal title="Tendência">
                            <p>Indica se os scores estão subindo (Crescente), caindo (Decrescente) ou se mantendo (Estável) ao longo dos meses. É calculado pela inclinação (a) da reta de regressão.</p>
                            <div className="reg-formula-box">
                                <span>Se <b>a {'>'} 0</b> → Crescente</span>
                                <span>Se <b>a {'<'} 0</b> → Decrescente</span>
                                <span>Se <b>a ≈ 0</b> → Estável</span>
                            </div>
                        </InfoModal>
                    </div>
                    <span className="reg-trend-badge" style={{ color: getTrendColor(data.trend) }}>
                        {getTrendIcon(data.trend)} {data.trend}
                    </span>
                </div>

                {/* Equação */}
                <div className="reg-section">
                    <div className="reg-label-row">
                        <span className="reg-label">Equação</span>
                        <InfoModal title="Equação da Reta">
                            <p>A equação da reta que melhor se ajusta aos dados.</p>
                            <div className="reg-formula-box">
                                <span><b>y = ax + b</b></span>
                            </div>
                            <p>Onde <b>'a'</b> (é a inclinação) mostra quanto o score muda a cada mês, e <b>'b'</b> é o valor inicial estimado.</p>
                            <p><i>Exemplo: y = 0.23x + 6.9 significa que o score sobe 0.23 por mês partindo de 6.9.</i></p>
                        </InfoModal>
                    </div>
                    <code className="reg-equation">{data.equation}</code>
                </div>

                {/* R² */}
                <div className="reg-section">
                    <div className="reg-label-row">
                        <span className="reg-label">R² — {getR2Quality(data.r2)}</span>
                        <InfoModal title="R² — Coeficiente de Determinação">
                            <p>O R² indica o quanto a reta explica os dados reais. Varia de 0% a 100%. Quanto mais próximo de 100%, melhor a reta representa a realidade.</p>
                            <div className="reg-formula-box">
                                <span><b>R² = 1 − (Σ erros² ÷ Σ variações²)</b></span>
                            </div>
                            <div className="reg-formula-box">
                                <span><b>{'≥ 80%'}</b> Forte</span>
                                <span><b>{'≥ 50%'}</b> Moderada</span>
                                <span><b>{'≥ 30%'}</b> Fraca</span>
                                <span><b>{'< 30%'}</b> Muito Fraca</span>
                            </div>
                        </InfoModal>
                    </div>
                    <div className="reg-bar-wrapper">
                        <div className="reg-bar">
                            <div className="reg-bar__fill" style={{ width: `${Math.max(0, 100 - data.r2 * 100)}%` }} />
                        </div>
                        <span className="reg-bar__value">{(data.r2 * 100).toFixed(1)}%</span>
                    </div>
                </div>

                {/* Estatísticas */}
                <div className="reg-section">
                    <span className="reg-label">Estatísticas</span>
                    <div className="reg-stats-grid">
                        <div className="reg-stat">
                            <span className="reg-stat__val">{data.monthsAnalyzed}</span>
                            <span className="reg-stat__lbl">Meses</span>
                        </div>
                        <div className="reg-stat">
                            <span className="reg-stat__val">{data.averageScore.toFixed(2)}</span>
                            <span className="reg-stat__lbl">Média</span>
                        </div>
                        <div className="reg-stat">
                            <span className="reg-stat__val">{data.slope.toFixed(3)}</span>
                            <span className="reg-stat__lbl">Inclinação</span>
                        </div>
                    </div>
                </div>



                {/* CV Gauge */}
                <div className="reg-section">
                    <div className="reg-label-row" style={{ width: '100%' }}>
                        <span className="reg-label">Coef. de Variação (CV)</span>
                        <InfoModal title="Coef. de Variação (CV)">
                            <p>Mede o quanto os scores variam em relação à média. Quanto menor, mais consistente o fornecedor.</p>
                            <div className="reg-formula-box">
                                <span><b>CV = (Desvio Padrão ÷ Média) × 100</b></span>
                            </div>
                            <div className="reg-formula-box">
                                <span>Até <b>25%</b> = OK (consistente)</span>
                                <span>Acima de <b>25%</b> = Ruim (disperso)</span>
                            </div>
                        </InfoModal>
                    </div>
                    <CVGauge cv={data.cv} />
                </div>

                {/* Conclusão Geral */}
                <div className="reg-section" style={{ borderBottom: 'none', flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <span className="reg-label" style={{ marginBottom: '8px' }}>Conclusão da Análise</span>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                        <div className="reg-conclusion-item" style={{ margin: 0, padding: '6px 0', borderBottom: '1px solid rgba(128, 128, 128, 0.1)' }}>
                            <span className="reg-conclusion-label">Variação:</span>
                            <span className="reg-conclusion-text" style={{ color: data.cv <= 25 ? '#00A34F' : '#CE1126' }}>
                                {data.cv <= 25 ? 'Consistente (OK)' : 'Inconsistente (Ruim)'}
                            </span>
                        </div>

                        <div className="reg-conclusion-item" style={{ margin: 0, padding: '6px 0', borderBottom: '1px solid rgba(128, 128, 128, 0.1)' }}>
                            <span className="reg-conclusion-label">Tendência:</span>
                            <span className="reg-conclusion-text" style={{ color: getTrendColor(data.trend) }}>
                                {data.trend}
                            </span>
                        </div>

                        {target !== null && (
                            <div className="reg-conclusion-item" style={{ margin: 0, padding: '6px 0' }}>
                                <span className="reg-conclusion-label">Meta (Tgt):</span>
                                <span className="reg-conclusion-text" style={{ color: data.averageScore >= target ? '#00A34F' : '#CE1126' }}>
                                    {data.averageScore >= target ? 'Atingida' : 'Abaixo da Meta'} ({data.averageScore.toFixed(2)} vs {target})
                                </span>
                            </div>
                        )}
                    </div>

                    <p className="reg-conclusion-summary" style={{ fontSize: '0.65rem', opacity: 0.85, marginTop: '12px', paddingTop: '8px' }}>
                        <i className="bi bi-info-circle" style={{ marginRight: '4px' }}></i>
                        A análise de <b>Variação</b> e <b>Tendência</b> avalia o comportamento dos dados curante os meses selecionados, mas <b>não substitui nem altera</b> as notas reais (Scores) obtidas pelo fornecedor.
                    </p>
                </div>
            </div>
        </aside>
    );
};

export default RegressionPanel;
