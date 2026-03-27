import { useState, useEffect } from 'react';
import OCEANBars from '../components/OCEANBars.jsx';
import { OCEAN_LABELS } from '../data/scoring.js';

const RANK_LABELS = ['Primary', 'Rising', 'Moon'];
const RANK_COLORS = ['#B8CC6A', '#8B5CF6', '#60A5FA'];
const RANK_ICONS  = ['✦', '↑', '◎'];

function RevealCard({ children, delay = 0, style = {} }) {
  return (
    <div
      className="fade-up"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'both', ...style }}
    >
      {children}
    </div>
  );
}

function Card({ children, style = {} }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '28px 24px',
      ...style,
    }}>
      {children}
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <p style={{
      fontSize: 11,
      color: 'var(--muted)',
      letterSpacing: '0.12em',
      textTransform: 'uppercase',
      marginBottom: 16,
    }}>
      {children}
    </p>
  );
}

export default function Results({ answers, results }) {
  const { primary, rising, moon, ocean, psychSignals, fruitRanking } = results;
  const [showDev, setShowDev] = useState(false);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setRevealed(true), 100);
    return () => clearTimeout(t);
  }, []);

  const trio = [primary, rising, moon].map((f, i) => ({ ...f, rank: RANK_LABELS[i], color: RANK_COLORS[i], icon: RANK_ICONS[i] }));

  const devPayload = {
    name: answers.name,
    answers: {
      styleVibes: answers.styleVibes,
      styleTwins: answers.styleTwins,
      vibeCheck: answers.vibeCheck,
      energy: answers.energy,
    },
    fruitScores: Object.fromEntries(fruitRanking.map(f => [f.key, +f.score.toFixed(3)])),
    ocean: Object.fromEntries(Object.entries(ocean).map(([k,v]) => [k, +v.toFixed(3)])),
    result: { primary: primary?.key, rising: rising?.key, moon: moon?.key },
  };

  return (
    <div style={{ minHeight: '100vh', padding: '0 0 60px' }}>
      {/* Header */}
      <div style={{
        padding: '16px 24px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 0,
      }}>
        <span style={{ fontFamily: 'Playfair Display, serif', fontSize: 20, color: 'var(--accent)', letterSpacing: '-0.02em' }}>
          pearme
        </span>
        <span style={{ fontSize: 12, color: 'var(--muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Your Fruit Psych Profile
        </span>
      </div>

      <div style={{ maxWidth: 780, margin: '0 auto', padding: '48px 20px 0' }}>

        {/* ── Hero: Primary Fruit ── */}
        {revealed && (
          <RevealCard delay={0} style={{ textAlign: 'center', marginBottom: 48 }}>
            <p style={{ fontSize: 12, color: 'var(--muted)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 16 }}>
              {answers.name ? `${answers.name}'s` : 'Your'} Fruit Identity
            </p>
            <div style={{ fontSize: 72, lineHeight: 1, marginBottom: 12 }}>{primary?.emoji}</div>
            <h1 style={{
              fontFamily: 'Playfair Display, serif',
              fontSize: 'clamp(28px, 5vw, 48px)',
              fontWeight: 700,
              color: 'var(--text)',
              marginBottom: 8,
              lineHeight: 1.1,
            }}>
              {primary?.tagline}
            </h1>
            <p style={{ fontSize: 16, color: 'var(--muted)', marginBottom: 4 }}>
              You are <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{primary?.name}</span>
            </p>
          </RevealCard>
        )}

        {/* ── FruitScope Trio ── */}
        {revealed && (
          <RevealCard delay={200} style={{ marginBottom: 32 }}>
            <Card>
              <SectionLabel>FruitScope ✦</SectionLabel>
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                {trio.map((f, i) => f && (
                  <div key={i} style={{
                    flex: 1,
                    minWidth: 160,
                    background: 'var(--surface2)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '16px',
                    border: `1px solid ${f.color}30`,
                    textAlign: 'center',
                  }}>
                    <div style={{ fontSize: 28, marginBottom: 6 }}>{f.emoji}</div>
                    <div style={{
                      display: 'inline-block',
                      fontSize: 10,
                      fontWeight: 600,
                      letterSpacing: '0.1em',
                      textTransform: 'uppercase',
                      color: f.color,
                      background: `${f.color}18`,
                      borderRadius: 99,
                      padding: '3px 10px',
                      marginBottom: 8,
                    }}>
                      {f.icon} {f.rank}
                    </div>
                    <p style={{ fontFamily: 'Playfair Display, serif', fontSize: 15, fontWeight: 600, color: 'var(--text)' }}>
                      {f.name}
                    </p>
                    <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>{f.tagline}</p>
                  </div>
                ))}
              </div>
            </Card>
          </RevealCard>
        )}

        {/* ── Fruit Psych Profile ── */}
        {revealed && (
          <RevealCard delay={350} style={{ marginBottom: 32 }}>
            <Card style={{ borderLeft: `3px solid var(--accent)` }}>
              <SectionLabel>Fruit Psych Profile</SectionLabel>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
                <span style={{ fontSize: 36 }}>{primary?.emoji}</span>
                <div>
                  <h3 style={{
                    fontFamily: 'Playfair Display, serif',
                    fontSize: 22,
                    fontWeight: 700,
                    color: 'var(--text)',
                    marginBottom: 2,
                  }}>
                    {primary?.psychName}
                  </h3>
                  <span style={{
                    fontSize: 12,
                    color: 'var(--accent)',
                    background: 'rgba(184,204,106,0.12)',
                    padding: '3px 10px',
                    borderRadius: 99,
                    fontWeight: 600,
                  }}>
                    {primary?.psychEnergy}
                  </span>
                </div>
              </div>
              <p style={{ fontSize: 16, color: 'var(--muted)', lineHeight: 1.7 }}>
                {primary?.narrative}
              </p>
            </Card>
          </RevealCard>
        )}

        {/* ── OCEAN Bars ── */}
        {revealed && (
          <RevealCard delay={500} style={{ marginBottom: 32 }}>
            <Card>
              <SectionLabel>Your Psych Dimensions</SectionLabel>
              <OCEANBars ocean={ocean} animate />
            </Card>
          </RevealCard>
        )}

        {/* ── Psych Signals ── */}
        {revealed && (
          <RevealCard delay={650} style={{ marginBottom: 32 }}>
            <Card>
              <SectionLabel>Psych Signals</SectionLabel>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {psychSignals.map((k) => {
                  const { label, icon } = OCEAN_LABELS[k];
                  return (
                    <div key={k} style={{
                      padding: '10px 18px',
                      background: 'rgba(184,204,106,0.1)',
                      border: '1px solid rgba(184,204,106,0.3)',
                      borderRadius: 99,
                      fontSize: 14,
                      fontWeight: 500,
                      color: 'var(--accent)',
                    }}>
                      {icon} {label}
                    </div>
                  );
                })}
              </div>
            </Card>
          </RevealCard>
        )}

        {/* ── Disclaimer ── */}
        {revealed && (
          <RevealCard delay={750} style={{ marginBottom: 32 }}>
            <p style={{
              fontSize: 13,
              color: 'var(--muted)',
              textAlign: 'center',
              fontStyle: 'italic',
              padding: '0 20px',
              lineHeight: 1.6,
            }}>
              Your Fruit Psych Profile is for fun and self-discovery — not a clinical assessment.
            </p>
          </RevealCard>
        )}

        {/* ── Developer View ── */}
        {revealed && (
          <RevealCard delay={800}>
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 24 }}>
              <button
                onClick={() => setShowDev((v) => !v)}
                style={{
                  background: 'none',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--muted)',
                  fontFamily: 'DM Sans, sans-serif',
                  fontSize: 13,
                  padding: '8px 16px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  margin: '0 auto',
                }}
              >
                <span>{showDev ? '▲' : '▼'}</span> Developer View
              </button>
              {showDev && (
                <div className="fade-up" style={{ marginTop: 16 }}>
                  <pre style={{
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius)',
                    padding: '20px',
                    fontSize: 12,
                    color: '#B8CC6A',
                    overflowX: 'auto',
                    lineHeight: 1.6,
                    fontFamily: 'monospace',
                    textAlign: 'left',
                  }}>
                    {JSON.stringify(devPayload, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </RevealCard>
        )}
      </div>
    </div>
  );
}
