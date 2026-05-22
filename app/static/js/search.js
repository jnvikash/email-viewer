export const Search = (() => {
  let _onResult = null;
  let _onClear = null;
  let _debounceTimer = null;

  function init(onResult, onClear) {
    _onResult = onResult;
    _onClear = onClear;

    const input = document.getElementById('searchInput');
    const dropdown = document.getElementById('searchDropdown');
    const clearBtn = document.getElementById('clearSearch');

    input.addEventListener('input', () => {
      clearTimeout(_debounceTimer);
      const q = input.value.trim();
      clearBtn.style.display = q ? '' : 'none';
      if (!q) {
        _hideDropdown();
        return;
      }
      _debounceTimer = setTimeout(() => _liveSearch(q), 300);
    });

    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        clearTimeout(_debounceTimer);
        const q = input.value.trim();
        _hideDropdown();
        if (q && _onResult) _onResult(q);
      }
      if (e.key === 'Escape') {
        _hideDropdown();
        input.blur();
      }
    });

    document.addEventListener('click', e => {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        _hideDropdown();
      }
    });
  }

  async function _liveSearch(q) {
    try {
      const r = await fetch(`/api/search?q=${encodeURIComponent(q)}&per_page=8`);
      const data = await r.json();
      _showDropdown(data.emails || [], q);
    } catch (_) {
      _hideDropdown();
    }
  }

  function _showDropdown(emails, q) {
    const dropdown = document.getElementById('searchDropdown');
    if (!emails.length) {
      dropdown.innerHTML = '<div class="px-4 py-3 text-muted small">No results found</div>';
      dropdown.style.display = '';
      return;
    }

    dropdown.innerHTML = '';
    for (const e of emails) {
      const div = document.createElement('div');
      div.className = 'search-result-item';
      const snippet = e.snippet || e.body_preview || '';
      div.innerHTML = `
        <div class="sr-subject">${_esc(e.subject || '(No subject)')}</div>
        <div class="sr-meta">${_esc(e.sender_name || e.sender_email || '')} · ${_fmtDate(e.date_sent)}</div>
        ${snippet ? `<div class="sr-snippet">${snippet}</div>` : ''}
      `;
      div.addEventListener('mousedown', e => {
        e.preventDefault();
        _hideDropdown();
        if (_onResult) _onResult(q);
      });
      dropdown.appendChild(div);
    }

    const footer = document.createElement('div');
    footer.className = 'px-4 py-2 text-center border-top';
    footer.innerHTML = `<a href="#" class="small text-primary">See all results for "${_esc(q)}"</a>`;
    footer.addEventListener('mousedown', ev => {
      ev.preventDefault();
      _hideDropdown();
      if (_onResult) _onResult(q);
    });
    dropdown.appendChild(footer);
    dropdown.style.display = '';
  }

  function _hideDropdown() {
    document.getElementById('searchDropdown').style.display = 'none';
  }

  function clear() {
    document.getElementById('searchInput').value = '';
    document.getElementById('clearSearch').style.display = 'none';
    _hideDropdown();
    if (_onClear) _onClear();
  }

  function _esc(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function _fmtDate(iso) {
    try { return new Date(iso).toLocaleDateString(); } catch { return ''; }
  }

  return { init, clear };
})();
