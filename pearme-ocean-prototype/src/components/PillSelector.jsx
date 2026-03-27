export default function PillSelector({ options, selected, onToggle, max = 3 }) {
  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: 10,
      justifyContent: 'center',
    }}>
      {options.map((opt) => {
        const active = selected.includes(opt);
        const disabled = !active && selected.length >= max;
        return (
          <button
            key={opt}
            onClick={() => !disabled && onToggle(opt)}
            style={{
              padding: '10px 18px',
              borderRadius: 99,
              border: active
                ? '1.5px solid var(--accent)'
                : '1.5px solid rgba(255,255,255,0.12)',
              background: active
                ? 'rgba(184,204,106,0.15)'
                : 'rgba(255,255,255,0.04)',
              color: active ? 'var(--accent)' : disabled ? 'rgba(240,237,232,0.25)' : 'var(--text)',
              fontFamily: 'DM Sans, sans-serif',
              fontSize: 14,
              fontWeight: active ? 600 : 400,
              cursor: disabled ? 'not-allowed' : 'pointer',
              transition: 'all 0.18s ease',
              letterSpacing: '0.01em',
              outline: 'none',
              transform: active ? 'scale(1.02)' : 'scale(1)',
            }}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}
