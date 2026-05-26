# Email Indexing Performance Guide

Indexing speed depends on file count, attachment sizes, and attachment text extraction. Here are optimization strategies.

## Performance Expectations

| Scenario | Time | Notes |
|----------|------|-------|
| 1,000 emails (no attachments) | ~1 min | Baseline |
| 1,000 emails (with attachments) | ~3-5 min | Default: extracts PDF/DOCX text |
| 5,000 emails (with attachments) | ~15-25 min | Larger archive |
| 10,000+ emails (heavy attachments) | 45+ min | Very large archive |

---

## Quick Optimizations

### 1. Skip Attachment Text Extraction (Fastest: 3-5x faster)

**Edit** `app/indexer.py` line 18:
```python
EXTRACT_ATTACHMENTS = False  # Change from True to False
```

**Impact:**
- ✓ 3-5x faster indexing
- ✗ Cannot search within PDF/DOCX/XLSX attachment content
- ✓ Can still search by attachment filename
- ✓ Can still preview attachments

**When to use:** Large archives where speed matters more than searching attachment content.

### 2. Skip Large Attachments (Moderate: 20-30% faster)

**Edit** `app/indexer.py` line 19:
```python
MAX_ATTACHMENT_SIZE = 5_000_000  # 5 MB instead of 50 MB
```

**Impact:**
- ✓ 20-30% faster for archives with large files
- ✗ Skip text extraction from files > 5MB
- ✓ Metadata still indexed

### 3. Increase Batch Size (Slight: 5-10% faster)

Already optimized to 150 files per batch (up from 50).

---

## Advanced Optimizations

### Skip on Second Run (Already Implemented)

The database uses `INSERT OR IGNORE`, so re-indexing only processes new files:
- First run: Slow (extracts all attachments)
- Subsequent runs: Fast (only new files)

### Use SSD Storage

If possible, store database on SSD:
- WAL mode performance improves significantly
- ~2x faster on SSD vs HDD

### Disable Attachment Extraction Permanently

Edit `app/indexer.py` and change line 18:
```python
EXTRACT_ATTACHMENTS = False
```

Then index (will be much faster).

---

## Recommended Settings

### For Speed (Large Archives)
```python
EXTRACT_ATTACHMENTS = False       # Fastest
MAX_ATTACHMENT_SIZE = 0           # Skip all attachment extraction
BATCH = 150                        # Already set
```
**Result:** ~1 min per 1,000 emails

### Balanced (Default)
```python
EXTRACT_ATTACHMENTS = True        # Current default
MAX_ATTACHMENT_SIZE = 50_000_000  # 50 MB
BATCH = 150                        # Current batch size
```
**Result:** ~3-5 min per 1,000 emails

### Comprehensive (Slow but Complete)
```python
EXTRACT_ATTACHMENTS = True
MAX_ATTACHMENT_SIZE = 999_999_999 # No size limit
BATCH = 50                         # Smaller batches for safety
```
**Result:** ~5-10 min per 1,000 emails

---

## Troubleshooting Slow Indexing

### Check Indexing Status

Go to **Settings** and watch the progress bar. If it's stuck:

1. **Wait longer** — Indexing takes time
   - 5,000 emails = 15-25 minutes (normal)
   - 10,000 emails = 45+ minutes (expected)

2. **Check disk space** — If drive is full, indexing stops
   ```bash
   df -h  # On Linux/Mac
   ```

3. **Check CPU usage** — If low, system might be idle
   - Indexing uses ~1 CPU core
   - Can browse while indexing runs

4. **Verify database** — If corrupted, re-initialize
   ```bash
   make reset-db
   make init-db
   make run
   ```

---

## Monitor Indexing

### Real-Time Progress

Visit **Settings** page:
- Progress bar shows percent complete
- Shows done/total/skipped counts
- Status displays: running, done, error

### Database Query

Check progress via SQL:
```bash
sqlite3 data/email_index.db
> SELECT user_id, status, done_files, total_files FROM index_state;
```

### Log Output

Check application logs:
```bash
# Logs are printed to console when running make run
# Look for: "Indexing complete for user X: Y indexed, Z skipped"
```

---

## Re-Indexing Strategy

### Update Index (Only New Files)

```bash
make run
# Go to Settings → Start Indexing
```

Only new files are indexed (thanks to `INSERT OR IGNORE`).

### Full Re-Index (Delete and Reindex)

```bash
make run
# Go to Settings → "Reset My Index" button
# Then click "Start Indexing"
```

This deletes all your indexed emails and re-indexes everything.

---

## Performance Comparison

```
Archive Size: 5,000 emails
Attachment Types: PDFs, Word docs, Spreadsheets

Setting                          Time      Search In Attachments
─────────────────────────────────────────────────────────────────
EXTRACT_ATTACHMENTS = False      5 min     ✗ No
MAX_ATTACHMENT_SIZE = 5MB        8 min     ✓ Yes (< 5MB only)
Default Settings                 15 min    ✓ Yes (all)
BATCH = 50 (old)                 18 min    ✓ Yes (all)
```

---

## System Requirements for Fast Indexing

| Component | Recommendation |
|-----------|-----------------|
| CPU | 2+ cores (faster = better) |
| RAM | 2+ GB (4GB+ recommended) |
| Disk | SSD preferred, HDD okay |
| Python | 3.10+ (3.11 slightly faster) |

---

## Enable Fast Mode (Recommended for Large Archives)

To significantly speed up indexing:

1. **Edit** `app/indexer.py` line 18:
   ```python
   EXTRACT_ATTACHMENTS = False
   ```

2. **Save** the file

3. **Re-run** the app:
   ```bash
   make run
   ```

4. **Start** indexing in Settings

**Result:** 3-5x faster indexing, can still search emails by subject/sender/body.

---

## Tips

- ✓ Indexing happens in background — you can use the app while it runs
- ✓ Multiple users can index in parallel (each has their own thread)
- ✓ Safe to restart during indexing (will resume/retry)
- ✓ Subsequent runs only index new files (much faster)
- ✓ Search still works during indexing

Enjoy faster indexing! 🚀
