// Live indexing monitor - polls and updates UI during email indexing

export const IndexMonitor = (() => {
  let pollInterval = null;
  const POLL_INTERVAL = 2000; // Poll every 2 seconds

  const show = (status) => {
    const banner = document.getElementById('indexingBanner');
    const bar = document.getElementById('indexingBar');
    const count = document.getElementById('indexingCount');
    const total = document.getElementById('indexingTotal');
    const percent = document.getElementById('indexingPercent');

    if (status.indexing) {
      count.textContent = status.indexed_count;
      total.textContent = status.total_files;
      percent.textContent = status.percent + '%';
      bar.style.width = status.percent + '%';
      banner.style.display = '';
    } else {
      banner.style.display = 'none';
    }
  };

  const poll = async () => {
    try {
      const resp = await fetch('/api/emails/index-status');
      const status = await resp.json();

      // Update banner
      show(status);

      // If indexing, auto-refresh folder tree and email list
      if (status.indexing) {
        // Refresh folder tree to show newly indexed emails
        if (window.FolderTree && window.FolderTree.reload) {
          FolderTree.reload();
        }
        // Refresh email list if one is active
        if (window.EmailList && window.EmailList.reload) {
          EmailList.reload();
        }
      } else {
        // Indexing complete, do final refresh
        if (window.FolderTree && window.FolderTree.reload) {
          FolderTree.reload();
        }
        if (window.EmailList && window.EmailList.reload) {
          EmailList.reload();
        }
        // Stop polling
        stop();
      }
    } catch (e) {
      console.error('IndexMonitor poll error:', e);
    }
  };

  const start = () => {
    if (pollInterval) return; // Already running
    poll(); // Immediate first poll
    pollInterval = setInterval(poll, POLL_INTERVAL);
  };

  const stop = () => {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  };

  // Auto-detect if indexing is in progress on page load
  const init = () => {
    fetch('/api/emails/index-status')
      .then(r => r.json())
      .then(status => {
        if (status.indexing) {
          show(status);
          start();
        }
      })
      .catch(e => console.error('IndexMonitor init error:', e));
  };

  return { init, start, stop, show, poll };
})();

