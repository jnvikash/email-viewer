# Email Viewer — Installation Guide

Complete installation instructions for all platforms.

---

## Option 1: Quick Install with Make (Recommended)

**Requirements:** Python 3.10+, Make

```bash
cd email-viewer
make setup     # One command: venv + dependencies + database
make run       # Start the application
```

Then visit http://localhost:5000

---

## Option 2: Manual Installation

**Requirements:** Python 3.10+

### Step 1: Create Virtual Environment

```bash
cd email-viewer
python3 -m venv venv
```

### Step 2: Activate Virtual Environment

**On Linux/Mac:**
```bash
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

### Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Initialize Database

```bash
python -c "from app.db import init_db; init_db(); print('✓ Database initialized')"
```

### Step 6: Run the Application

```bash
python run.py
```

Then visit http://localhost:5000

---

## Option 3: Docker Installation

**Requirements:** Docker, Docker Compose

```bash
cd email-viewer
docker-compose up --build
```

Then visit http://localhost:5000

To stop: Press `Ctrl+C` or run `docker-compose down`

---

## Option 4: Docker (Without Compose)

**Build the image:**
```bash
docker build -t email-viewer .
```

**Run the container:**
```bash
docker run -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/settings.json:/app/settings.json \
  email-viewer
```

Then visit http://localhost:5000

---

## Verify Installation

After installing, verify everything works:

```bash
make validate
```

Or manually:

```bash
cd email-viewer
source venv/bin/activate
python scripts/validate.py
```

You should see:
```
✓ Python version 3.11
✓ Virtual environment exists
✓ All required packages installed
✓ Database initialized with 7 tables
✓ Configuration file exists
✓ Flask app created successfully

Result: 6/6 checks passed
✓ Setup is complete! Run: make run
```

---

## Post-Installation

### 1. Start the Application

```bash
make run
# or
python run.py
```

### 2. Create Admin Account

- Visit http://localhost:5000
- Click "Create an admin account"
- Enter credentials and optional email folder path
- Create account

### 3. Configure and Index Emails

- Go to Settings (⚙️)
- Set or verify email folder path
- Click "Start Indexing"
- Wait for completion

### 4. Start Browsing

- Click folders on left pane to browse emails
- Click emails to read full content
- Use search bar to find emails

---

## Installation Troubleshooting

### Python Version Error

If you get "python3: command not found" or version too old:

**Check your Python version:**
```bash
python --version
python3 --version
```

**Solution:** Install Python 3.10+
- **Ubuntu/Debian:** `sudo apt-get install python3.10-dev python3.10-venv`
- **Mac:** `brew install python@3.11`
- **Windows:** Download from python.org

### Permission Denied Errors

On Linux/Mac, if you get permission errors:

```bash
chmod +x venv/bin/python
chmod +x venv/bin/activate
```

### Port Already in Use

If port 5000 is in use:

**Option 1: Stop the other app**
```bash
# Find what's using port 5000
lsof -i :5000

# Kill it
kill -9 <PID>
```

**Option 2: Use a different port**

Edit `run.py` and change:
```python
app.run(host="127.0.0.1", port=5000)  # Change 5000 to 5001
```

### Missing Dependencies

If you get "ModuleNotFoundError":

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database Lock Error

If you get "database is locked":

```bash
# Stop all instances of the app
make clean
make setup
make run
```

### Virtual Environment Issues

If venv seems broken:

```bash
# Remove and recreate
rm -rf venv
make setup
make run
```

---

## System-Specific Notes

### Linux

**Debian/Ubuntu:**
```bash
sudo apt-get install python3.10-dev python3.10-venv libmagic1
cd email-viewer
make setup
make run
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-devel python3-virtualenv file-libs
cd email-viewer
make setup
make run
```

### macOS

```bash
brew install python@3.11
cd email-viewer
make setup
make run
```

### Windows

**PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "from app.db import init_db; init_db()"
python run.py
```

**Command Prompt:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -c "from app.db import init_db; init_db()"
python run.py
```

**Windows Subsystem for Linux (WSL):**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from app.db import init_db; init_db()"
python run.py
```

### Docker on Different Systems

**Linux/Mac:**
```bash
docker-compose up
```

**Windows:**
```powershell
docker-compose up
```

Or use Docker Desktop GUI.

---

## Upgrade Instructions

### Update Dependencies

```bash
make install
```

Or manually:
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Update Application Code

If installing from git:

```bash
git pull origin main
make install
make run
```

---

## Uninstall

### Remove All (Clean Slate)

```bash
make clean
```

This removes the virtual environment. To completely uninstall:

```bash
make clean
rm -rf data/
rm -f settings.json
```

---

## Next Steps

See:
- **QUICKSTART.md** — Quick reference for common tasks
- **SETUP.md** — Comprehensive setup guide with troubleshooting
- **DEVELOPMENT.md** — Guide for developers

---

## Need Help?

1. Check `SETUP.md` for common issues
2. Run `make validate` to diagnose
3. Check `data/email_index.db` exists
4. Try `make reset-all` for a clean slate
