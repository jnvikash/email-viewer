export const ReadingPane = (() => {
  const MIME_ICONS = {
    'application/pdf': 'bi-file-earmark-pdf text-danger',
    'image/': 'bi-file-earmark-image text-info',
    'application/vnd.openxmlformats-officedocument.wordprocessingml': 'bi-file-earmark-word text-primary',
    'application/msword': 'bi-file-earmark-word text-primary',
    'application/vnd.openxmlformats-officedocument.spreadsheetml': 'bi-file-earmark-excel text-success',
    'application/vnd.ms-excel': 'bi-file-earmark-excel text-success',
    'application/vnd.openxmlformats-officedocument.presentationml': 'bi-file-earmark-ppt text-warning',
    'text/': 'bi-file-earmark-text text-secondary',
    'application/zip': 'bi-file-earmark-zip text-secondary',
  };

  function _mimeIcon(mime) {
    for (const [prefix, cls] of Object.entries(MIME_ICONS)) {
      if (mime && mime.startsWith(prefix)) return cls;
    }
    return 'bi-file-earmark text-secondary';
  }

  function _fmtSize(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function _esc(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function _formatFullDate(iso) {
    try {
      return new Date(iso).toLocaleString([], { dateStyle: 'long', timeStyle: 'short' });
    } catch { return iso || ''; }
  }

  async function load(emailId) {
    document.getElementById('readingEmpty').style.display = 'none';
    document.getElementById('readingContent').style.display = 'flex';

    const header = document.getElementById('emailHeader');
    header.innerHTML = '<div class="text-muted small py-2">Loading…</div>';

    const iframe = document.getElementById('emailIframe');
    iframe.srcdoc = '';

    const attSection = document.getElementById('attachmentSection');
    attSection.style.display = 'none';

    try {
      const r = await fetch(`/api/emails/${emailId}`);
      if (!r.ok) throw new Error('Failed to load email');
      const email = await r.json();

      _renderHeader(email);
      _renderBody(email);
      _renderAttachments(email.attachments || [], emailId);
    } catch (e) {
      header.innerHTML = `<div class="text-danger small">${e.message}</div>`;
    }
  }

  function _renderHeader(email) {
    const header = document.getElementById('emailHeader');
    const recipients = (email.recipients || []).map(r => r.name ? `${_esc(r.name)} &lt;${_esc(r.email)}&gt;` : _esc(r.email)).join(', ');
    const importanceBadge = email.importance === 'high'
      ? '<span class="importance-high ms-2"><i class="bi bi-exclamation-circle-fill"></i> High</span>'
      : email.importance === 'low'
      ? '<span class="importance-low ms-2"><i class="bi bi-arrow-down-circle"></i> Low</span>'
      : '';

    header.innerHTML = `
      <h5 class="subject-line">${_esc(email.subject || '(No subject)')}${importanceBadge}</h5>
      <div class="header-row">
        <span class="header-label">From</span>
        <span class="header-value">${email.sender_name ? `<strong>${_esc(email.sender_name)}</strong> &lt;${_esc(email.sender_email)}&gt;` : _esc(email.sender_email || '—')}</span>
      </div>
      ${recipients ? `<div class="header-row"><span class="header-label">To</span><span class="header-value">${recipients}</span></div>` : ''}
      <div class="header-row">
        <span class="header-label">Date</span>
        <span class="header-value">${_formatFullDate(email.date_sent)}</span>
      </div>
    `;
  }

  function _renderBody(email) {
    const iframe = document.getElementById('emailIframe');
    let content = '';

    if (email.body_html) {
      content = `<!DOCTYPE html><html><head><meta charset="utf-8">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size:14px; padding:16px 20px; color:#333; margin:0; }
          img { max-width:100%; height:auto; }
          a { color:#0d6efd; }
          pre { white-space:pre-wrap; }
          table { border-collapse:collapse; max-width:100%; }
        </style></head><body>${email.body_html}</body></html>`;
    } else if (email.body_text) {
      const escaped = email.body_text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      content = `<!DOCTYPE html><html><head><meta charset="utf-8">
        <style>body{font-family:monospace;font-size:13px;padding:16px;white-space:pre-wrap;color:#333;margin:0;}</style>
        </head><body>${escaped}</body></html>`;
    } else {
      content = `<!DOCTYPE html><html><body style="padding:20px;color:#888;font-family:sans-serif">(No message body)</body></html>`;
    }

    iframe.srcdoc = content;
  }

  function _renderAttachments(attachments, emailId) {
    const section = document.getElementById('attachmentSection');
    const list = document.getElementById('attachmentList');
    list.innerHTML = '';

    if (!attachments.length) {
      section.style.display = 'none';
      return;
    }

    section.style.display = '';
    for (const att of attachments) {
      const idx = att.attach_index;
      const card = document.createElement('div');
      card.className = 'att-card';

      card.innerHTML = `
        <i class="bi ${_mimeIcon(att.mime_type)} att-icon"></i>
        <div class="att-info">
          <div class="att-name" title="${_esc(att.filename)}">${_esc(att.filename)}</div>
          <div class="att-size">${_fmtSize(att.size_bytes)}</div>
        </div>
        <div class="att-actions">
          ${_isPreviewable(att.mime_type) ? `<button class="btn btn-link btn-sm p-0 text-primary" title="Preview" onclick="ReadingPane.previewAtt(${emailId},${idx},'${_esc(att.filename)}','${_esc(att.mime_type)}')"><i class="bi bi-eye"></i></button>` : ''}
          <a href="/api/attachments/${emailId}/${idx}/download" class="btn btn-link btn-sm p-0 text-secondary" title="Download"><i class="bi bi-download"></i></a>
        </div>
      `;

      list.appendChild(card);
    }
  }

  function _isPreviewable(mime) {
    if (!mime) return false;
    return mime.startsWith('image/') || mime === 'application/pdf' || mime.startsWith('text/');
  }

  function previewAtt(emailId, attachIndex, filename, mimeType) {
    const dialog = document.getElementById('attachPreviewDialog');
    document.getElementById('previewTitle').textContent = filename;
    const body = document.getElementById('previewBody');
    const url = `/api/attachments/${emailId}/${attachIndex}/preview`;

    if (mimeType.startsWith('image/')) {
      body.innerHTML = `<img src="${url}" style="max-width:100%;display:block;padding:16px">`;
    } else if (mimeType === 'application/pdf') {
      body.innerHTML = `<embed src="${url}" type="application/pdf" style="width:100%;height:70vh">`;
    } else {
      body.innerHTML = `<iframe src="${url}" style="width:100%;height:70vh;border:none"></iframe>`;
    }

    dialog.showModal();
  }

  // Expose previewAtt globally for inline onclick handlers
  window.ReadingPane = { previewAtt };

  return { load };
})();
