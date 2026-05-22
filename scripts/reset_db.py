#!/usr/bin/env python3
"""Reset database and all user data."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "email_index.db"


def reset_database():
    """Delete all tables and re-initialize."""
    if not DB_PATH.exists():
        print("Database not found. Nothing to reset.")
        return

    print(f"Resetting database at {DB_PATH}...")

    try:
        conn = sqlite3.connect(str(DB_PATH))

        # Drop all tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table_name in tables:
            print(f"  Dropping table: {table_name[0]}")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]};")

        conn.commit()
        conn.close()

        # Remove the database file
        DB_PATH.unlink()
        print(f"✓ Database reset successfully")
        print("")
        print("Next steps:")
        print("  1. Run: make init-db")
        print("  2. Run: make run")
        print("  3. Visit http://localhost:5000 and create a new admin account")

    except Exception as e:
        print(f"✗ Error resetting database: {e}")
        exit(1)


if __name__ == "__main__":
    reset_database()
