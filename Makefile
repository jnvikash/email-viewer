.PHONY: help setup install init-db reset-db reset-all config run clean venv

PYTHON := python3
VENV := venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
ACTIVATE := . $(VENV)/bin/activate

help:
	@echo "Email Viewer — Multi-User Setup"
	@echo ""
	@echo "Available targets:"
	@echo "  make setup       — Create venv and install dependencies (one-time)"
	@echo "  make install     — Install/update dependencies"
	@echo "  make init-db     — Initialize database with first admin user"
	@echo "  make reset-db    — Reset entire database (deletes all users/emails)"
	@echo "  make reset-all   — Full reset: venv, database, config"
	@echo "  make config      — Interactive configuration"
	@echo "  make run         — Run the application (http://localhost:5000)"
	@echo "  make validate    — Validate installation and configuration"
	@echo "  make clean       — Remove venv and temporary files"
	@echo ""

venv:
	@echo "Creating Python virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created at ./$(VENV)"

setup: venv install init-db
	@echo ""
	@echo "✓ Setup complete!"
	@echo "  Run: make run"

install: $(VENV)
	@echo "Installing dependencies..."
	$(PIP) install -q --upgrade pip setuptools wheel
	$(PIP) install -q -r requirements.txt
	@echo "✓ Dependencies installed"

init-db:
	@echo "Initializing database..."
	$(BIN)/python -c "from app.db import init_db; init_db(); print('✓ Database initialized')"
	@echo ""
	@echo "Database created at: data/email_index.db"
	@echo ""
	@echo "Next: Run 'make run' and visit http://localhost:5000 to create admin account"

reset-db:
	@echo ""
	@echo "⚠️  WARNING: This will DELETE all users, emails, and indexed data"
	@read -p "Type 'YES' to confirm: " confirm; \
	if [ "$$confirm" = "YES" ]; then \
		$(BIN)/python scripts/reset_db.py; \
		echo "✓ Database reset"; \
	else \
		echo "Cancelled"; \
	fi

reset-all: clean setup
	@echo "✓ Full reset complete (venv, database, config)"

config:
	$(BIN)/python scripts/setup_config.py

run:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Run: make setup"; \
		exit 1; \
	fi
	@if [ ! -f "settings.json" ]; then \
		echo "Configuration not found. Run: make config"; \
		exit 1; \
	fi
	@echo "Starting Email Viewer..."
	@echo "Open http://localhost:5000 in your browser"
	@echo "Press Ctrl+C to stop"
	@echo ""
	$(BIN)/python run.py

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV)
	rm -rf __pycache__ .pytest_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

validate:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Run: make setup"; \
		exit 1; \
	fi
	@echo "Validating installation..."
	$(BIN)/python scripts/validate.py

.PHONY: show-status
show-status:
	@echo "Email Viewer Status:"
	@if [ -d "$(VENV)" ]; then echo "✓ venv created"; else echo "✗ venv not found"; fi
	@if [ -f "settings.json" ]; then echo "✓ settings.json exists"; else echo "✗ settings.json not found"; fi
	@if [ -f "data/email_index.db" ]; then echo "✓ database exists"; else echo "✗ database not found"; fi
