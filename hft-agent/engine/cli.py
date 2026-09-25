"""Command line: backtest, plan, paper, serve, robinhood inspect."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .config import STATE_DIR, load_config


def main(argv: list[str] | None = None) -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    p = argparse.ArgumentParser(prog="hft-agent", description="Barbell engine: backtest, plan, paper-trade, serve.")
    p.add_argument("--config", help="Path to engine.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backtest", help="Walk-forward backtest on real historical data")
    b.add_argument("--start", default="2007-06-01")
    b.add_argument("--end", default=None)
    b.add_argument("--capital", type=float, default=100_000)
    b.add_argument("--train-years", type=int, default=3)
    b.add_argument("--csv", help="Offline CSV of prices instead of downloading")
    b.add_argument("--symbols", help="Comma-separated universe override")
    b.add_argument("--hedge", action="store_true", help="Include the model-priced put overlay")

    pl = sub.add_parser("plan", help="Today's orders for given holdings (never trades)")
    pl.add_argument("--holdings", help='JSON file: {"cash": 1000, "positions": {"SPY": 1.5}}')
    pl.add_argument("--json", action="store_true", help="Print the full plan as JSON")

    pa = sub.add_parser("paper", help="Paper-trading account")
    pa_sub = pa.add_subparsers(dest="paper_cmd", required=True)
    pi = pa_sub.add_parser("init")
    pi.add_argument("--capital", type=float, default=10_000)
    pa_sub.add_parser("step", help="Fetch latest prices, trade the plan once per day, mark to market")
    pa_sub.add_parser("status")

    s = sub.add_parser("serve", help="Dashboard at http://localhost:8000")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--host", default="127.0.0.1")

    rh = sub.add_parser("robinhood", help="Robinhood Agentic Trading MCP (read-only)")
    rh_sub = rh.add_subparsers(dest="rh_cmd", required=True)
    ri = rh_sub.add_parser("inspect", help="Sign in with OAuth and list the real MCP tools")
    ri.add_argument("--url", default=None)

    args = p.parse_args(argv)
    cfg = load_config(args.config)

    if args.cmd == "backtest":
        _backtest(cfg, args)
    elif args.cmd == "plan":
        _plan(cfg, args)
    elif args.cmd == "paper":
        _paper(cfg, args)
    elif args.cmd == "serve":
        import uvicorn

        print(f"Dashboard: http://{args.host}:{args.port}")
        uvicorn.run("dashboard.app:app", host=args.host, port=args.port)
    elif args.cmd == "robinhood":
        from brokers.robinhood_mcp import DEFAULT_URL, TOOLS_FILE, inspect_tools

        tools = asyncio.run(inspect_tools(args.url or DEFAULT_URL))
        for t in tools:
            print(f"- {t['name']}: {(t['description'] or '').splitlines()[0] if t['description'] else ''}")
        print(f"\n{len(tools)} tools. Full schemas saved to {TOOLS_FILE}")


def _backtest(cfg, args) -> None:
    from .data import load_prices
    from .walkforward import walk_forward

    if args.symbols:
        cfg.universe = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    if args.hedge:
        cfg.hedge.enabled = True
    symbols = [*cfg.universe, cfg.safe_asset, *cfg.safe_asset_fallbacks, cfg.benchmark]
    source = "csv" if args.csv else cfg.data_source
    print(f"Loading prices for {len(set(symbols))} symbols from {args.start}...")
    md = load_prices(symbols, args.start, args.end, source=source, csv_path=args.csv or cfg.csv_path)
    print(f"Loaded {md.close.shape[0]} days x {md.close.shape[1]} symbols from {md.source}. Running walk-forward...")
    res = walk_forward(md, cfg, train_years=args.train_years, capital=args.capital,
                       progress=lambda i, n: print(f"  backtest {i}/{n}", end="\r", flush=True))
    print()
    print_report(res)


def print_report(res: dict) -> None:
    print(f"\nOut-of-sample period {res['period'][0]} -> {res['period'][1]} ({res['n_param_sets_tried']} parameter sets tried)\n")
    hdr = f"{'':42s} {'CAGR':>7s} {'LogG':>7s} {'MADr':>6s} {'MaxDD':>7s} {'ES99/d':>7s}"
    print(hdr)
    for name, m in res["metrics"].items():
        if not m:
            continue
        print(f"{name[:42]:42s} {m['cagr']:+7.2%} {m['log_growth']:+7.3f} {m['mad_ratio']:6.2f} {m['max_drawdown']:7.1%} {m['es99_daily']:7.2%}")
    print("\nProbability strategy out-grows each comparison (block bootstrap):")
    for k, v in res["bootstrap"].items():
        print(f"  {k:45s} {v:.0%}")
    c = res["convexity"]
    if "convexity_t" in c:
        print(f"\nFragility test: {c['state']} (convexity t={c['convexity_t']:.2f}, beta={c['beta']:.2f})")
    g = res["gauge"]["usd"]
    print(f"Gauge attribution (log growth): exposure {g['exposure']:+.3f}, timing/holonomy {g['timing_holonomy']:+.3f}, "
          f"convexity {g['convexity']:+.3f}, total {g['total_log_growth']:+.3f}")
    print("\nChosen each year:")
    for f in res["folds"]:
        print(f"  {f['test_year']}: {f['chosen']:52s} blind-year log growth {f['test_log_growth']:+.3f}")
    for w in res["warnings"]:
        print(f"! {w}")
    print(f"\nLive parameters saved to {STATE_DIR / 'model.json'}. Dashboard: python -m engine serve")


def _plan(cfg, args) -> None:
    from .plan import make_plan

    holdings, cash = {}, 0.0
    if args.holdings:
        data = json.loads(Path(args.holdings).read_text())
        holdings = data.get("positions", {})
        cash = float(data.get("cash", 0.0))
    plan = make_plan(cfg, holdings, cash)
    if args.json:
        print(json.dumps(plan, indent=2, default=float))
        return
    print(plan["summary"])
    print(f"\nEquity ${plan['equity']:,.2f} | data through {plan['data_last_date']} ({plan['data_source']}) | params: {plan['params_source']}")
    for o in plan["orders"]:
        print(f"  {o['side'].upper():4s} {o['symbol']:6s} ${o['notional_usd']:>10,.2f}  (~{o['est_shares']:.4f} sh @ {o['ref_price']})")
        print(f"       {o['reason']}")
    print("\nChecks:")
    for c in plan["checks"]:
        print(f"  [{'ok' if c['ok'] else 'BLOCKED'}] {c['message']}")
    if plan["blocked"]:
        print("\nPLAN BLOCKED: do not execute.")
        sys.exit(2)


def _paper(cfg, args) -> None:
    from . import paper

    if args.paper_cmd == "init":
        paper.init(args.capital)
        print(f"Paper account created with ${args.capital:,.2f}. Run: python -m engine paper step")
    elif args.paper_cmd == "step":
        out = paper.step(cfg)
        print(out["plan"]["summary"])
        print(f"Equity ${out['equity']:,.2f} ({'traded' if out['traded'] else 'no trades today'})")
    else:
        ledger = paper.load()
        if not ledger:
            print("No paper account. Run: python -m engine paper init --capital 10000")
            return
        last = ledger["history"][-1] if ledger["history"] else {"date": "-", "equity": ledger["cash"]}
        print(f"Equity ${last['equity']:,.2f} on {last['date']} (started ${ledger['starting_capital']:,.2f})")
        print(f"Cash ${ledger['cash']:,.2f}; holdings: {json.dumps({k: round(v, 4) for k, v in ledger['holdings'].items()})}")


if __name__ == "__main__":
    main()
