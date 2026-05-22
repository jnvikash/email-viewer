#!/usr/bin/env python3
"""Validate Email Viewer installation and configuration."""

import sys
import sqlite3
from pathlib import Path
from importlib import util

REPO_ROOT = Path(__file__).parent
VENV_PATH = REPO_ROOT / "venv"
DB_PATH = REPO_ROOT / "data" / "email_index.db"
SETTINGS_PATH = REPO_ROOT / "settings.json"


def check_python_version():
    """Check Python version >= 3.10."""
    if sys.version_info < (3, 10):
        print(f"✗ Python 3.10+ required (found {sys.version_info.major}.{sys.version_info.minor})")
        return False
    print(f"✓ Python version {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_venv():
    """Check virtual environment exists."""
    if not VENV_PATH.exists():
        print(f"✗ Virtual environment not found: {VENV_PATH}")
        print("  Run: make setup")
        return False
    print(f"✓ Virtual environment exists")
    return True


def check_dependencies():
    """Check required packages are installed."""
    required = [
        "flask", "flask_login", "extract_msg", "bleach", "pdfminer",
        "docx", "openpyxl", "werkzeug"
    ]
    missing = []
    for package in required:
        if util.find_spec(package) is None:
            missing.append(package)

    if missing:
        print(f"✗ Missing packages: {', '.join(missing)}")
        print("  Run: make install")
        return False
    print(f"✓ All required packages installed")
    return True


def check_database():
    """Check database is initialized."""
    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        print("  Run: make init-db")
        return False

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

        if not tables:
            print(f"✗ Database exists but is empty")
            return False

        table_names = [t[0] for t in tables]
        required_tables = {"users", "emails", "index_state"}
        if not required_tables.issubset(set(table_names)):
            print(f"✗ Database missing required tables")
            return False

        print(f"✓ Database initialized with {len(table_names)} tables")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def check_configuration():
    """Check settings.json exists."""
    if not SETTINGS_PATH.exists():
        print(f"⚠ Configuration not found: {SETTINGS_PATH}")
        print("  Run: make config (optional)")
        return True

    try:
        import json
        with open(SETTINGS_PATH) as f:
            config = json.load(f)
        if "secret_key" not in config:
            print(f"✗ Invalid configuration (missing secret_key)")
            return False
        print(f"✓ Configuration file exists")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def check_app():
    """Check app can be imported."""
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from app import create_app
        app = create_app()
        print(f"✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        return False


def main():
    print("\nEmail Viewer — Installation Validation")
    print("=" * 50)

    checks = [
        ("Python version", check_python_version),
        ("Virtual environment", check_venv),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("Configuration", check_configuration),
        ("App import", check_app),
    ]

    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        try:
            results.append(check_func())
        except Exception as e:
            print(f"✗ {name} check failed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")

    if all(results):
        print("\n✓ Setup is complete! Run: make run")
        return 0
    else:
        print("\n✗ Setup incomplete. Address errors above and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
