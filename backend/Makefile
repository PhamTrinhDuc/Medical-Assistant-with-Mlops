.PHONY: test test-fast test-coverage test-watch test-markers help

help:
	@echo "Available commands:"
	@echo "  make test              - Run all tests"
	@echo "  make test-fast         - Run only quick tests"
	@echo "  make test-coverage     - Run tests with coverage report"
	@echo "  make test-watch        - Run tests in watch mode"
	@echo "  make test-auth         - Run only auth tests"
	@echo "  make test-conv         - Run only conversation tests"
	@echo "  make test-msg          - Run only message tests"
	@echo "  make test-integration  - Run only integration tests"
	@echo ""

test:
	pytest -v

test-fast:
	pytest -x -v tests/test_health.py tests/test_auth.py

test-coverage:
	pytest --cov=backend --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report: htmlcov/index.html"

test-watch:
	pip install -q pytest-watch
	ptw tests/

test-auth:
	pytest -m auth -v

test-conv:
	pytest -m conversation -v

test-msg:
	pytest -m message -v

test-integration:
	pytest -m integration -v

test-markers:
	pytest --markers
