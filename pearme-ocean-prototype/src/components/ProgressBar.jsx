export default function ProgressBar({ step, total }) {
  const pct = ((step - 1) / total) * 100;
  return (
    <div style={{ padding: '20px 24px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontSize: 12, color: 'var(--muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          Question {step} of {total}
        </span>
      </div>
      <div style={{
        height: 3,
        background: 'rgba(255,255,255,0.07)',
        borderRadius: 99,
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          background: 'linear-gradient(90deg, var(--accent), var(--accent2))',
          borderRadius: 99,
          transition: 'width 0.4s cubic-bezier(0.4,0,0.2,1)',
        }} />
      </div>
    </div>
  );
}
