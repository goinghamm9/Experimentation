# Hosting

The engine makes one decision per trading day, so it needs no special infrastructure.

## Your own computer (recommended to start)

Run `python -m engine serve` when you want the dashboard, and `python -m engine paper step`
after each market close. Execution on Robinhood happens in Claude Code on your desktop anyway.

## Always-on paper trading on a small server

Any $5-10/month VPS (Hetzner, DigitalOcean, Lightsail) is plenty.

```bash
git clone <your-repo> && cd hft-agent
python3 -m venv .venv && . .venv/bin/activate && pip install -e .
python -m engine backtest
python -m engine paper init --capital 10000
crontab -e
# 30 22 * * 1-5  cd /path/to/hft-agent && .venv/bin/python -m engine paper step >> state/paper.log 2>&1
```

(22:30 UTC is after the US close year-round.) To view the dashboard from your laptop without
exposing it: `ssh -L 8000:127.0.0.1:8000 you@server` and open http://127.0.0.1:8000.

## Docker

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

The container serves the dashboard on 127.0.0.1:8000 and keeps `state/` on the host.
