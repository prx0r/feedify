.PHONY: dev test seed ingest clean

dev:
	uvicorn feedify.api:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q

seed:
	python -m feedify.cli seed

ingest:
	python -m feedify.cli ingest

clean:
	rm -f feedify.db
