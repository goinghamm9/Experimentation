"""Plain-English glossary shown in the dashboard. Each entry: what it is, why it is here, source."""

CONCEPTS: dict[str, dict[str, str]] = {
    "barbell": {
        "title": "Barbell portfolio",
        "plain": "Most of the money sits in something that almost cannot lose (short-term T-bills). "
        "A small, capped slice takes real risk. The worst case is bounded by the size of the slice, "
        "not by a forecast.",
        "why": "Taleb's answer to not knowing the tails: make the damage from being wrong small and known in advance.",
        "source": "Taleb, Antifragile (2012); The Black Swan, 2nd ed.",
    },
    "fat_tails": {
        "title": "Fat tails",
        "plain": "Big market moves happen far more often than the bell curve says. A '5-sigma' day that "
        "should occur once in millennia shows up every few years.",
        "why": "Every risk number here assumes fat tails (Student-t, power-law exponent around 3), never a bell curve.",
        "source": "Mandelbrot (1963); Gabaix (2009); Taleb, Statistical Consequences of Fat Tails (2020)",
    },
    "metaprobability": {
        "title": "Metaprobability haircut",
        "plain": "We cannot measure how fat the tail is precisely, and errors run one way: tails look thinner "
        "than they are. So the measured tail exponent is cut by 15% before it is used.",
        "why": "Uncertainty about the model is itself a risk; it should make you more careful, not less.",
        "source": "Taleb (2012), 'How we tend to overestimate power-law tail exponents'",
    },
    "expected_shortfall": {
        "title": "Expected shortfall (ES99)",
        "plain": "The average loss on the worst 1% of days. Value-at-Risk only tells you where the bad days "
        "start; ES tells you how bad they get.",
        "why": "Position sizes and the portfolio risk cap are set from ES, using the worse of the historical "
        "and the fat-tailed model estimate.",
        "source": "Artzner et al. (1999); Acerbi & Tasche (2002)",
    },
    "mad": {
        "title": "Mean absolute deviation (MAD)",
        "plain": "Average distance from typical. Unlike standard deviation it does not square outliers, so one "
        "crash does not swamp the estimate, and it exists even when variance does not.",
        "why": "Volatility, the MAD ratio and the Student-t scale all come from MAD.",
        "source": "Taleb (2020), ch. 4",
    },
    "kelly_ergodicity": {
        "title": "Fractional Kelly and ergodicity",
        "plain": "You live one path through time, not the average of many parallel worlds. The growth rate that "
        "matters is the average of log returns. Betting the full amount that maximises it is fragile to "
        "estimation error, so we cap exposure at a quarter of it.",
        "why": "The Kelly cap can only reduce the risky sleeve, never increase it.",
        "source": "Kelly (1956); Peters, 'The ergodicity problem in economics', Nature Physics (2019)",
    },
    "trend": {
        "title": "Trend following (time-series momentum)",
        "plain": "Hold an asset while its own price has been rising over the past 1-12 months, sized so each "
        "asset contributes similar tail risk. Trend following has historically done well in long crashes, "
        "which gives it a convex payoff without buying options.",
        "why": "It is the risky end of the barbell. Long-only because the Robinhood agent account cannot short.",
        "source": "Moskowitz, Ooi & Pedersen (2012); Hurst, Ooi & Pedersen (2017)",
    },
    "hurst": {
        "title": "DFA Hurst exponent",
        "plain": "Measures whether moves tend to continue (above 0.5) or reverse (below 0.5). Used only as a "
        "mild size multiplier, and the walk-forward test decides whether it is used at all.",
        "why": "Detrended fluctuation analysis is more robust than the older rescaled-range method on short, "
        "fat-tailed samples.",
        "source": "Peng et al. (1994); Mandelbrot & Van Ness (1968)",
    },
    "convexity": {
        "title": "Fragility and convexity test",
        "plain": "Does the strategy gain more from big market moves than it loses (convex, antifragile) or the "
        "reverse (fragile)? Measured by the curvature of monthly strategy returns against the market.",
        "why": "Taleb and Douady define fragility as a concave response to stress. This checks it on real returns.",
        "source": "Taleb & Douady (2013), Quantitative Finance; Treynor & Mazuy (1966)",
    },
    "gauge": {
        "title": "Gauge attribution (Malaney-Weinstein)",
        "plain": "Splits growth into three parts. Exposure: what you would have made holding average weights. "
        "Timing: what came from changing weights along the way (the path-dependent part, or holonomy). "
        "Convexity: the gain from rebalancing a diversified mix. Timing and convexity do not change "
        "if you measure in T-bills instead of dollars, which is what makes them honest measures of skill.",
        "why": "Malaney & Weinstein showed price indices are connections whose curvature comes from changing "
        "preferences. Here the 'preferences' are portfolio weights.",
        "source": "Malaney, 'The Index Number Problem: A Differential Geometric Approach' (Harvard PhD, 1996); "
        "Weinstein & Malaney, 'The Economic Index Problem'",
    },
    "walk_forward": {
        "title": "Walk-forward validation",
        "plain": "Each year, choose settings using only the previous three years, then trade the next year blind. "
        "Only those blind years are reported. It is the closest a backtest gets to real trading.",
        "why": "A backtest tuned on the whole history always looks good and means nothing.",
        "source": "Pardo (2008); Bailey, Borwein, Lopez de Prado & Zhu (2014)",
    },
    "bootstrap": {
        "title": "Bootstrap probability",
        "plain": "Reshuffle the blind-year returns in monthly blocks thousands of times and count how often the "
        "strategy still beats the comparison. Near 50% means you cannot tell them apart.",
        "why": "One historical path is one sample. This shows how much of the result could be luck.",
        "source": "Politis & Romano (1994), stationary bootstrap",
    },
}
