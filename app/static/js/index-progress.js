export const IndexProgress = (() => {
  let _modal = null;
  let _onDone = null;

  function init(onDone) {
    _onDone = onDone;
    _modal = new bootstrap.Modal(document.getElementById('indexModal'));
  }

  async function checkOnLoad() {
    try {
      const r = await fetch('/api/index/status');
      const state = await r.json();

      if (state.status === 'running') {
        _showModal('Indexing your emails…');
        _streamProgress();
        return;
      }

      if (state.status === 'idle' && state.total_files === 0) {
        // Check if there are any emails indexed at all
        const er = await fetch('/api/emails?per_page=1');
        const ed = await er.json();
        if (ed.total === 0) {
          // No emails, no path configured — prompt user to go to settings
          const cfgR = await fetch('/api/config');
          const cfg = await cfgR.json();
          if (!cfg.root_path) {
            _showFirstRunBanner();
          }
        }
      }
    } catch (_) {}
  }

  function _showFirstRunBanner() {
    const layout = document.getElementById('mainLayout');
    const banner = document.createElement('div');
    banner.id = 'firstRunBanner';
    banner.style.cssText = 'position:fixed;top:52px;left:0;right:0;z-index:500;background:#0d6efd;color:#fff;text-align:center;padding:10px;';
    banner.innerHTML = `
      <i class="bi bi-info-circle me-2"></i>
      No email folder configured yet.
      <a href="/config" class="btn btn-light btn-sm ms-3">Open Settings</a>
    `;
    document.body.insertBefore(banner, layout);
  }

  function _showModal(msg) {
    document.getElementById('indexModalMsg').textContent = msg;
    document.getElementById('indexModalFooter').style.display = 'none';
    document.getElementById('modalProgressBar').style.width = '0%';
    document.getElementById('modalProgressBar').className = 'progress-bar progress-bar-striped progress-bar-animated';
    document.getElementById('modalProgressText').textContent = 'Starting…';
    _modal.show();
  }

  function _streamProgress() {
    const es = new EventSource('/api/index/progress');
    es.onmessage = e => {
      const d = JSON.parse(e.data);
      const bar = document.getElementById('modalProgressBar');
      bar.style.width = d.percent + '%';
      document.getElementById('modalProgressText').textContent =
        `${d.done} of ${d.total} files indexed (${d.skipped} skipped)`;

      if (d.status === 'done') {
        bar.classList.remove('progress-bar-animated');
        document.getElementById('indexModalMsg').textContent = `Done! ${d.done} emails indexed.`;
        document.getElementById('indexModalFooter').style.display = '';
        es.close();
        if (_onDone) _onDone();
      } else if (d.status === 'error') {
        bar.classList.add('bg-danger');
        bar.classList.remove('progress-bar-animated');
        document.getElementById('indexModalMsg').textContent = 'Indexing encountered an error.';
        document.getElementById('indexModalFooter').style.display = '';
        es.close();
      }
    };
    es.onerror = () => es.close();
  }

  return { init, checkOnLoad };
})();
