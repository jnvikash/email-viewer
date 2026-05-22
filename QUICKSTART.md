# Email Viewer — Quick Start Guide

Get Email Viewer up and running in minutes.

## 30-Second Setup

```bash
cd email-viewer
make setup    # Creates venv, installs deps, initializes database
make run      # Starts the app
```

Open **http://localhost:5000** and create your admin account.

---

## 5-Minute Full Setup

### Step 1: Setup (2 min)
```bash
cd email-viewer
make setup
```

### Step 2: Run (1 min)
```bash
make run
```

### Step 3: Create Admin Account (1 min)
- Visit http://localhost:5000
- Click "Create an admin account"
- Enter username, password, optional email folder path
- Click "Create Admin Account"

### Step 4: Index Emails (optional, 1+ min)
- Go to Settings (⚙️)
- Start Indexing
- Wait for completion
- Browse your emails!

---

## Common Commands

| Command | What it does |
|---------|-------------|
| `make help` | Show all available commands |
| `make setup` | One-time: create venv + install + init database |
| `make install` | Update dependencies |
| `make run` | Start the application |
| `make config` | Interactive configuration wizard |
| `make validate` | Check installation is correct |
| `make reset-db` | Delete all users and emails (dangerous!) |
| `make reset-all` | Full clean slate (venv + database) |
| `make clean` | Remove virtual environment |

---

## First-Time Checklist

- [ ] Run `make setup`
- [ ] Run `make run`
- [ ] Create admin account at http://localhost:5000
- [ ] Go to Settings, set email folder path
- [ ] Click "Start Indexing"
- [ ] Wait for indexing complete
- [ ] Browse emails in 3-pane interface
- [ ] Try searching emails
- [ ] (Admin) Create more users in Admin panel

---

## Multi-User Setup

### As Admin: Create a New User

1. Log in with admin account
2. Click **Admin** in top right
3. Click **Manage Users**
4. Click **"Create New User"**
5. Fill in username, password, email folder
6. (Optional) Check "Admin user" to make them an admin
7. Click **"Create User"**

The new user can now log in.

### Per-User Email Folders

Each user can have their own email folder path:

**Admin sets it:**
- Admin → Manage Users → Edit user → Set "Email Folder Path"

**User views it:**
- Settings (⚙️) → Shows their assigned folder

---

## Troubleshooting

### "make: command not found"
You don't have `make` installed. Use Python directly:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from app.db import init_db; init_db()"
python run.py
```

### "Virtual environment not found"
```bash
make setup
```

### "Database not found"
```bash
make init-db
```

### "Settings not found"
```bash
make config
# Or just run the app, it will create a default settings.json
```

### "Port 5000 already in use"
Either:
- Stop the other app using port 5000
- Or modify `run.py` to use a different port

### Still stuck?
Check `SETUP.md` for detailed troubleshooting.

---

## What's Next?

- **Browse emails** — Click folders on the left
- **Search** — Type in the search bar at top
- **Download attachments** — Click email, scroll to attachments
- **Create users** — Admin → Manage Users (admin only)
- **Change settings** — Settings (⚙️) icon

---

## Architecture at a Glance

```
┌─────────────────────────────┐
│   Web Browser (localhost:5000)
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   Flask Web App (run.py)     │
│  ├─ Multi-user auth         │
│  ├─ Admin panel             │
│  └─ REST API endpoints      │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   SQLite Database (data/)    │
│  ├─ Users + passwords       │
│  ├─ Emails metadata         │
│  ├─ Full-text search index  │
│  └─ Indexing status         │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   .msg Files on Disk        │
│  /path/to/email/folder      │
└─────────────────────────────┘
```

---

## Performance Expectations

- **Setup**: ~1-2 minutes (venv creation + pip install)
- **First indexing**: ~1 minute per 1,000 emails (depends on CPU/disk)
- **Search**: ~50-100ms for typical queries
- **Browsing**: Instant folder navigation

---

## Key Features

✓ Multi-user (create unlimited users via admin panel)  
✓ Per-user email folders  
✓ Background indexing (doesn't block the UI)  
✓ Full-text search (fast FTS5 implementation)  
✓ 3-pane email interface (like traditional mail clients)  
✓ Attachment preview/download  
✓ Role-based access (admin vs regular users)  
✓ Password-protected  
✓ Local only (runs on your machine, no cloud)  

---

Enjoy browsing your emails! 📧
  ```
- Click **Save Path**

## 5. Start Indexing

- Click **Start Indexing** button
- Watch the progress bar until it completes
- You'll see: "Indexing complete! X emails indexed"

## 6. Browse Your Emails

Once indexing is done:
- **Left pane**: Folder tree shows all folders with email counts
- **Middle pane**: Click a folder to see emails, sort/filter as needed
- **Right pane**: Click an email to read full content with attachments
- **Search**: Use the search bar at top to find emails across all folders

---

## Supported Email Formats

✅ **OLE2 Binary (.msg)** - Microsoft Outlook format  
✅ **RFC 822 MIME (.msg, .eml, .txt)** - Server/MDaemon format  
✅ **Multipart MIME** - Text + HTML + attachments  

The app auto-detects format and handles both seamlessly.

---

## Features You Can Use

| Feature | How |
|---------|-----|
| **Search** | Type in search bar at top; press Enter for full results |
| **Sort** | Click "Sort" dropdown in email list toolbar |
| **Filter** | Click "Filter" (funnel icon), set date range, click "Apply" |
| **Preview Attachment** | Click email, scroll to attachments, click preview icon |
| **Download Attachment** | Click download icon on attachment card |
| **Change Password** | Settings → Change Password section |
| **Re-index** | Settings → "Reset Index" then "Start Indexing" |

---

## Troubleshooting

### "No emails found" after indexing
- Double-check the folder path is correct
- Make sure it contains .msg files
- Try "Reset Index" and re-index

### Login page keeps appearing
- Password is case-sensitive
- If you forget it, delete `settings.json` and restart

### App won't start
```bash
# Make sure you're in the project folder
cd /home/vikash/email-viewer

# Activate virtual environment
source venv/bin/activate

# Try again
python run.py
```

### Indexing very slow
- It's normal for large files (>100MB) or many attachments
- Leave it running; it will complete in background
- You can still use the app while indexing continues

---

## Project Structure

```
email-viewer/
├── run.py                 ← Start the app
├── requirements.txt
├── data/
│   └── email_index.db     (created on first run)
├── settings.json          (created on first run)
├── app/
│   ├── msg_parser.py      (handles OLE2 + MIME)
│   ├── indexer.py         (background indexing thread)
│   ├── db.py              (SQLite + FTS5)
│   ├── sanitizer.py       (HTML safety)
│   └── routes/            (6 API blueprints)
└── README.md              (full documentation)
```

---

## Data Storage

- **Emails**: Stored in `data/email_index.db` (SQLite)
- **Settings**: Stored in `settings.json` (root path, password hash)
- **Original files**: Never modified, read-only access
- **No cloud sync**: Everything is local

Both files are added to `.gitignore` to protect privacy.

---

## Performance Notes

- **First indexing**: 5000 files takes ~5-10 minutes
- **Subsequent loads**: Instant (index is persistent)
- **Search**: FTS5 returns results in <200ms typically
- **Memory**: App uses ~50-100MB normally

---

## Security

✅ **Local only** - Bound to 127.0.0.1 (not accessible from network)  
✅ **Password protected** - PBKDF2-SHA256 hashing  
✅ **HTML sanitized** - Email bodies cleaned before display  
✅ **No external requests** - Everything offline  
✅ **No temp files** - Attachments streamed from memory  

---

## Need Help?

1. **Check README.md** for detailed documentation
2. **Check logs** in console output
3. **Reset and try again**: Delete `data/email_index.db` and `settings.json`, restart
4. **Browser console**: Open DevTools (F12) to see any client-side errors

---

Enjoy your email viewer! 📧
