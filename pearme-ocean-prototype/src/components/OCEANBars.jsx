import { OCEAN_LABELS } from '../data/scoring.js';

const DIM_COLORS = {
  O: '#B8CC6A',
  C: '#8B5CF6',
  E: '#F59E0B',
  A: '#34D399',
  N: '#60A5FA',
};

export default function OCEANBars({ ocean, animate = false, compact = false }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 8 : 12 }}>
      {['O','C','E','A','N'].map((k) => {
        const { label, icon } = OCEAN_LABELS[k];
        const pct = Math.round((ocean[k] ?? 0.5) * 100);
        return (
          <div key={k}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: compact ? 11 : 13, color: 'var(--muted)', fontFamily: 'DM Sans, sans-serif' }}>
                {icon} {label}
              </span>
              <span style={{ fontSize: compact ? 11 : 13, color: DIM_COLORS[k], fontWeight: 600 }}>
                {pct}
              </span>
            </div>
            <div style={{
              height: compact ? 5 : 7,
              background: 'rgba(255,255,255,0.07)',
              borderRadius: 99,
              overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${pct}%`,
                background: `linear-gradient(90deg, ${DIM_COLORS[k]}80, ${DIM_COLORS[k]})`,
                borderRadius: 99,
                transition: animate ? 'width 0.8s cubic-bezier(0.4,0,0.2,1)' : 'width 0.3s ease',
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
