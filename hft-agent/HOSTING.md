# HFT Agent — Hosting & Deployment Guide

## Recommended Hosting Options (Ranked by Latency)

### 1. Equinix NY5 / NJ2 (Colocation) — Best for True HFT
- **Latency**: <1ms to NYSE/NASDAQ
- **Cost**: $2,000-5,000/month for a cabinet
- **When to use**: If you need sub-millisecond execution and are trading
  at institutional scale with IBKR FIX protocol
- **Setup**: Bare metal server, dedicated network, FPGA optional

### 2. AWS us-east-1 (N. Virginia) — Best Balance of Cost & Performance
- **Latency**: 1-5ms to major exchanges
- **Cost**: ~$200-500/month
- **Recommended instance**: `c6i.xlarge` (4 vCPU, 8GB RAM) or `c7g.xlarge` (ARM, cheaper)
- **Why us-east-1**: Closest AWS region to NYSE (Mahwah, NJ) and NASDAQ
- **Setup**:
  ```bash
  # Use EC2 with docker-compose
  sudo yum install docker docker-compose-plugin -y
  sudo systemctl start docker
  git clone <your-repo>
  cd hft-agent
  cp .env.example .env  # Fill in credentials
  docker compose -f deploy/docker-compose.yml up -d
  ```

### 3. Google Cloud us-east4 (Ashburn, VA) — Alternative Cloud
- **Latency**: 1-5ms to exchanges
- **Cost**: Similar to AWS
- **Instance**: `c2-standard-4` (4 vCPU, 16GB)

### 4. Hetzner Ashburn DC — Budget Option
- **Latency**: 2-10ms
- **Cost**: ~$50-100/month for dedicated server
- **Good for**: Paper trading, backtesting, medium-frequency strategies

### 5. DigitalOcean NYC — Budget Cloud
- **Latency**: 5-15ms
- **Cost**: ~$50-100/month
- **Good for**: Development, paper trading

## Production Deployment Architecture

```
┌─────────────────────────────────────────────┐
│                AWS us-east-1                 │
│                                              │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │ HFT Agent│  │TimescaleDB│  │  Redis    │ │
│  │ (EC2)    │──│  (RDS)    │  │(Elasticache│ │
│  └────┬─────┘  └───────────┘  └──────────┘ │
│       │                                      │
│  ┌────┴─────┐  ┌───────────┐               │
│  │Prometheus │  │  Grafana  │               │
│  │(EC2/ECS) │──│ (EC2/ECS) │               │
│  └──────────┘  └───────────┘               │
└─────────────────────────────────────────────┘
        │
        │ WebSocket (Alpaca/Polygon data feed)
        │ REST API (Broker execution)
        ▼
┌───────────────┐
│ Exchange APIs  │
│ (NYSE/NASDAQ)  │
└───────────────┘
```

## Quick Start (Local Development)

```bash
# 1. Clone and configure
git clone <repo-url>
cd hft-agent
cp .env.example .env
# Edit .env with your API keys

# 2. Start infrastructure
docker compose -f deploy/docker-compose.yml up -d timescaledb redis

# 3. Install Python dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 4. Run in paper trading mode
python main.py --mode paper --broker alpaca

# 5. Run tests
pytest tests/ -v
```

## Quick Start (Docker — Full Stack)

```bash
cp .env.example .env
# Edit .env with credentials
docker compose -f deploy/docker-compose.yml up -d
```

## Database Choice Rationale

### TimescaleDB (Primary — Tick Data & Analytics)
- **Why not InfluxDB?** TimescaleDB offers full SQL, JOINs, and better
  compression. InfluxDB's query language (Flux) is limited for complex
  analytics. TimescaleDB's continuous aggregates auto-compute OHLCV bars.
- **Why not QuestDB?** QuestDB is faster for ingestion but lacks the
  mature ecosystem, compression policies, and continuous aggregates.
- **Why not plain PostgreSQL?** TimescaleDB adds 10-20x compression and
  automatic time-partitioning that makes range queries orders of magnitude faster.

### Redis (Cache Layer — Real-time State)
- Sub-millisecond reads for order book state
- Pub/sub for event-driven architecture
- Rate limiting for API calls
- No persistence needed (cache only)

## Monitoring

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091
- **Health Check**: http://localhost:8080/health

## Security Notes

- Never commit `.env` files
- Use AWS Secrets Manager or HashiCorp Vault for production credentials
- Enable VPC and security groups in cloud deployments
- Use read-only API keys where possible (data feeds)
- Enable 2FA on all broker accounts
