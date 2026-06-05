export const EmailList = (() => {
  let _state = {
    folder: '__all__',
    folderName: 'All Mail',
    page: 1,
    perPage: 50,
    sort: '-date',
    dateFrom: '',
    dateTo: '',
    fromEmail: '',
    toEmail: '',
    subjectQ: '',
    hasAttachment: false,
    searchMode: false,
    searchQuery: '',
  };
  let _onSelect = null;
  let _activeId = null;
  const _read = new Set(JSON.parse(localStorage.getItem('readEmails') || '[]'));

  function init(onSelect) {
    _onSelect = onSelect;
    window.EmailList = { setSort, applyFilter, clearFilter, toggleFilter, setFolder, setSearch, clearSearch };
  }

  function setFolder(path, name) {
    _state.folder = path;
    _state.folderName = name || path;
    _state.page = 1;
    _state.searchMode = false;
    _state.searchQuery = '';
    document.getElementById('listTitle').textContent = _state.folderName;
    _load();
  }

  function setSearch(query) {
    _state.searchMode = true;
    _state.searchQuery = query;
    _state.page = 1;
    document.getElementById('listTitle').textContent = `Search: "${query}"`;
    _load();
  }

  function clearSearch() {
    _state.searchMode = false;
    _state.searchQuery = '';
    document.getElementById('listTitle').textContent = _state.folderName;
    _load();
  }

  function setSort(sort) {
    _state.sort = sort;
    _state.page = 1;
    _load();
  }

  function toggleFilter() {
    const panel = document.getElementById('filterPanel');
    panel.style.display = panel.style.display === 'none' ? '' : 'none';
  }

  function _hasActiveFilters() {
    return !!(
      _state.dateFrom || _state.dateTo ||
      _state.fromEmail || _state.toEmail ||
      _state.subjectQ || _state.hasAttachment
    );
  }

  function _updateFilterBtn() {
    const btn = document.querySelector('[onclick="EmailList.toggleFilter()"]');
    if (!btn) return;
    if (_hasActiveFilters()) {
      btn.classList.add('btn-warning');
      btn.classList.remove('btn-outline-secondary');
    } else {
      btn.classList.remove('btn-warning');
      btn.classList.add('btn-outline-secondary');
    }
  }

  function applyFilter() {
    _state.dateFrom       = document.getElementById('filterDateFrom').value;
    _state.dateTo         = document.getElementById('filterDateTo').value;
    _state.fromEmail      = document.getElementById('filterFromEmail').value.trim();
    _state.toEmail        = document.getElementById('filterToEmail').value.trim();
    _state.subjectQ       = document.getElementById('filterSubject').value.trim();
    _state.hasAttachment  = document.getElementById('filterHasAttachment').checked;
    _state.page = 1;
    _updateFilterBtn();
    _load();
  }

  function clearFilter() {
    _state.dateFrom = '';
    _state.dateTo = '';
    _state.fromEmail = '';
    _state.toEmail = '';
    _state.subjectQ = '';
    _state.hasAttachment = false;
    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value = '';
    document.getElementById('filterFromEmail').value = '';
    document.getElementById('filterToEmail').value = '';
    document.getElementById('filterSubject').value = '';
    document.getElementById('filterHasAttachment').checked = false;
    _state.page = 1;
    _updateFilterBtn();
    _load();
  }

  async function _load() {
    const rows = document.getElementById('emailRows');
    rows.innerHTML = '<div class="empty-state"><div class="spinner-border spinner-border-sm" role="status"></div></div>';

    try {
      let data;

      // Append structured filter fields shared by both endpoints
      const _addFilters = (p) => {
        if (_state.dateFrom)      p.set('date_from',      _state.dateFrom);
        if (_state.dateTo)        p.set('date_to',        _state.dateTo);
        if (_state.fromEmail)     p.set('from_email',     _state.fromEmail);
        if (_state.toEmail)       p.set('to_email',       _state.toEmail);
        if (_state.subjectQ)      p.set('subject',        _state.subjectQ);
        if (_state.hasAttachment) p.set('has_attachment', '1');
      };

      if (_state.searchMode) {
        const p = new URLSearchParams({
          q: _state.searchQuery,
          folder: _state.folder,
          page: _state.page,
          per_page: _state.perPage,
        });
        _addFilters(p);
        const r = await fetch(`/api/search?${p}`);
        data = await r.json();
      } else {
        const p = new URLSearchParams({
          folder: _state.folder,
          page: _state.page,
          per_page: _state.perPage,
          sort: _state.sort,
        });
        _addFilters(p);
        const r = await fetch(`/api/emails?${p}`);
        data = await r.json();
      }

      _renderRows(data.emails || []);
      _renderPagination(data.total, data.page, data.per_page);
    } catch (e) {
      rows.innerHTML = `<div class="empty-state"><i class="bi bi-exclamation-triangle"></i><span>${e.message}</span></div>`;
    }
  }

  function _renderRows(emails) {
    const rows = document.getElementById('emailRows');
    if (!emails.length) {
      rows.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><span>No emails found</span></div>';
      return;
    }
    rows.innerHTML = '';
    for (const e of emails) {
      const div = document.createElement('div');
      div.className = 'email-row' + (_read.has(e.id) ? '' : ' unread') + (e.id === _activeId ? ' active' : '');
      div.dataset.id = e.id;

      const dateStr = e.date_sent ? _formatDate(e.date_sent) : '—';
      const snippet = e.snippet || e.body_preview || '';

      div.innerHTML = `
        <div class="email-sender">
          <span class="text-truncate">${_esc(e.sender_name || e.sender_email || 'Unknown')}</span>
          <span class="email-date">${dateStr}</span>
        </div>
        <div class="email-subject">${_esc(e.subject || '(No subject)')}</div>
        <div class="email-meta">
          ${snippet ? `<span class="email-preview">${snippet}</span>` : ''}
          ${e.attachment_count > 0 ? `<i class="bi bi-paperclip ms-auto flex-shrink-0"></i>` : ''}
          ${e.importance === 'high' ? `<i class="bi bi-exclamation-circle text-danger flex-shrink-0"></i>` : ''}
        </div>
      `;

      div.addEventListener('click', () => {
        document.querySelectorAll('.email-row').forEach(r => r.classList.remove('active'));
        div.classList.add('active');
        div.classList.remove('unread');
        _activeId = e.id;
        _read.add(e.id);
        localStorage.setItem('readEmails', JSON.stringify([..._read].slice(-2000)));
        if (_onSelect) _onSelect(e.id);
      });

      rows.appendChild(div);
    }
  }

  function _renderPagination(total, page, perPage) {
    const info = document.getElementById('paginationInfo');
    const pages = document.getElementById('paginationPages');
    const totalPages = Math.ceil(total / perPage);
    const start = (page - 1) * perPage + 1;
    const end = Math.min(page * perPage, total);

    info.textContent = total ? `${start}–${end} of ${total}` : 'No emails';
    pages.innerHTML = '';

    if (totalPages <= 1) return;

    const mkLi = (label, pg, disabled = false, active = false) => {
      const li = document.createElement('li');
      li.className = `page-item${disabled ? ' disabled' : ''}${active ? ' active' : ''}`;
      const a = document.createElement('a');
      a.className = 'page-link';
      a.href = '#';
      a.innerHTML = label;
      if (!disabled && !active) a.addEventListener('click', e => { e.preventDefault(); _state.page = pg; _load(); });
      li.appendChild(a);
      return li;
    };

    pages.appendChild(mkLi('&laquo;', page - 1, page === 1));

    const range = _pageRange(page, totalPages);
    let last = 0;
    for (const p of range) {
      if (p - last > 1) {
        const li = document.createElement('li');
        li.className = 'page-item disabled';
        li.innerHTML = '<span class="page-link">…</span>';
        pages.appendChild(li);
      }
      pages.appendChild(mkLi(p, p, false, p === page));
      last = p;
    }

    pages.appendChild(mkLi('&raquo;', page + 1, page === totalPages));
  }

  function _pageRange(current, total) {
    const delta = 2;
    const range = [];
    for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) range.push(i);
    if (range[0] > 1) range.unshift(1);
    if (range[range.length - 1] < total) range.push(total);
    return range;
  }

  function _formatDate(iso) {
    try {
      const d = new Date(iso);
      const now = new Date();
      const diff = now - d;
      if (diff < 86400000 && d.getDate() === now.getDate()) {
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      if (diff < 604800000) {
        return d.toLocaleDateString([], { weekday: 'short' });
      }
      return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: d.getFullYear() !== now.getFullYear() ? 'numeric' : undefined });
    } catch { return iso; }
  }

  function _esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  return { init, setFolder, setSearch, clearSearch, setSort, toggleFilter, applyFilter, clearFilter, reload: _load };
})();
