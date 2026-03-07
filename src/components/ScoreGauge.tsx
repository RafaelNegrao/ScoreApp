import React from 'react';

interface ScoreGaugeProps {
    title: string;
    value: number | null;
    target?: number;
    isPercentage?: boolean;
    isCV?: boolean;
}

const ScoreGauge: React.FC<ScoreGaugeProps> = ({ title, value, target = 8.7, isPercentage = false, isCV = false }) => {
    const cx = 65, cy = 55;
    const r = 40;
    const sw = 8;

    // Se for porcentagem ou CV, o valor máximo é 100, senão 10
    const max = isPercentage || isCV ? 100 : 10;

    const displayValue = value === null ? 0 : value;
    const clamped = Math.min(Math.max(displayValue, 0), max);

    // Se for CV, a lógica inverte (<= 25 é bom, maior é ruim)
    let isGood = isCV ? clamped <= 25 : clamped >= target;

    const px = (deg: number) => cx + r * Math.cos((deg * Math.PI) / 180);
    const py = (deg: number) => cy - r * Math.sin((deg * Math.PI) / 180);

    const arc = (a1: number, a2: number) => {
        const la = (a1 - a2) > 180 ? 1 : 0;
        return `M ${px(a1).toFixed(1)} ${py(a1).toFixed(1)} A ${r} ${r} 0 ${la} 1 ${px(a2).toFixed(1)} ${py(a2).toFixed(1)}`;
    };

    const g = 2; // gap
    // Needle points left (180) for 0, right (0) for max
    const ndeg = 180 - (clamped / max) * 180;
    const nrad = (ndeg * Math.PI) / 180;
    const nlen = r - sw / 2 - 3;
    const nx = cx + nlen * Math.cos(nrad);
    const ny = cy - nlen * Math.sin(nrad);

    // Colors for Scores 
    // CV: lower is better (Green <= 25, Yellow <= 50, Red > 50)
    // Score: higher is better (Right is Green)
    const getCvColor = (val: number) => val <= 25 ? '#00A34F' : (val <= 50 ? '#FFB81C' : '#CE1126');
    const getScoreColor = (val: number) => isGood ? '#00A34F' : (val >= target * 0.8 ? '#FFB81C' : '#CE1126');

    const ncolor = value === null ? 'rgba(148,163,184,0.4)' : (isCV ? getCvColor(clamped) : getScoreColor(clamped));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', padding: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase' }}>
                {title}
            </span>
            <div style={{
                width: '100%',
                maxWidth: '180px',
                display: 'flex',
                justifyContent: 'center',
                flexGrow: 1,
                alignItems: 'center'
            }}>
                <svg viewBox="0 0 130 90" width="100%" height="auto" style={{ display: 'block' }}>
                    {isCV ? (
                        <>
                            {/* CV Arcs: Green (180-135), Yellow (135-90), Red (90-0) */}
                            <path d={arc(180, 135 + g)} stroke="#00A34F" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                            <path d={arc(135 - g, 90 + g)} stroke="#FFB81C" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                            <path d={arc(90 - g, 0)} stroke="#CE1126" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                        </>
                    ) : (
                        <>
                            {/* Score Arcs: Red (180-120), Yellow (120-60), Green (60-0) */}
                            <path d={arc(180, 120 + g)} stroke="#CE1126" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                            <path d={arc(120 - g, 60 + g)} stroke="#FFB81C" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                            <path d={arc(60 - g, 0)} stroke="#00A34F" strokeWidth={sw} fill="none" strokeLinecap="butt" />
                        </>
                    )}

                    {value !== null && (
                        <>
                            <line x1={cx} y1={cy} x2={nx.toFixed(1)} y2={ny.toFixed(1)} stroke={ncolor} strokeWidth="2.5" strokeLinecap="round" />
                            <circle cx={cx} cy={cy} r={3.5} fill="var(--card-bg)" stroke={ncolor} strokeWidth={1.5} />
                        </>
                    )}

                    <text x={cx - r - 2} y={cy + 10} textAnchor="middle" fontSize="6" fill="rgba(148,163,184,0.6)">0</text>
                    <text x={cx + r + 2} y={cy + 10} textAnchor="middle" fontSize="6" fill="rgba(148,163,184,0.6)">{max}</text>

                    <text x={cx} y={cy + 16} textAnchor="middle" fontSize="14" fontWeight="800" fill={value === null ? 'var(--text-muted)' : ncolor}>
                        {value === null ? '-' : (isPercentage || isCV ? `${clamped.toFixed(1)}%` : clamped.toFixed(1))}
                    </text>
                    {value !== null && (
                        <text x={cx} y={cy + 29} textAnchor="middle" fontSize="11" fontWeight="600" fill="rgba(148,163,184,0.8)">
                            {isGood ? '✓ OK' : '⚠ Ruim'}
                        </text>
                    )}
                </svg>
            </div>
        </div>
    );
};

export default ScoreGauge;
