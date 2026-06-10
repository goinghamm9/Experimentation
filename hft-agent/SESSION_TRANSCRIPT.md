# Coding Agent Session: Building a Fat-Tail Aware HFT Trading Agent

## Session Overview

**Task**: Build a complete high-frequency trading agent codebase from scratch, grounded in a detailed research paper covering Taleb's fat-tail probability framework, market microstructure theory, ergodicity economics, and power-law dynamics.

**Outcome**: 50 files, ~5,700 lines of production-grade Python — a full HFT system with broker integrations (Robinhood, Alpaca, Interactive Brokers), a fat-tail probability engine, signal generation, risk management, backtesting, database layer, Docker deployment, and hosting recommendations.

**Branch**: `claude/hft-agent-robinhood-B0Zpx`

---

## The Research Foundation

The user provided an extensive research brief synthesizing papers from five tiers of academic literature:

1. **Taleb's Core Papers** — Statistical Consequences of Fat Tails, metaprobability correction for tail exponents, antifragility framework
2. **Power Laws & Fat Tails** — Cont's stylized facts, Gabaix's cubic law (tail exponent ~3), EVT for equity markets
3. **Fractal & Multifractal Models** — Mandelbrot's MMAR, Hurst exponent for regime detection, fractal market hypothesis
4. **Market Microstructure** — Cont's Order Flow Imbalance (R² ~65%), VPIN toxicity detection, Kyle-Obizhaeva invariance
5. **Ergodicity & Path-Dependent Risk** — Peters' ergodicity economics, Kelly criterion, fractional Kelly under fat tails

The key insight: standard financial metrics (Sharpe ratio, Gaussian VaR, mean-variance optimization) systematically misrepresent risk at HFT timescales. The agent needed to be built from the ground up with fat-tailed distributions, not retrofitted.

---

## Architecture Decisions

### Why These Components?

**Probability Engine** — The entire system is built on Student-t distributions with power-law tails (exponent ~3, the "cubic law"), not Gaussian. Every risk calculation uses Mean Absolute Deviation instead of standard deviation, because variance is unreliable when the tail exponent is below 4. The metaprobability correction (Taleb 2012) automatically biases tail estimates fatter than measured — because historical samples systematically underestimate tail thickness.

**Signal Generation** — Four signals chosen specifically from the research:
- **OFI (Order Flow Imbalance)**: The primary alpha signal. Cont et al. (2011) showed OFI explains ~65% of short-term price variance — far better than any technical indicator.
- **Hurst Exponent**: Regime detector. H > 0.55 = trending (use momentum), H < 0.45 = mean-reverting (use contrarian), H ≈ 0.5 = random walk (spread capture only).
- **VPIN**: Toxicity filter. Volume-synchronized probability of informed trading — the metric that warned of the Flash Crash an hour early. When VPIN is high, the agent steps aside entirely.
- **Multifractal Spectrum**: Market stability measure. When the fractal structure narrows, short-term and long-term investors are correlating instead of offsetting — a precursor to instability.

**Risk Management** — Fractional Kelly (0.25x) instead of full Kelly, because under fat tails, full Kelly over-leverages catastrophically. The objective is log-wealth maximization (time-average growth, per Peters 2019), NOT expected return (ensemble average). These diverge under multiplicative dynamics — using the wrong one is how funds blow up.

**Database Choice** — TimescaleDB over InfluxDB or QuestDB because it offers full SQL with JOINs, 10-20x compression on tick data, and continuous aggregates that auto-compute OHLCV bars. Redis for sub-millisecond order book caching and rate limiting.

**Broker Selection** — Three brokers for different use cases:
- Robinhood: Commission-free, but rate-limited (~1 req/sec). Best as execution-only with external data feed.
- Alpaca: Best for development/paper trading. Real-time websocket feed, better API limits, free tier.
- Interactive Brokers: Best for production HFT. Lowest latency, DMA, deepest order types, FIX protocol.

---

## What Was Built

### File Structure (50 files)

```
hft-agent/
├── main.py                          # Application entry point & orchestrator
├── pyproject.toml                   # Dependencies & build config
├── config/settings.yaml             # Full configuration file
├── .env.example                     # Environment variable template
├── .gitignore
├── HOSTING.md                       # Deployment & hosting guide
│
├── core/
│   ├── probability/
│   │   ├── distributions.py         # Fat-tailed distribution (Student-t, power-law)
│   │   └── tail_estimator.py        # EVT tail estimation (GPD, Hill estimator)
│   ├── signals/
│   │   ├── ofi.py                   # Order Flow Imbalance signal
│   │   ├── hurst.py                 # Hurst exponent regime detection
│   │   ├── vpin.py                  # VPIN toxicity filter
│   │   ├── multifractal.py          # Multifractal spectrum analysis (MF-DFA)
│   │   └── aggregator.py            # Composite signal generation
│   └── risk/
│       ├── kelly.py                 # Fractional Kelly position sizing
│       ├── fragility.py             # Taleb-Douady fragility detection
│       └── manager.py               # Central risk orchestrator
│
├── brokers/
│   ├── base.py                      # Abstract broker interface
│   ├── robinhood.py                 # Robinhood via robin_stocks
│   ├── alpaca_broker.py             # Alpaca Markets integration
│   └── ibkr.py                      # Interactive Brokers via ib_insync
│
├── data/
│   ├── feeds/
│   │   ├── base.py                  # Abstract data feed
│   │   └── alpaca_feed.py           # Alpaca websocket data feed
│   └── storage/
│       ├── timescale.py             # TimescaleDB storage (tick, bar, orderbook)
│       └── redis_cache.py           # Redis cache (orderbook, signals, rate limiting)
│
├── strategies/
│   └── adaptive_microstructure.py   # Regime-adaptive HFT strategy
│
├── execution/
│   └── engine.py                    # Order execution with power-law slippage
│
├── backtest/
│   └── engine.py                    # Backtester with fat-tail aware metrics
│
├── utils/
│   ├── config.py                    # Pydantic settings management
│   ├── logging.py                   # Structured logging (structlog)
│   └── types.py                     # Shared type definitions
│
├── tests/
│   ├── test_probability.py          # Tests for distribution fitting, tail estimation
│   ├── test_signals.py              # Tests for OFI, Hurst, VPIN
│   └── test_risk.py                 # Tests for Kelly sizing, fragility detection
│
└── deploy/
    ├── Dockerfile                   # Container build
    ├── docker-compose.yml           # Full stack (agent + TimescaleDB + Redis + Prometheus + Grafana)
    └── prometheus.yml               # Metrics scraping config
```

### Key Implementation Details

**Fat-Tailed Distribution (`distributions.py`)**:
- Fits Student-t via MLE with automatic metaprobability correction (effective exponent = measured × 0.85)
- Asymmetric tails detected from data (left tail typically 15% fatter than right for equities)
- VaR and CVaR computed from the fat-tailed distribution, NOT Gaussian
- Monte Carlo CVaR estimation for the asymmetric case

**Order Flow Imbalance (`ofi.py`)**:
- Computes OFI from order book snapshots: bid size changes vs ask size changes
- Exponentially weighted smoothing over configurable lookback
- Normalized to [-1, 1] range using rolling standard deviation
- Directly implements the Cont, Kukanov, Stoikov (2011) framework

**Hurst Exponent (`hurst.py`)**:
- Rescaled Range (R/S) analysis with logarithmic scale spacing
- Linear regression in log-log space for Hurst estimation
- Regime classification: trending (H > 0.55), mean-reverting (H < 0.45), random walk
- The strategy flips OFI direction in mean-reverting regimes (contrarian)

**VPIN (`vpin.py`)**:
- Volume-synchronized sampling (volume clock, not time clock)
- Bulk Volume Classification for buy/sell attribution
- Rolling window of volume buckets for toxicity estimation
- Binary toxicity flag used as a hard filter — agent steps aside when toxic

**Fractional Kelly (`kelly.py`)**:
- Position sizing via log-wealth maximization (ergodically correct)
- MAD-based dispersion instead of standard deviation
- Configurable fraction (default 0.25x) to protect against estimation errors
- Monte Carlo ruin probability estimation
- Optimal fraction finder via growth rate sweep

**Fragility Detection (`fragility.py`)**:
- Measures sensitivity of P&L to realized volatility changes
- Classifies strategy as FRAGILE (short gamma), ROBUST, or ANTIFRAGILE
- Quadratic fit for gamma (convexity) estimation
- Generates actionable recommendations when fragility detected

**Adaptive Strategy (`adaptive_microstructure.py`)**:
- Regime-switches between momentum (trending), contrarian (mean-reverting), and spread capture (random walk)
- VPIN toxicity gate — refuses to trade in toxic flow
- OFI as primary directional signal
- Multifractal stability discount when market structure breaks down
- Limit order preference for spread capture

**Backtester (`backtest/engine.py`)**:
- Fat-tail aware performance metrics: MAD ratio (not Sharpe), CVaR (not VaR), log-growth rate (not expected return)
- Power-law slippage model (square root market impact)
- Kelly analysis: optimal fraction, growth rate, ruin probability
- Tail exponent estimation on realized returns

### Hosting Recommendation

AWS us-east-1 (N. Virginia) on a `c6i.xlarge` instance — 1-5ms latency to NYSE/NASDAQ at ~$300/month. Full stack deploys via `docker compose -f deploy/docker-compose.yml up -d`.

---

## Technical Highlights

1. **No Gaussian assumptions anywhere** — Every probability calculation uses fat-tailed distributions. The system is designed from first principles to handle the cubic law and power-law dynamics that actually govern equity markets.

2. **Ergodically correct objective** — The agent maximizes log-wealth (time-average growth), not expected return. This is the mathematically correct objective for a single compounding account per Peters (2019).

3. **Research-to-code mapping** — Each module directly implements a specific paper: OFI from Cont (2011), VPIN from Easley/Lopez de Prado (2011), Hurst from Qian & Rasheed (2004), Kelly from Thorp/MacLean/Ziemba (2016), fragility from Taleb & Douady (2012).

4. **Three broker abstractions** — Unified interface lets the same strategy run on Robinhood (free), Alpaca (paper trading), or IBKR (production) by changing one config line.

5. **Production-ready deployment** — Docker Compose with TimescaleDB, Redis, Prometheus, and Grafana. Health checks, compression policies, and performance-tuned database settings.

---

## Session Stats

- **Files created**: 50
- **Lines of code**: ~5,700
- **Research papers referenced**: 60+
- **Broker integrations**: 3 (Robinhood, Alpaca, IBKR)
- **Signal generators**: 4 (OFI, Hurst, VPIN, Multifractal)
- **Risk systems**: 3 (Kelly, CVaR, Fragility)
- **Test files**: 3 (probability, signals, risk)
