import { useState } from 'react';
import ProgressBar from '../components/ProgressBar.jsx';
import PillSelector from '../components/PillSelector.jsx';
import ContinueButton from '../components/ContinueButton.jsx';
import OCEANBars from '../components/OCEANBars.jsx';
import { computeOCEAN } from '../data/engine.js';
import {
  STYLE_VIBES, STYLE_TWINS, VIBES, ENERGIES,
} from '../data/scoring.js';

const TOTAL = 5;

export default function Questionnaire({ onComplete }) {
  const [step, setStep] = useState(1);
  const [answers, setAnswers] = useState({
    name: '',
    styleVibes: [],
    styleTwins: [],
    vibeCheck: [],
    energy: [],
  });

  const ocean = computeOCEAN(answers);

  const canContinue = () => {
    if (step === 1) return answers.name.trim().length > 0;
    if (step === 2) return answers.styleVibes.length > 0;
    if (step === 3) return answers.styleTwins.length > 0;
    if (step === 4) return answers.vibeCheck.length > 0;
    if (step === 5) return answers.energy.length > 0;
    return false;
  };

  const handleNext = () => {
    if (step < TOTAL) setStep((s) => s + 1);
    else onComplete(answers);
  };

  const toggleMulti = (field, val, max = 3) => {
    setAnswers((prev) => {
      const cur = prev[field];
      if (cur.includes(val)) return { ...prev, [field]: cur.filter((x) => x !== val) };
      if (cur.length >= max) return prev;
      return { ...prev, [field]: [...cur, val] };
    });
  };

  const questions = [
    {
      title: `What's your first name?`,
      subtitle: "We'll use it to personalize your profile.",
      content: (
        <input
          type="text"
          placeholder="Type your name..."
          value={answers.name}
          onChange={(e) => setAnswers((p) => ({ ...p, name: e.target.value }))}
          onKeyDown={(e) => e.key === 'Enter' && canContinue() && handleNext()}
          autoFocus
          style={{
            width: '100%',
            maxWidth: 360,
            padding: '14px 20px',
            background: 'var(--surface2)',
            border: '1.5px solid rgba(255,255,255,0.12)',
            borderRadius: 'var(--radius)',
            color: 'var(--text)',
            fontFamily: 'DM Sans, sans-serif',
            fontSize: 18,
            outline: 'none',
            textAlign: 'center',
            transition: 'border-color 0.2s',
          }}
          onFocus={(e) => (e.target.style.borderColor = 'var(--accent)')}
          onBlur={(e) => (e.target.style.borderColor = 'rgba(255,255,255,0.12)')}
        />
      ),
    },
    {
      title: 'Pick up to 3 style vibes',
      subtitle: 'Choose the aesthetics that feel most like you right now.',
      content: (
        <PillSelector
          options={STYLE_VIBES}
          selected={answers.styleVibes}
          onToggle={(v) => toggleMulti('styleVibes', v)}
        />
      ),
    },
    {
      title: 'Pick your style twins (up to 3)',
      subtitle: 'Whose energy do you gravitate toward most?',
      content: (
        <PillSelector
          options={STYLE_TWINS}
          selected={answers.styleTwins}
          onToggle={(v) => toggleMulti('styleTwins', v)}
        />
      ),
    },
    {
      title: 'Vibe check — pick 3',
      subtitle: 'Which of these feels like your current era?',
      content: (
        <PillSelector
          options={VIBES}
          selected={answers.vibeCheck}
          onToggle={(v) => toggleMulti('vibeCheck', v)}
        />
      ),
    },
    {
      title: 'What energy are you walking in with?',
      subtitle: 'Pick up to 3 that resonate.',
      content: (
        <PillSelector
          options={ENERGIES}
          selected={answers.energy}
          onToggle={(v) => toggleMulti('energy', v)}
        />
      ),
    },
  ];

  const q = questions[step - 1];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{
        padding: '16px 24px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <span style={{ fontFamily: 'Playfair Display, serif', fontSize: 20, color: 'var(--accent)', letterSpacing: '-0.02em' }}>
          pearme
        </span>
        <span style={{ fontSize: 12, color: 'var(--muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Fruit Psych Profile
        </span>
      </div>

      <ProgressBar step={step} total={TOTAL} />

      {/* Main layout */}
      <div style={{
        display: 'flex',
        flex: 1,
        gap: 0,
        maxWidth: 1100,
        margin: '0 auto',
        width: '100%',
        padding: '0 20px',
      }}>
        {/* Question area */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px 20px',
          gap: 32,
        }}>
          <div key={step} className="fade-up" style={{ textAlign: 'center', maxWidth: 600, width: '100%' }}>
            <h2 style={{
              fontFamily: 'Playfair Display, serif',
              fontSize: 'clamp(22px, 3vw, 32px)',
              fontWeight: 700,
              marginBottom: 10,
              lineHeight: 1.2,
              color: 'var(--text)',
            }}>
              {q.title}
            </h2>
            <p style={{ color: 'var(--muted)', fontSize: 15, marginBottom: 32 }}>{q.subtitle}</p>
            {q.content}
          </div>

          <ContinueButton onClick={handleNext} disabled={!canContinue()} />
        </div>

        {/* Live OCEAN sidebar */}
        <div style={{
          width: 220,
          flexShrink: 0,
          padding: '40px 0 40px 20px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}>
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            padding: '20px 16px',
          }}>
            <p style={{
              fontSize: 10,
              color: 'var(--muted)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              marginBottom: 16,
              textAlign: 'center',
            }}>
              Live Profile ✦
            </p>
            <OCEANBars ocean={ocean} compact />
          </div>
        </div>
      </div>
    </div>
  );
}
