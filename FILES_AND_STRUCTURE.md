# Email Viewer — Files and Structure

## Complete File Listing

### Entry Point
```
run.py                          Flask app entry point
start_server.sh                 Bash script to start the app
```

### Configuration
```
requirements.txt                Python dependencies (11 packages)
.gitignore                      Git ignore rules
settings.json                   Auto-created: root path, password hash, secret key
```

### Backend — Core Modules (app/)
```
app/__init__.py                 Flask app factory (create_app)
app/config.py                   Settings management (load/save to settings.json)
app/auth.py                     Login/logout with Flask-Login and werkzeug password hashing
app/db.py                       SQLite connection pool, schema bootstrap, WAL mode setup
app/indexer.py                  Background threading indexer with progress tracking
app/msg_parser.py               ⭐ DUAL FORMAT MESSAGE PARSER (OLE2 binary + RFC 822 MIME)
app/sanitizer.py                HTML sanitization with bleach (whitelisting)
```

### Backend — API Routes (app/routes/)
```
app/routes/__init__.py          Empty init file
app/routes/main.py              GET /app, /config (template routes)
app/routes/api_config.py        GET/POST /api/config (settings CRUD)
app/routes/api_folders.py       GET /api/folders (nested tree with email counts)
app/routes/api_emails.py        GET /api/emails (paginated list + sort/filter)
                                GET /api/emails/<id> (full email detail)
app/routes/api_attachments.py   GET /api/attachments/<id>/<idx>/download|preview
app/routes/api_search.py        GET /api/search (FTS5 full-text search)
app/routes/api_index.py         POST /api/index/start, GET /api/index/status|progress|reset
```

### Frontend — HTML Templates (app/templates/)
```
app/templates/base.html         Base layout with Bootstrap 5.3 CDN
app/templates/login.html        Password login page (first run setup)
app/templates/config.html       Settings page (folder path, password, indexing)
app/templates/app.html          Main 3-pane shell (navbar, sidebar, grid layout)
```

### Frontend — CSS (app/static/css/)
```
app/static/css/app.css          3-pane grid layout, responsive design, email styles
```

### Frontend — JavaScript (app/static/js/)
```
app/static/js/app.js            Main entry point (initializes all components)
app/static/js/folder-tree.js    Folder tree component (recursive, collapsible)
app/static/js/email-list.js     Email list component (sort, filter, pagination)
app/static/js/reading-pane.js   Email reader (HTML iframe, attachment preview)
app/static/js/search.js         Search component (live dropdown, full results)
app/static/js/index-progress.js Indexing modal with SSE streaming
```

### Database (data/)
```
data/                           Database directory (auto-created)
data/email_index.db             SQLite database with FTS5
data/email_index.db-shm         WAL mode shared memory file
data/email_index.db-wal         WAL mode write-ahead log file
```

### Documentation
```
README.md                       Full documentation and user guide
QUICKSTART.md                   Quick start guide (5-minute setup)
IMPLEMENTATION.md               Technical implementation details
PROJECT_SUMMARY.txt             ASCII summary of the project
FILES_AND_STRUCTURE.md          This file
```

---

## File Count Summary

| Category | Count | Details |
|----------|-------|---------|
| Python backend | 15 | 1 factory + 1 config + 1 auth + 1 db + 1 indexer + 1 parser + 1 sanitizer + 6 routes + 2 util |
| HTML templates | 4 | base, login, config, app shell |
| CSS | 1 | app.css (3-pane layout) |
| JavaScript | 6 | 5 components + 1 main entry point |
| Configuration | 4 | requirements.txt, .gitignore, settings.json (auto), run.py |
| Documentation | 4 | README, QUICKSTART, IMPLEMENTATION, PROJECT_SUMMARY |
| **Total** | **~40** | **All production-ready** |

---

## Directory Tree

```
email-viewer/
│
├── run.py                           ← START HERE
├── start_server.sh                  ← Alternative startup script
├── requirements.txt
├── .gitignore
├── settings.json                    (auto-created on first run)
│
├── README.md                        ← Full documentation
├── QUICKSTART.md                    ← Quick start guide
├── IMPLEMENTATION.md                ← Technical details
├── PROJECT_SUMMARY.txt              ← ASCII summary
├── FILES_AND_STRUCTURE.md           ← This file
│
├── data/
│   └── email_index.db               (auto-created on first run)
│
└── app/
    ├── __init__.py                  (Flask factory)
    ├── config.py                    (Settings management)
    ├── auth.py                      (Login/session auth)
    ├── db.py                        (Database setup + schema)
    ├── indexer.py                   (Background indexing thread)
    ├── msg_parser.py                (⭐ DUAL FORMAT PARSER)
    ├── sanitizer.py                 (HTML sanitization)
    │
    ├── routes/
    │   ├── __init__.py
    │   ├── main.py                  (Template routes)
    │   ├── api_config.py            (/api/config)
    │   ├── api_folders.py           (/api/folders)
    │   ├── api_emails.py            (/api/emails + detail)
    │   ├── api_attachments.py       (/api/attachments)
    │   ├── api_search.py            (/api/search)
    │   └── api_index.py             (/api/index + SSE)
    │
    ├── templates/
    │   ├── base.html
    │   ├── login.html
    │   ├── config.html
    │   └── app.html                 (3-pane shell)
    │
    └── static/
        ├── css/
        │   └── app.css              (3-pane layout)
        └── js/
            ├── app.js               (Main entry)
            ├── folder-tree.js
            ├── email-list.js
            ├── reading-pane.js
            ├── search.js
            └── index-progress.js
```

---

## Key Implementation Files

### The Fix: msg_parser.py
This file handles the dual-format support that fixed the OLE2 error:

```python
# Core functions
parse_msg_metadata()      # Auto-detect and parse OLE2 or MIME
get_msg_body()           # Extract HTML + text from either format
get_attachment_bytes()   # Get attachment data from either format
list_attachments()       # List attachments from either format

# Helper functions
_is_ole2_msg()           # Check if file is binary OLE2
_parse_ole2_msg()        # Parse using extract-msg (Outlook)
_parse_mime_msg()        # Parse using email.parser (RFC 822)
_detect_mime()           # Guess MIME type from filename + magic bytes
```

### Database: db.py
Defines the complete SQLite schema:

```python
# Tables
emails               # Core email metadata (19 fields)
attachments         # Attachment list per email
emails_fts          # FTS5 virtual table for search
fts_body           # Email body text (synced with FTS)
index_state        # Indexing progress tracking

# Functions
get_db()           # Thread-safe connection getter
close_db()         # Clean connection close
init_db()          # Bootstrap schema on startup
```

### Indexing: indexer.py
Background thread that processes emails:

```python
IndexerThread               # Threading.Thread subclass
  .run()                   # Main indexing loop
  ._run()                  # Actual indexing logic
  _scan_files()            # Find all .msg files
  _extract_attachment_text() # PDF/docx/xlsx text for FTS
  _update_state()          # Update index_state table

# Module functions
start_indexing()           # Create + start thread
get_status()              # Read index_state
reset_index()             # Wipe index
```

---

## Data Flow

### Indexing Flow
```
run.py
  ↓
app/__init__.py (create_app)
  ↓
app/db.py (init_db) → Creates SQLite schema
  ↓
User: Click "Start Indexing" → /api/index/start
  ↓
app/routes/api_index.py → indexer.start_indexing()
  ↓
app/indexer.py (IndexerThread)
  ↓
  For each .msg file:
    1. app/msg_parser.py (parse_msg_metadata)
    2. Extract body (get_msg_body)
    3. Extract attachment text
    4. INSERT emails, attachments, emails_fts
    5. UPDATE index_state
  ↓
SQLite: emails + attachments + emails_fts tables populated
```

### Reading Flow
```
User: Click email in list
  ↓
app/static/js/email-list.js (emailSelected event)
  ↓
app/static/js/reading-pane.js (ReadingPane.load)
  ↓
GET /api/emails/<id>
  ↓
app/routes/api_emails.py → fetch from DB
  ↓
  1. Retrieve email metadata
  2. app/msg_parser.py (get_msg_body)
  3. app/sanitizer.py (sanitize_html)
  4. Fetch attachments from DB
  5. Return JSON
  ↓
JavaScript: Render in iframe (HTML), attachment cards
```

### Search Flow
```
User: Type in search bar → Enter
  ↓
app/static/js/search.js → /api/search?q=...
  ↓
app/routes/api_search.py
  ↓
  1. Parse user query (FTS5 safe)
  2. Query emails_fts MATCH query
  3. JOIN with emails table
  4. snippet() for highlights
  5. Return paginated results
  ↓
JavaScript: Render search results in email list
```

---

## Dependencies

### Python (requirements.txt)
```
flask==3.0.3                # Web framework
flask-login==0.6.3          # Session management
extract-msg==0.55.0         # OLE2 .msg parsing
bleach==6.1.0              # HTML sanitization
bleach[css]==6.1.0         # CSS sanitization
Pillow==10.3.0             # Image utilities
python-magic==0.4.27       # MIME type detection
pdfminer.six==20231228     # PDF text extraction
python-docx==1.1.0         # DOCX text extraction
openpyxl==3.1.2            # XLSX text extraction
werkzeug==3.0.3            # Password hashing (PBKDF2)
```

### Frontend
```
Bootstrap 5.3.3             CDN: https://cdn.jsdelivr.net/npm/bootstrap@5.3.3
Bootstrap Icons 1.11.3      CDN: https://cdn.jsdelivr.net/npm/bootstrap-icons
Vanilla JavaScript          ES6 modules (no jQuery, no build tools)
```

---

## Auto-Created Files (First Run)

When you start the app for the first time:

```
settings.json               Contains:
                           - root_path: (empty, you set it)
                           - password_hash: (PBKDF2 hashed)
                           - secret_key: (randomly generated)

data/email_index.db         SQLite database with full schema
data/email_index.db-shm     WAL mode shared memory
data/email_index.db-wal     WAL mode write-ahead log
```

Both files are in `.gitignore` to protect your data.

---

## File Sizes (Approximate)

| File | Size | Purpose |
|------|------|---------|
| msg_parser.py | ~12 KB | Core format handling (FIXED) |
| indexer.py | ~8 KB | Background indexing |
| api_emails.py | ~5 KB | Email list/detail routes |
| app.js | ~4 KB | Frontend main entry |
| email-list.js | ~6 KB | Email list component |
| reading-pane.js | ~8 KB | Email reader component |
| app.css | ~4 KB | 3-pane layout |
| **Total code** | **~100 KB** | All modules combined |

---

## Quick Reference

### Start the app
```bash
python run.py
```

### Access via browser
```
http://localhost:5000
```

### Add to folder (test)
```bash
cp /path/to/emails/*.msg /home/vikash/email-viewer/test/
```

### View database directly
```bash
sqlite3 data/email_index.db
sqlite> SELECT COUNT(*) FROM emails;
```

### Check logs
```bash
tail console output from run.py
```

### Reset everything
```bash
rm settings.json data/email_index.db*
python run.py
```

---

**Status**: ✅ Production-ready. All files created, tested, documented.
