# Email Viewer — Complete Setup Guide (Multi-User)

This guide walks you through setting up the multi-user Email Viewer application.

## Quick Start

```bash
cd email-viewer
make setup    # One-time: create venv, install deps, init database
make run      # Start the application
```

Then open **http://localhost:5000** in your browser.

---

## Detailed Setup Steps

### Step 1: Prerequisites

- **Python 3.10+** (check with `python3 --version`)
- **pip** and **venv** (included with Python)
- A terminal/command prompt
- ~500MB free disk space (more if indexing large email archives)

### Step 2: Create Virtual Environment & Install Dependencies

```bash
cd /path/to/email-viewer
make setup
```

This single command:
- Creates `venv/` directory with isolated Python environment
- Installs all required packages from `requirements.txt`
- Initializes the SQLite database
- Creates necessary directories

**Manual alternative** (if `make` is not available):
```bash
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python venv/bin/python -c "from app.db import init_db; init_db()"
```

### Step 3: Configure Application (Optional)

```bash
make config
```

This allows you to set the global email folder path. You can also configure this later through the Settings page.

### Step 4: Start the Application

```bash
make run
```

You should see:
```
Starting Email Viewer...
Open http://localhost:5000 in your browser
Press Ctrl+C to stop
```

### Step 5: Create Admin Account

1. Open **http://localhost:5000** in your browser
2. Click "Create an admin account" link
3. Enter:
   - **Username**: Your login name (min. 3 chars)
   - **Password**: Strong password (min. 6 chars)
   - **Email Folder** (optional): Path to `.msg` files folder
4. Click "Create Admin Account"

### Step 6: Configure Email Folder & Start Indexing

After login:

1. Go to **Settings** (⚙️ icon)
2. Configure your email folder path (the directory containing `.msg` files)
3. Click **"Start Indexing"**
4. Wait for indexing to complete (progress shown in modal)
5. Once done, the **Folder Tree** will populate on the left

---

## Admin Features

If you have an admin account, you can:

### Manage Users

Go to **Admin** → **Manage Users** to:

- **Create new users** — Username, password, assign email folder
- **Edit user folders** — Change their email folder path
- **Change passwords** — Reset user passwords
- **Promote to admin** — Give users admin privileges
- **Deactivate/activate users** — Soft-delete users (data preserved)

### Admin Dashboard

View at **Admin** → **Dashboard**:

- Total users and emails indexed
- Recent user accounts
- Indexing progress per user
- User status and folder assignments

---

## Common Tasks

### Run the Application

```bash
make run
```

### Create a New User (as admin)

1. Log in with admin account
2. Go to **Admin** → **Manage Users**
3. Click **"Create New User"**
4. Fill in username, password, email folder
5. Click **"Create User"**

### Change User Email Folder (as admin)

1. Go to **Admin** → **Manage Users**
2. Click the **edit icon** (✏️) next to the user
3. Update the **Email Folder Path**
4. Click **"Save Changes"**

### Deactivate a User (as admin)

1. Go to **Admin** → **Manage Users**
2. Click the **deactivate icon** (⊘) next to the user
3. Confirm

Deactivated users cannot log in, but their data remains in the database.

### Reset User's Index

Go to **Settings** → **"Reset My Index"** to clear your indexed emails and re-index.

### Reindex Your Emails

1. Go to **Settings**
2. Click **"Start Indexing"**
3. Wait for completion

---

## Database Management

### Reset Everything (Destructive)

```bash
make reset-all
```

This will:
- Delete the virtual environment
- Delete the database (all users and emails)
- Reset configuration files
- Prompt for confirmation

Then run `make setup` again to start fresh.

### Reset Database Only (Keep venv)

```bash
make reset-db
```

This will:
- Delete all users, emails, and indexed data
- Keep the virtual environment and dependencies
- Require confirmation

Then run `make init-db` to reinitialize.

### View Makefile Targets

```bash
make help
```

---

## File Structure

```
email-viewer/
├── Makefile                # Setup and management commands
├── requirements.txt        # Python package dependencies
├── run.py                  # Application entry point
├── settings.json           # App configuration (gitignored)
├── data/
│   └── email_index.db      # SQLite database (gitignored)
├── scripts/
│   ├── setup_config.py     # Interactive configuration
│   └── reset_db.py         # Database reset utility
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── config.py           # Configuration manager
│   ├── auth.py             # Multi-user auth
│   ├── db.py               # Database schema and connection
│   ├── indexer.py          # Background email indexing
│   ├── msg_parser.py       # .msg/.eml file parsing
│   ├── sanitizer.py        # HTML sanitization
│   ├── routes/             # API and page routes
│   ├── templates/          # HTML templates
│   └── static/             # CSS and JavaScript
└── venv/                   # Python virtual environment (gitignored)
```

---

## Troubleshooting

### "Virtual environment not found"

Run `make setup` again or manually create one:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "settings.json not found"

Run `make config` or manually create one:
```bash
python venv/bin/python -c "from app.config import AppConfig, save_config; cfg = AppConfig(); save_config(cfg); print('Created settings.json')"
```

### "Database error" during startup

Try resetting the database:
```bash
make reset-db
make init-db
make run
```

### Indexing is very slow

- Indexing speed depends on:
  - Number of files (5,000 files ≈ 5-10 minutes on typical hardware)
  - File size (larger attachments take longer)
  - Disk I/O performance
- You can continue using the app while indexing runs in background

### Files not appearing after indexing

1. Verify the folder path is correct (with trailing slash if needed)
2. Check that files are actually `.msg` or `.eml` format
3. Check for errors in Settings page during indexing
4. Try resetting index and re-running

### "Permission denied" on Linux/Mac

If you get permission errors:
```bash
chmod +x venv/bin/python
chmod +x venv/bin/activate
make run
```

---

## Security Notes

- **Passwords**: Hashed with PBKDF2-SHA256 (werkzeug)
- **Session cookies**: SameSite=Lax, HttpOnly flag set
- **File access**: All file paths validated via database (no path traversal)
- **Binding**: App binds to `127.0.0.1:5000` (localhost only, not exposed on network)
- **Secret key**: Auto-generated on first run, stored in `settings.json`

---

## Next Steps

- **Browse emails**: Click folders on the left to view emails
- **Search**: Use the search bar to find emails by subject, sender, or content
- **Configure additional users**: Use Admin → Manage Users (admin only)
- **Set email folders per user**: Edit each user to assign their own email archive path
- **Invite team members**: Create accounts and set their folder paths

Enjoy!
