export default function ContinueButton({ onClick, disabled, label = 'Continue →' }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '14px 40px',
        borderRadius: 99,
        border: 'none',
        background: disabled
          ? 'rgba(255,255,255,0.08)'
          : 'linear-gradient(135deg, #B8CC6A, #8B5CF6)',
        color: disabled ? 'rgba(240,237,232,0.3)' : '#0C0C0F',
        fontFamily: 'DM Sans, sans-serif',
        fontSize: 16,
        fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.2s ease',
        letterSpacing: '0.02em',
        animation: !disabled ? 'pulse-glow 2.5s infinite' : 'none',
        outline: 'none',
      }}
    >
      {label}
    </button>
  );
}
