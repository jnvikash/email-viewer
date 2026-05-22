# Quick Start Guide

## 1. Start the Application

```bash
cd /home/vikash/email-viewer
python run.py
```

You'll see:
```
Email Viewer running at http://localhost:5000
```

## 2. Open in Browser

Navigate to: **http://localhost:5000**

## 3. First Run - Set Password

- You'll see a login page asking you to create a password
- Enter any password you want to use
- Click "Set Password & Continue"

## 4. Configure Email Folder

- Click the **Settings** (⚙️) button in the top right
- Enter the **absolute path** to your .msg files folder:
  ```
  /mnt/c/Users/User/Documents/msg
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
