# Email Viewer — Development Guide

Guide for developers working on the Email Viewer codebase.

## Development Setup

### 1. Clone and Setup

```bash
git clone <repository>
cd email-viewer
make setup
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Run in Development Mode

```bash
export FLASK_DEBUG=1  # On Windows: set FLASK_DEBUG=1
make run
```

The app will auto-reload on code changes.

---

## Project Architecture

### Backend Structure

```
app/
├── __init__.py          # Flask app factory + blueprint registration
├── config.py            # Configuration management (settings.json)
├── auth.py              # User authentication (Flask-Login + werkzeug hashing)
├── db.py                # SQLite schema + thread-safe connection pooling
├── indexer.py           # Background email indexing (threading.Thread)
├── msg_parser.py        # .msg/.eml parsing + dual-format support
├── sanitizer.py         # HTML sanitization with bleach
├── routes/
│   ├── __init__.py
│   ├── main.py          # Page routes (/app, /config)
│   ├── admin.py         # Admin panel (/admin/*)
│   ├── api_config.py    # GET/POST /api/config
│   ├── api_folders.py   # GET /api/folders (tree building, caching)
│   ├── api_emails.py    # GET /api/emails, /api/emails/<id>
│   ├── api_attachments.py  # Download/preview attachments
│   ├── api_search.py    # FTS5 search with fallback
│   └── api_index.py     # Background indexing control (SSE progress)
├── templates/
│   ├── base.html        # Bootstrap layout
│   ├── login.html       # Multi-user login form
│   ├── register.html    # First-run admin creation
│   ├── config.html      # Settings page
│   ├── app.html         # 3-pane email viewer
│   └── admin/
│       ├── dashboard.html    # Admin overview
│       └── manage_users.html # User CRUD + index status
└── static/
    ├── css/
    │   └── app.css      # 3-pane layout (CSS grid)
    └── js/
        ├── app.js
        ├── folder-tree.js
        ├── email-list.js
        ├── reading-pane.js
        ├── search.js
        └── index-progress.js
```

### Key Design Decisions

#### Multi-User Isolation
- **Database**: `users` table + foreign keys on `emails` table
- **Queries**: All API routes filter by `current_user.id`
- **Indexing**: Per-user threads with per-user `index_state` rows
- **Folders**: Per-user folder trees with caching by `user_id`

#### Dual-Format .msg Parsing
- **Detection**: Magic byte check (`\xd0\xcf\x11\xe0` for OLE2)
- **OLE2 path**: `extract-msg` library → `parse_msg_metadata()`
- **MIME path**: Python `email.parser` → fallback parsing
- **Error handling**: Per-file try/except, never abort thread

#### Full-Text Search
- **Backend**: SQLite FTS5 virtual table with porter stemmer
- **Indexing**: Subject, sender, sender_email, body, attachment text
- **Query handling**:
  - Safe FTS syntax wrapping in quotes
  - Fallback to LIKE if FTS fails (syntax errors)
  - Per-user filtering with `WHERE user_id = ?`

#### Background Indexing
- **Threading**: One thread per user, stored in `_threads: dict[int, Thread]`
- **Locking**: `threading.Lock` on thread dict access
- **Batching**: 50 files per transaction (BEGIN IMMEDIATE)
- **State tracking**: Per-user `index_state` row with live updates
- **Attachment extraction**: PDFs (pdfminer), DOCX (python-docx), XLSX (openpyxl)

---

## Development Workflow

### Adding a New API Route

1. Create handler in `app/routes/api_example.py`:

```python
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from ..db import get_db

bp = Blueprint("api_example", __name__, url_prefix="/api/example")

@bp.route("/data", methods=["GET"])
@login_required
def get_data():
    db = get_db()
    # Filter by user_id for multi-user isolation
    rows = db.execute(
        "SELECT * FROM some_table WHERE user_id=?",
        (current_user.id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])
```

2. Register in `app/__init__.py`:

```python
from .routes import api_example
app.register_blueprint(api_example.bp)
```

### Adding a New Admin Feature

1. Add route to `app/routes/admin.py`
2. Use `@admin_required` decorator
3. Create template in `app/templates/admin/`
4. Add navigation link in admin templates

### Database Schema Changes

1. Modify `SCHEMA` in `app/db.py`
2. Drop and recreate database: `make reset-db && make init-db`
3. Or implement migrations (not currently in place)

### Frontend Changes

1. Edit `app/templates/` for HTML
2. Edit `app/static/css/app.css` for styling
3. Edit `app/static/js/` for interactivity
4. Test in browser with `make run`

---

## Testing

### Manual Testing Checklist

- [ ] Create admin account on first run
- [ ] Create additional users (admin panel)
- [ ] Set email folder for each user
- [ ] Index emails (background progress)
- [ ] Browse folder tree (different users see different folders)
- [ ] Search emails (results filtered by user)
- [ ] View email details + attachments
- [ ] Deactivate/reactivate user (admin)
- [ ] Change user password (admin)
- [ ] Reset index (user settings)

### Automated Tests

Currently no automated test suite. To add pytest:

```bash
pip install pytest pytest-flask
# Add tests/ directory with test_*.py files
```

---

## Performance Considerations

### Indexing Speed
- **Bottleneck**: File I/O + text extraction
- **Optimization**: Batch transactions (50 files)
- **Large archives**: 5,000 files ≈ 5-10 minutes

### Search Performance
- **FTS5**: ~50ms for typical queries on 5,000 emails
- **Caching**: Folder tree cached 60s per user
- **Optimization**: Proper indexes on `user_id`, `date_sent`, `sender_email`

### Memory
- **Per-user indexer thread**: ~50MB
- **FTS index**: ~200MB for 5,000 emails (depends on attachment text)
- **Session cache**: Minimal (folder trees only)

---

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Database State

```bash
sqlite3 data/email_index.db
> SELECT * FROM users;
> SELECT COUNT(*) FROM emails;
> SELECT * FROM index_state;
```

### Check Indexing Status

Visit http://localhost:5000/config and check progress bar, or query:

```sql
SELECT user_id, status, done_files, total_files FROM index_state;
```

### Inspect Session/Auth

```python
from flask import session
print(session)  # In route handler
```

---

## Dependencies

Key packages (see `requirements.txt`):

- **Flask 3.0.3** — Web framework
- **extract-msg 0.55.0** — OLE2 .msg parsing
- **email** (stdlib) — MIME parsing
- **sqlite3** (stdlib) — Database
- **bleach 6.1.0** — HTML sanitization
- **pdfminer.six** — PDF text extraction
- **python-docx** — DOCX text extraction
- **openpyxl** — XLSX text extraction
- **werkzeug 3.0.3** — Password hashing
- **flask-login 0.6.3** — Session management

---

## Security Review Checklist

- [ ] No SQL injection (all queries parameterized)
- [ ] No path traversal (file_path from DB, not client)
- [ ] Passwords hashed (PBKDF2-SHA256 via werkzeug)
- [ ] CSRF protected (Flask-Login default)
- [ ] XSS mitigated (bleach sanitizer + template escaping)
- [ ] Session cookies secure (SameSite=Lax, HttpOnly)
- [ ] Admin routes guarded (@admin_required decorator)
- [ ] User data isolated (WHERE user_id = current_user.id)

---

## Deployment

See `docker-compose.yml` and `Dockerfile` for containerized deployment.

For production:
- Set `FLASK_DEBUG=0`
- Use production WSGI server (Gunicorn, uWSGI)
- Configure reverse proxy (nginx)
- Use SSL/TLS termination
- Restrict to internal network (firewall rules)

---

## Contributing

1. Fork and create a feature branch
2. Make changes following code style
3. Test manually with checklist above
4. Submit pull request with description

---

## Questions?

Check existing route handlers and templates for examples of common patterns.
