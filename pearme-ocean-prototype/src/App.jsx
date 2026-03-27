import { useState } from 'react';
import './index.css';
import Intro from './pages/Intro.jsx';
import Questionnaire from './pages/Questionnaire.jsx';
import Results from './pages/Results.jsx';
import { computeResults } from './data/engine.js';

export default function App() {
  const [screen, setScreen] = useState('intro'); // intro | quiz | results
  const [answers, setAnswers] = useState(null);
  const [results, setResults] = useState(null);

  const handleStart = () => setScreen('quiz');

  const handleComplete = (ans) => {
    const r = computeResults(ans);
    setAnswers(ans);
    setResults(r);
    setScreen('results');
  };

  if (screen === 'intro')   return <Intro onStart={handleStart} />;
  if (screen === 'quiz')    return <Questionnaire onComplete={handleComplete} />;
  if (screen === 'results') return <Results answers={answers} results={results} />;
  return null;
}
