export const FolderTree = (() => {
  let _onSelect = null;
  let _activePath = '__all__';

  function init(onSelect) {
    _onSelect = onSelect;
  }

  async function reload() {
    const container = document.getElementById('folderTree');
    container.innerHTML = '<div class="px-3 py-2 text-muted small">Loading…</div>';
    try {
      const r = await fetch('/api/folders');
      if (!r.ok) throw new Error('Failed to load folders');
      const tree = await r.json();
      container.innerHTML = '';
      const ul = _renderList(tree, 0);
      container.appendChild(ul);
      _setActive(_activePath, false);
    } catch (e) {
      container.innerHTML = `<div class="px-3 py-2 text-danger small">${e.message}</div>`;
    }
  }

  function _renderList(nodes, depth) {
    const ul = document.createElement('ul');
    ul.style.paddingLeft = depth > 0 ? '16px' : '0';
    ul.classList.add('folder-list');

    for (const node of nodes) {
      const li = document.createElement('li');

      const item = document.createElement('div');
      item.className = 'folder-item';
      item.dataset.path = node.path;

      // Toggle arrow (only if has children)
      const toggle = document.createElement('span');
      toggle.className = 'folder-toggle';
      if (node.children && node.children.length) {
        toggle.innerHTML = '<i class="bi bi-chevron-down" style="font-size:10px"></i>';
      } else {
        toggle.innerHTML = '<i class="bi bi-dot" style="font-size:10px;opacity:.3"></i>';
      }

      const icon = document.createElement('i');
      icon.className = node.path === '__all__'
        ? 'bi bi-inbox text-primary'
        : 'bi bi-folder text-warning';
      icon.style.fontSize = '14px';

      const name = document.createElement('span');
      name.className = 'folder-name';
      name.textContent = node.name;

      const badge = document.createElement('span');
      badge.className = 'badge bg-secondary rounded-pill';
      badge.textContent = node.email_count;
      if (node.email_count === 0) badge.style.opacity = '0.4';

      item.appendChild(toggle);
      item.appendChild(icon);
      item.appendChild(name);
      item.appendChild(badge);

      item.addEventListener('click', (e) => {
        e.stopPropagation();
        _setActive(node.path);
        if (_onSelect) _onSelect(node.path, node.name);
      });

      li.appendChild(item);

      if (node.children && node.children.length) {
        const childContainer = document.createElement('div');
        childContainer.className = 'folder-children';
        childContainer.appendChild(_renderList(node.children, depth + 1));
        li.appendChild(childContainer);

        toggle.addEventListener('click', (e) => {
          e.stopPropagation();
          const collapsed = childContainer.classList.toggle('collapsed');
          toggle.innerHTML = collapsed
            ? '<i class="bi bi-chevron-right" style="font-size:10px"></i>'
            : '<i class="bi bi-chevron-down" style="font-size:10px"></i>';
        });
      }

      ul.appendChild(li);
    }
    return ul;
  }

  function _setActive(path, triggerSelect = true) {
    _activePath = path;
    document.querySelectorAll('.folder-item').forEach(el => {
      el.classList.toggle('active', el.dataset.path === path);
    });
  }

  return { init, reload };
})();
