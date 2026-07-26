.PHONY: install test run verify clean

install:
	pip install -r requirements.txt

test:
	python -m pytest -q

run:
	python -m ethnography run config/study.example.yaml -o report.md
	@echo "Wrote report.md"

verify:
	python -m ethnography verify config/study.example.yaml

clean:
	rm -f report.md
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
