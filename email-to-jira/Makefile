PY := .venv/bin/python

.PHONY: setup dev test poll harness harness-live seed

setup:            ## create venv and install dependencies
	python3 -m venv .venv && $(PY) -m pip install -r requirements.txt

dev:              ## run the review dashboard at http://localhost:8000
	$(PY) -m uvicorn app.main:app --reload --port 8000

test:             ## run the test suite
	$(PY) -m pytest tests/ -q

poll:             ## one live Gmail poll cycle (needs OAuth creds in .env)
	$(PY) -m scripts.poller

harness:          ## feed fixture emails through the pipeline, offline (no keys)
	$(PY) -m scripts.harness

harness-live:     ## same, but with the real Anthropic API
	$(PY) -m scripts.harness --live

seed: harness     ## alias: seed the dashboard with sample data
