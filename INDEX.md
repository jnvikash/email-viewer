# Email Viewer — Documentation Index

Welcome! Here's where to find what you need.

---

## 🚀 Getting Started

**Start here if you're new:**

1. **[QUICKSTART.md](QUICKSTART.md)** — 5-minute setup and common tasks
   - Quick installation with `make setup`
   - Creating admin accounts
   - Multi-user management basics
   - Troubleshooting quick fixes

2. **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** — Complete installation options
   - Installation with Make (recommended)
   - Manual installation steps
   - Docker installation
   - System-specific guides (Linux, Mac, Windows)
   - Troubleshooting all installation issues

---

## 📖 Complete Guides

**For comprehensive information:**

3. **[SETUP.md](SETUP.md)** — Comprehensive setup guide for multi-user
   - Detailed step-by-step setup
   - Database management
   - File structure explanation
   - Security notes
   - Post-installation configuration

4. **[DEVELOPMENT.md](DEVELOPMENT.md)** — For developers
   - Project architecture
   - How to add new features
   - Database schema changes
   - Development workflow
   - Performance considerations
   - Debugging tips
   - Security checklist

---

## 🛠️ Make Commands

Quick reference for all Make commands:

```bash
make help       # Show all available commands
make setup      # One-time: create venv + install + init database
make install    # Install/update dependencies
make init-db    # Initialize database
make reset-db   # Reset database (deletes all data)
make reset-all  # Full clean slate
make config     # Interactive configuration
make run        # Start the application
make validate   # Check installation
make clean      # Remove venv
```

See [Makefile](Makefile) for details.

---

## 📁 Key Files and Directories

```
email-viewer/
├── Makefile                    # Setup and management commands
├── QUICKSTART.md              # Quick start (read this first!)
├── INSTALLATION_GUIDE.md      # Installation options
├── SETUP.md                   # Comprehensive setup guide
├── DEVELOPMENT.md             # Developer guide
├── README.md                  # Project overview
├── requirements.txt           # Python dependencies
├── run.py                     # Application entry point
├── Dockerfile                 # Docker build config
├── docker-compose.yml         # Docker Compose config
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── scripts/                   # Utility scripts
│   ├── setup_config.py       # Interactive configuration
│   ├── reset_db.py           # Database reset utility
│   └── validate.py           # Installation validator
│
├── app/                       # Flask application
│   ├── __init__.py           # App factory
│   ├── config.py             # Configuration manager
│   ├── auth.py               # Multi-user authentication
│   ├── db.py                 # Database schema
│   ├── indexer.py            # Background indexing
│   ├── msg_parser.py         # .msg/.eml parsing
│   ├── sanitizer.py          # HTML sanitization
│   ├── routes/               # API and page routes
│   ├── templates/            # HTML templates
│   └── static/               # CSS and JavaScript
│
├── data/                      # Application data (gitignored)
│   └── email_index.db        # SQLite database
│
└── venv/                      # Virtual environment (gitignored)
```

---

## ❓ Common Questions

### "How do I install this?"
→ See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)

### "How do I get started?"
→ See [QUICKSTART.md](QUICKSTART.md)

### "How do I create users?"
→ Section "Multi-User Setup" in [QUICKSTART.md](QUICKSTART.md)

### "How do I index emails?"
→ Section "Step 4" in [QUICKSTART.md](QUICKSTART.md)

### "How do I troubleshoot problems?"
→ "Troubleshooting" section in [SETUP.md](SETUP.md) or [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)

### "How do I contribute code?"
→ See [DEVELOPMENT.md](DEVELOPMENT.md)

### "How do I deploy to production?"
→ See "Deployment" section in [DEVELOPMENT.md](DEVELOPMENT.md)

### "How do I use Docker?"
→ See "Option 3: Docker" in [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)

---

## 📚 Feature Overview

### User Management
- Multi-user support with per-user email folders
- Admin panel for creating/managing users
- Password management (PBKDF2-SHA256)
- Role-based access (admin vs regular users)

### Email Viewing
- 3-pane interface (Folder tree | Email list | Reading pane)
- Full-text search (FTS5 with porter stemmer)
- Sorting and filtering
- Attachment preview/download
- HTML email rendering with sanitization

### Technical Features
- Dual-format .msg parsing (OLE2 + RFC 822 MIME)
- Background email indexing (doesn't block UI)
- SQLite database with FTS5 search
- Per-user data isolation
- Automatic detection and handling of malformed files

---

## 🔒 Security

This application:
- ✓ Binds to localhost only (127.0.0.1:5000)
- ✓ Uses PBKDF2-SHA256 password hashing
- ✓ Parameterized SQL queries (no injection)
- ✓ HTML sanitization with bleach
- ✓ Session-based authentication
- ✓ Per-user data isolation

See security notes in [SETUP.md](SETUP.md) and [DEVELOPMENT.md](DEVELOPMENT.md)

---

## 🐛 Found an Issue?

1. Check the troubleshooting sections:
   - [QUICKSTART.md](QUICKSTART.md#troubleshooting)
   - [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md#installation-troubleshooting)
   - [SETUP.md](SETUP.md#troubleshooting)

2. Run the validator:
   ```bash
   make validate
   ```

3. Try a clean reinstall:
   ```bash
   make reset-all
   make setup
   make run
   ```

---

## 📝 Documentation Quick Links

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute quick start |
| [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) | Complete installation |
| [SETUP.md](SETUP.md) | Comprehensive guide |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Developer reference |
| [INDEX.md](INDEX.md) | This file - documentation index |

---

## 🎯 Next Steps

1. **First time?** Start with [QUICKSTART.md](QUICKSTART.md)
2. **Installing?** See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
3. **Need help?** Check [SETUP.md](SETUP.md#troubleshooting)
4. **Developing?** Read [DEVELOPMENT.md](DEVELOPMENT.md)

---

**Happy emailing! 📧**
