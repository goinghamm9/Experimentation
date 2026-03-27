import ContinueButton from '../components/ContinueButton.jsx';

export default function Intro({ onStart }) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
      textAlign: 'center',
    }}>
      {/* Decorative circles */}
      <div style={{
        position: 'fixed', top: '-120px', right: '-120px',
        width: 400, height: 400,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(184,204,106,0.06) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'fixed', bottom: '-80px', left: '-80px',
        width: 300, height: 300,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <div className="fade-up">
        <div style={{ fontSize: 64, marginBottom: 20, filter: 'drop-shadow(0 0 20px rgba(184,204,106,0.3))' }}>
          🍐🍇🍒🥭🍌
        </div>
        <h1 style={{
          fontFamily: 'Playfair Display, serif',
          fontSize: 'clamp(32px, 6vw, 56px)',
          fontWeight: 700,
          color: 'var(--text)',
          marginBottom: 12,
          lineHeight: 1.1,
          letterSpacing: '-0.02em',
        }}>
          Your Fruit<br />
          <span style={{
            background: 'linear-gradient(135deg, #B8CC6A, #8B5CF6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            Psych Profile
          </span>
        </h1>
        <p style={{
          fontSize: 'clamp(15px, 2vw, 18px)',
          color: 'var(--muted)',
          maxWidth: 440,
          lineHeight: 1.7,
          marginBottom: 40,
        }}>
          5 questions. A personality score rooted in psychology.
          Discover your Primary, Rising & Moon fruit — and what they say about your style energy.
        </p>
        <ContinueButton onClick={onStart} label="Start your profile →" />
        <p style={{ marginTop: 20, fontSize: 12, color: 'rgba(240,237,232,0.25)' }}>
          ~2 minutes · No account needed
        </p>
      </div>
    </div>
  );
}
