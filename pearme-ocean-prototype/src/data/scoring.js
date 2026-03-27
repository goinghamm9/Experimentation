// ── Fruit archetypes ──────────────────────────────────────────────────────────
export const FRUITS = {
  PEAR:   { emoji: '🍐', name: 'Pear',   tagline: 'Quiet Confidence',       psychName: 'The Calm Architect',       psychEnergy: 'Grounded',                   narrative: 'Your style energy is Grounded. You make decisions with intention, build systems that work, and show up composed.' },
  GRAPE:  { emoji: '🍇', name: 'Grape',  tagline: 'Soft Armor',              psychName: 'The Depth Seeker',         psychEnergy: 'Introspective + Original',    narrative: 'Your style energy is Introspective + Original. You process life through art, music, and texture.' },
  CHERRY: { emoji: '🍒', name: 'Cherry', tagline: 'Main Character Energy',   psychName: 'The Emotional Storyteller', psychEnergy: 'Expressive + Magnetic',      narrative: 'Your energy is Expressive + Magnetic. You feel everything and want your clothes to say it out loud.' },
  MANGO:  { emoji: '🥭', name: 'Mango',  tagline: 'Power Moves',             psychName: 'The Forward Mover',        psychEnergy: 'Driven + Polished',           narrative: 'Your style energy is Driven + Polished. You dress for what you\'re about to do, not for the mirror.' },
  BANANA: { emoji: '🍌', name: 'Banana', tagline: 'Golden Hour Soul',        psychName: 'The Warmth Weaver',        psychEnergy: 'Warm + Romantic',             narrative: 'Your style energy is Warm + Romantic. You romanticize life and dress for how you want the day to feel.' },
};

// ── OCEAN labels ──────────────────────────────────────────────────────────────
export const OCEAN_LABELS = {
  O: { label: 'Aesthetic Depth',  icon: '✨' },
  C: { label: 'Structure Seeker', icon: '🧱' },
  E: { label: 'Social Voltage',   icon: '⚡' },
  A: { label: 'Warmth Carrier',   icon: '🌿' },
  N: { label: 'Emotional Richness', icon: '🌊' },
};

// ── Style vibes ───────────────────────────────────────────────────────────────
export const STYLE_VIBES = [
  'Luxe Minimalist',
  'Thrift Witch',
  'Hot Villain Era',
  'IG Baddie',
  'Feral Cottagecore',
  'Clean Girl',
  'Alt Princess',
  'Coquette',
  'Early 2000s It-Girl',
  'Coastal Cowgirl',
];

export const STYLE_TWINS = [
  'Sofia Richie',
  'Chappell Roan',
  'Rosalía',
  'Billie Eilish',
  'Dua Lipa',
  'Hailey Bieber',
  'Doechii',
  'Kacey Musgraves',
  'Sabrina Carpenter',
  'Nicole Richie',
];

export const VIBES = [
  'Oat milk elite',
  'Cowgirl by moodboard only',
  'Glam with feelings',
  'Art school drop-in',
  'Cardio in Chrome Hearts',
  'Heartbreak core',
  'Soft power era',
  'Slick bun energy',
  'Romantic but unbothered',
  'Zillennial spiral',
];

export const ENERGIES = [
  'Polished + put together',
  'Warm + approachable',
  'Creative energy',
  'Sporty spice vibes',
  'Fun + lowkey flirty',
  'Glam with a capital G',
  'Quiet luxury chic',
  'Confident AF',
  'Playful + unpredictable',
  'A little edgy',
];

// ── Fruit weights (35% each for vibes + twins) ────────────────────────────────
export const VIBE_FRUIT = {
  'Luxe Minimalist':    { PEAR: 0.9, CHERRY: 0.1 },
  'Thrift Witch':       { BANANA: 0.8, GRAPE: 0.2 },
  'Hot Villain Era':    { GRAPE: 0.8, CHERRY: 0.2 },
  'IG Baddie':          { MANGO: 0.7, CHERRY: 0.3 },
  'Feral Cottagecore':  { BANANA: 0.9, PEAR: 0.1 },
  'Clean Girl':         { PEAR: 0.7, MANGO: 0.2, CHERRY: 0.1 },
  'Alt Princess':       { CHERRY: 0.7, GRAPE: 0.3 },
  'Coquette':           { CHERRY: 0.9, BANANA: 0.1 },
  'Early 2000s It-Girl':{ CHERRY: 0.8, MANGO: 0.2 },
  'Coastal Cowgirl':    { BANANA: 0.7, MANGO: 0.2, PEAR: 0.1 },
};

export const TWIN_FRUIT = {
  'Sofia Richie':     { PEAR: 0.9, MANGO: 0.1 },
  'Chappell Roan':    { GRAPE: 0.8, CHERRY: 0.2 },
  'Rosalía':          { GRAPE: 0.7, CHERRY: 0.3 },
  'Billie Eilish':    { MANGO: 0.6, GRAPE: 0.4 },
  'Dua Lipa':         { CHERRY: 0.7, MANGO: 0.3 },
  'Hailey Bieber':    { PEAR: 0.8, MANGO: 0.2 },
  'Doechii':          { MANGO: 0.8, GRAPE: 0.2 },
  'Kacey Musgraves':  { BANANA: 0.8, PEAR: 0.2 },
  'Sabrina Carpenter':{ CHERRY: 0.9, BANANA: 0.1 },
  'Nicole Richie':    { BANANA: 0.7, PEAR: 0.3 },
};

// ── OCEAN weights ─────────────────────────────────────────────────────────────
export const VIBE_OCEAN = {
  'Luxe Minimalist':    { O: 0,    C: 0.35, E: 0,    A: 0.1,  N: -0.25 },
  'Thrift Witch':       { O: 0.3,  C: -0.1, E: -0.1, A: 0,    N: 0.2   },
  'Hot Villain Era':    { O: 0.2,  C: -0.1, E: 0.2,  A: -0.2, N: 0.2   },
  'IG Baddie':          { O: 0,    C: 0.2,  E: 0.3,  A: -0.15,N: 0     },
  'Feral Cottagecore':  { O: 0.25, C: 0,    E: -0.1, A: 0.3,  N: -0.15 },
  'Clean Girl':         { O: 0,    C: 0.3,  E: 0,    A: 0.15, N: -0.2  },
  'Alt Princess':       { O: 0.3,  C: -0.1, E: 0.1,  A: 0,    N: 0.2   },
  'Coquette':           { O: 0.1,  C: 0,    E: 0.3,  A: 0,    N: 0.2   },
  'Early 2000s It-Girl':{ O: 0,    C: 0.15, E: 0.3,  A: 0,    N: 0     },
  'Coastal Cowgirl':    { O: 0.2,  C: 0,    E: 0,    A: 0.25, N: -0.1  },
};

export const TWIN_OCEAN = {
  'Sofia Richie':     { O: -0.1, C: 0.3,  E: 0,    A: 0.2,  N: -0.2  },
  'Chappell Roan':    { O: 0.35, C: -0.1, E: 0,    A: 0,    N: 0.2   },
  'Rosalía':          { O: 0.3,  C: 0,    E: 0.1,  A: -0.1, N: 0.15  },
  'Billie Eilish':    { O: 0.15, C: 0.2,  E: 0.2,  A: -0.15,N: 0     },
  'Dua Lipa':         { O: 0.1,  C: 0,    E: 0.3,  A: 0,    N: 0.15  },
  'Hailey Bieber':    { O: -0.1, C: 0.3,  E: 0,    A: 0.2,  N: -0.2  },
  'Doechii':          { O: 0.2,  C: 0.2,  E: 0.25, A: -0.15,N: 0     },
  'Kacey Musgraves':  { O: 0.2,  C: 0,    E: 0,    A: 0.3,  N: -0.15 },
  'Sabrina Carpenter':{ O: 0.1,  C: 0,    E: 0.3,  A: 0,    N: 0.15  },
  'Nicole Richie':    { O: 0.15, C: 0.1,  E: 0,    A: 0.25, N: -0.1  },
};

export const VIBE_OCEAN_Q4 = {
  'Oat milk elite':          { O: 0,    C: 0.25, E: 0,    A: 0.2,  N: -0.2  },
  'Cowgirl by moodboard only':{ O: 0.2, C: 0,    E: 0,    A: 0.25, N: -0.1  },
  'Glam with feelings':      { O: 0.1,  C: 0,    E: 0.2,  A: 0,    N: 0.25  },
  'Art school drop-in':      { O: 0.35, C: -0.1, E: 0,    A: 0,    N: 0.2   },
  'Cardio in Chrome Hearts': { O: 0,    C: 0.25, E: 0.25, A: -0.1, N: 0     },
  'Heartbreak core':         { O: 0.1,  C: 0,    E: 0.15, A: 0,    N: 0.3   },
  'Soft power era':          { O: 0,    C: 0.3,  E: 0,    A: 0.2,  N: -0.2  },
  'Slick bun energy':        { O: 0,    C: 0.3,  E: 0.2,  A: -0.1, N: 0     },
  'Romantic but unbothered': { O: 0.2,  C: 0,    E: 0,    A: 0.3,  N: -0.15 },
  'Zillennial spiral':       { O: 0.3,  C: -0.15,E: 0,    A: 0,    N: 0.25  },
};

export const ENERGY_OCEAN = {
  'Polished + put together':  { O: 0,    C: 0.3,  E: 0,    A: 0,    N: -0.25 },
  'Warm + approachable':      { O: 0,    C: 0,    E: 0.1,  A: 0.35, N: -0.1  },
  'Creative energy':          { O: 0.35, C: -0.1, E: 0,    A: 0,    N: 0.15  },
  'Sporty spice vibes':       { O: 0,    C: 0.2,  E: 0.3,  A: -0.1, N: 0     },
  'Fun + lowkey flirty':      { O: 0.1,  C: 0,    E: 0.3,  A: 0.1,  N: 0.1   },
  'Glam with a capital G':    { O: 0.1,  C: 0,    E: 0.35, A: -0.05,N: 0.15  },
  'Quiet luxury chic':        { O: 0,    C: 0.35, E: -0.1, A: 0.1,  N: -0.2  },
  'Confident AF':             { O: 0,    C: 0.2,  E: 0.3,  A: -0.15,N: -0.1  },
  'Playful + unpredictable':  { O: 0.3,  C: -0.15,E: 0.2,  A: 0.1,  N: 0     },
  'A little edgy':            { O: 0.25, C: 0,    E: 0.1,  A: -0.1, N: 0.15  },
};
