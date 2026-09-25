# Barbell Engine

A fat-tail aware portfolio engine for a Robinhood Agentic account. Most of the money sits in
T-bills; a capped slice follows trends across stock, bond, gold and commodity ETFs, sized by
expected shortfall under fat tails. It is validated walk-forward, runs a paper account, and hands
orders to Claude for execution on Robinhood with your approval.

**What it is not.** It is not high-frequency trading (Robinhood's agent interface is far too slow
for that) and it has no proven edge. On the only real data we could test with here (14 large tech
stocks, 2015-2022, out of sample) it grew 3.2%/yr with a 5.8% worst drawdown, while a naive barbell
at the same average exposure grew 4.9%/yr. That was a relentless bull market with V-shaped
recoveries, the worst case for trend timing. Run it on the default multi-asset universe (below) and
judge the out-of-sample numbers yourself before risking money.

## Quickstart

```bash
pip install -e ".[dev]"
python -m engine backtest            # downloads ~18 years of ETF prices, walk-forward test (~2-5 min)
python -m engine serve               # dashboard at http://127.0.0.1:8000
python -m engine paper init --capital 10000
python -m engine paper step          # run once per trading day after the close (or use the dashboard)
```

Prices come from Yahoo Finance with no key, or from Alpaca if `ALPACA_API_KEY`/`ALPACA_SECRET_KEY`
are set in `.env`. Offline: `python -m engine backtest --csv prices.csv` (long format
`symbol,date,close[,volume]` or wide `date,SPY,QQQ,...`).

Tests: `pytest` (43 tests, including a no-lookahead proof and the gauge invariance checks).

## Trading on Robinhood

The engine never places orders. Claude does, through Robinhood's official MCP server, after
showing you each order and its reason.

1. In the Robinhood app: **Agentic** tab -> fund the Agentic account (separate from your main
   portfolio, cash only).
2. From this folder: `claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading`
   and sign in when Claude Code prompts (desktop).
3. In Claude Code, from this folder: *"run the robinhood-rebalance skill"*. Claude reads your
   Agentic positions, runs `python -m engine plan`, shows the orders and checks, and asks
   before placing anything. Details and hard rules: `.claude/skills/robinhood-rebalance/SKILL.md`.

Claude discovers Robinhood's tool names and parameters from the server at run time; nothing is
hard-coded. To see them yourself: `python -m engine robinhood inspect` (read-only; this uses a
third-party OAuth client, which Robinhood may not allow, in which case use the Claude path).

Start with a small amount and paper-trade in parallel for a few months before scaling up.

## How it decides

```
prices -> trend (1-12 month momentum) -> DFA Hurst size multiplier -> fat-tail ES per asset
       -> risky sleeve (budget x strength / ES) -> fractional-Kelly cap -> portfolio ES cap
       -> drawdown brake -> T-bill sleeve gets the rest -> orders (sells first, no-trade band)
```

| Piece | What it does | Source |
|---|---|---|
| Barbell | 65-85% T-bills (SGOV), capped risky sleeve; worst case bounded by sleeve size | Taleb, *Antifragile* |
| Fat tails | Student-t / power-law risk, tail exponent from Hill, cut 15% for estimation error | Taleb (2012, 2020); Gabaix (2009) |
| Expected shortfall | Sizes positions and caps portfolio 1-day ES99 (worse of empirical and model) | Acerbi & Tasche (2002) |
| Fractional Kelly | Caps exposure at 0.25x the growth-optimal level on time-average log growth | Kelly (1956); Peters (2019) |
| Trend following | Long-only time-series momentum; historically convex in long crashes | Moskowitz, Ooi & Pedersen (2012) |
| DFA Hurst | Mild size multiplier; walk-forward decides whether to use it | Peng et al. (1994) |
| Fragility test | Curvature of monthly returns vs the market (convex = antifragile) | Taleb & Douady (2013) |
| Gauge attribution | Splits growth into exposure, timing (holonomy) and convexity; the last two are numeraire-invariant | Malaney & Weinstein, *The Economic Index Problem* |
| Walk-forward | Pick settings on 3 past years, trade the next year blind; only blind years reported | Bailey et al. (2014) |
| Bootstrap | Block-bootstrap probability the strategy genuinely beats each comparison | Politis & Romano (1994) |

The Weinstein piece is a measurement layer, not a signal: it tells you whether returns came from
holding assets or from the path-dependent act of trading them. Taleb's own edge (buying cheap
out-of-the-money options) needs historical option prices we do not have; `--hedge` adds a
*model-priced* put overlay for analysis only.

## Safety rails

- Cash-only, long-only, no margin, no options by default.
- A plan is **blocked** if prices are more than 5 days old, equity is not positive, a short is
  found, or buys exceed cash plus sells. Blocked plans exit with code 2 and Claude will not trade them.
- `state/` (holdings, plans, paper ledger, OAuth tokens) is git-ignored.
- The dashboard binds to localhost and has no login; do not expose it publicly.

## Configuration

`config/engine.yaml`: universe, safe asset, risk limits, costs, the walk-forward search grid.
Keep the grid small: every extra combination is another chance to fit noise.

## Limitations

- One historical path; a few out-of-sample years is weak evidence.
- Daily decisions from closing prices; fills in reality differ by the spread and timing.
- Yahoo data is unofficial and occasionally wrong; Alpaca is better if you have keys.
- The put hedge is priced with a model, not real option quotes.

## Research code

`research/` holds the earlier intraday microstructure experiment (order-flow imbalance, VPIN)
for Alpaca/IBKR. It is not validated and not connected to Robinhood.
