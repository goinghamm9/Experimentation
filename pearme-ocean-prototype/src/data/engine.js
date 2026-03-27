import {
  FRUITS,
  VIBE_FRUIT, TWIN_FRUIT,
  VIBE_OCEAN, TWIN_OCEAN, VIBE_OCEAN_Q4, ENERGY_OCEAN,
} from './scoring.js';

const FRUIT_KEYS = Object.keys(FRUITS);
const OCEAN_KEYS = ['O', 'C', 'E', 'A', 'N'];

// ── Accumulate OCEAN from a selection array + a weight map ────────────────────
function accumulateOCEAN(selections, weightMap, acc) {
  for (const sel of selections) {
    const w = weightMap[sel];
    if (!w) continue;
    for (const k of OCEAN_KEYS) acc[k] = (acc[k] || 0) + (w[k] || 0);
  }
}

// ── Accumulate fruit scores from a selection array + a weight map ─────────────
function accumulateFruit(selections, weightMap, acc) {
  for (const sel of selections) {
    const w = weightMap[sel];
    if (!w) continue;
    for (const [fruit, score] of Object.entries(w)) {
      acc[fruit] = (acc[fruit] || 0) + score;
    }
  }
}

// ── Compute live OCEAN from current partial answers ───────────────────────────
export function computeOCEAN(answers) {
  const acc = { O: 0, C: 0, E: 0, A: 0, N: 0 };
  if (answers.styleVibes?.length)  accumulateOCEAN(answers.styleVibes,  VIBE_OCEAN,    acc);
  if (answers.styleTwins?.length)  accumulateOCEAN(answers.styleTwins,  TWIN_OCEAN,    acc);
  if (answers.vibeCheck?.length)   accumulateOCEAN(answers.vibeCheck,   VIBE_OCEAN_Q4, acc);
  if (answers.energy?.length)      accumulateOCEAN(answers.energy,      ENERGY_OCEAN,  acc);

  // Normalize to 0-1 using a ±2 clamp → [0,1]
  const normalized = {};
  for (const k of OCEAN_KEYS) {
    normalized[k] = Math.min(1, Math.max(0, (acc[k] + 2) / 4));
  }
  return normalized;
}

// ── Compute final results ─────────────────────────────────────────────────────
export function computeResults(answers) {
  // Fruit accumulation (vibes 35%, twins 35%)
  const fruitAcc = {};
  for (const k of FRUIT_KEYS) fruitAcc[k] = 0;

  if (answers.styleVibes?.length) accumulateFruit(answers.styleVibes, VIBE_FRUIT, fruitAcc);
  if (answers.styleTwins?.length) accumulateFruit(answers.styleTwins, TWIN_FRUIT, fruitAcc);

  // Sort and pick top 3
  const sorted = Object.entries(fruitAcc)
    .sort(([, a], [, b]) => b - a)
    .map(([key, score]) => ({ key, score, ...FRUITS[key] }));

  const [primary, rising, moon] = sorted;

  const ocean = computeOCEAN(answers);

  // Top 3 high OCEAN dimensions for Psych Signals
  const psychSignals = Object.entries(ocean)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)
    .map(([k]) => k);

  return { primary, rising, moon, ocean, psychSignals, fruitRanking: sorted };
}
