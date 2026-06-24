.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  make lint     Check style with ruff"
	@echo "  make format   Format code with ruff"
	@echo "  make fix      Auto-fix and format"
	@echo "  make check    Check without modifying (used by CI)"
	@echo "  make test     Run tests with pytest"
	@echo "  make icon     Regenerate assets/icon.png from claudebar/icon.py"
	@echo "  make clean    Remove __pycache__ and .pyc files"

lint:
	ruff check .

format:
	ruff format .

fix:
	ruff check . --fix
	ruff format .

check:
	ruff check .
	ruff format . --check

test:
	poetry run pytest

icon:
	poetry run python3 -c "from claudebar.icon import render_app_icon; render_app_icon().save('assets/icon.png')"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
