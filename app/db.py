import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "email_index.db"
_local = threading.local()

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;

-- Users table (multi-user support)
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    email_folder    TEXT,
    is_admin        INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Sessions table (track active sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token           TEXT NOT NULL UNIQUE,
    ip_address      TEXT,
    user_agent      TEXT,
    created_at      TEXT NOT NULL,
    last_activity   TEXT NOT NULL,
    expires_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);

-- Original emails table (per-user emails)
CREATE TABLE IF NOT EXISTS emails (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_path        TEXT NOT NULL,
    folder_path      TEXT NOT NULL,
    subject          TEXT,
    sender_name      TEXT,
    sender_email     TEXT,
    recipients       TEXT,
    date_sent        TEXT,
    date_indexed     TEXT NOT NULL,
    has_html_body    INTEGER NOT NULL DEFAULT 0,
    body_preview     TEXT,
    attachment_count INTEGER NOT NULL DEFAULT 0,
    size_bytes       INTEGER,
    importance       TEXT DEFAULT 'normal',
    UNIQUE(user_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_emails_user ON emails(user_id);
CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder_path);
CREATE INDEX IF NOT EXISTS idx_emails_date   ON emails(date_sent);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email);

CREATE TABLE IF NOT EXISTS attachments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id     INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
    filename     TEXT NOT NULL,
    mime_type    TEXT,
    size_bytes   INTEGER,
    attach_index INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_attach_email ON attachments(email_id);

CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
    subject,
    sender_name,
    sender_email,
    body_text,
    attachment_text,
    content='emails',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TABLE IF NOT EXISTS fts_body (
    email_id  INTEGER PRIMARY KEY REFERENCES emails(id) ON DELETE CASCADE,
    body_text TEXT,
    attachment_text TEXT
);

-- Per-user indexing state
CREATE TABLE IF NOT EXISTS index_state (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status      TEXT NOT NULL DEFAULT 'idle',
    total_files INTEGER NOT NULL DEFAULT 0,
    done_files  INTEGER NOT NULL DEFAULT 0,
    skipped     INTEGER NOT NULL DEFAULT 0,
    started_at  TEXT,
    finished_at TEXT,
    updated_at  TEXT,
    error_msg   TEXT,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_index_state_user ON index_state(user_id);
"""


def get_db() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA busy_timeout=5000")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def close_db() -> None:
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None


def _migrate(conn: sqlite3.Connection) -> None:
    """Apply schema migrations for older databases."""

    def has_column(table: str, col: str) -> bool:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r[1] == col for r in rows)

    # Migration: add user_id to emails (old single-user schema)
    if not has_column("emails", "user_id"):
        conn.execute("ALTER TABLE emails ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_user ON emails(user_id)")

    # Migration: add folder_path to emails if missing
    if not has_column("emails", "folder_path"):
        conn.execute("ALTER TABLE emails ADD COLUMN folder_path TEXT NOT NULL DEFAULT ''")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder_path)")

    # Migration: rebuild index_state to add user_id (old schema had id=1 singleton)
    if not has_column("index_state", "user_id"):
        conn.execute("DROP TABLE IF EXISTS index_state")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS index_state (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status      TEXT NOT NULL DEFAULT 'idle',
                total_files INTEGER NOT NULL DEFAULT 0,
                done_files  INTEGER NOT NULL DEFAULT 0,
                skipped     INTEGER NOT NULL DEFAULT 0,
                started_at  TEXT,
                finished_at TEXT,
                updated_at  TEXT,
                error_msg   TEXT,
                UNIQUE(user_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_index_state_user ON index_state(user_id)")

    # Migration: add updated_at to index_state if missing
    if not has_column("index_state", "updated_at"):
        conn.execute("ALTER TABLE index_state ADD COLUMN updated_at TEXT")

    # Migration: fix emails UNIQUE constraint from UNIQUE(file_path) → UNIQUE(user_id, file_path)
    # The old single-user schema had `file_path TEXT NOT NULL UNIQUE`, which blocks multi-user
    # indexing because INSERT OR IGNORE silently skips rows whose file_path already exists
    # regardless of user_id.  Detect this by looking for a unique index covering only file_path.
    def _emails_has_single_file_path_unique() -> bool:
        for idx in conn.execute("PRAGMA index_list(emails)").fetchall():
            if idx[2] == 1:  # unique index
                cols = [c[2] for c in conn.execute(f"PRAGMA index_info({idx[1]})").fetchall()]
                if cols == ["file_path"]:
                    return True
        return False

    if _emails_has_single_file_path_unique():
        # Orphaned emails (user_id IS NULL) cannot be attributed to any user; drop them.
        # attachments and fts_body cascade automatically via FK ON DELETE CASCADE.
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("DELETE FROM emails WHERE user_id IS NULL")

        # Rebuild emails with the correct composite unique constraint.
        conn.execute("""
            CREATE TABLE emails_new (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                file_path        TEXT NOT NULL,
                folder_path      TEXT NOT NULL DEFAULT '',
                subject          TEXT,
                sender_name      TEXT,
                sender_email     TEXT,
                recipients       TEXT,
                date_sent        TEXT,
                date_indexed     TEXT NOT NULL DEFAULT '',
                has_html_body    INTEGER NOT NULL DEFAULT 0,
                body_preview     TEXT,
                attachment_count INTEGER NOT NULL DEFAULT 0,
                size_bytes       INTEGER,
                importance       TEXT DEFAULT 'normal',
                UNIQUE(user_id, file_path)
            )
        """)
        # Copy any remaining rows that already have a valid user_id
        conn.execute("""
            INSERT INTO emails_new
                (id, user_id, file_path, folder_path, subject, sender_name, sender_email,
                 recipients, date_sent, date_indexed, has_html_body, body_preview,
                 attachment_count, size_bytes, importance)
            SELECT id, user_id, file_path, folder_path, subject, sender_name, sender_email,
                   recipients, date_sent, date_indexed, has_html_body, body_preview,
                   attachment_count, size_bytes, importance
            FROM emails
            WHERE user_id IS NOT NULL
        """)
        conn.execute("DROP TABLE emails")
        conn.execute("ALTER TABLE emails_new RENAME TO emails")

        # Recreate indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_user   ON emails(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder_path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_date   ON emails(date_sent)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email)")

        # Clear the FTS index — use the FTS5 management command so it doesn't
        # try to read body_text/attachment_text columns from the content table.
        conn.execute("INSERT INTO emails_fts(emails_fts) VALUES('delete-all')")
        conn.execute("DELETE FROM fts_body")

    conn.commit()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    # Create schema first (with CREATE TABLE IF NOT EXISTS), then migrate
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    conn.close()
