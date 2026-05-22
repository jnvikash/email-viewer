import { FolderTree } from './folder-tree.js';
import { EmailList } from './email-list.js';
import { ReadingPane } from './reading-pane.js';
import { Search } from './search.js';
import { IndexProgress } from './index-progress.js';

// Expose globals needed by inline event handlers in HTML
window.FolderTree = FolderTree;
window.EmailList = EmailList;
window.App = { clearSearch };

document.addEventListener('DOMContentLoaded', () => {
  // Initialize all components
  IndexProgress.init(() => {
    FolderTree.reload();
    EmailList.reload();
  });

  FolderTree.init((path, name) => {
    document.getElementById('clearSearch').style.display = 'none';
    document.getElementById('searchInput').value = '';
    EmailList.setFolder(path, name);
  });

  EmailList.init((emailId) => {
    ReadingPane.load(emailId);
  });

  Search.init(
    (query) => {
      EmailList.setSearch(query);
    },
    () => {
      EmailList.clearSearch();
    }
  );

  // Load initial data
  FolderTree.reload().then(() => {
    EmailList.setFolder('__all__', 'All Mail');
  });

  // Check indexing state on load
  IndexProgress.checkOnLoad();
});

function clearSearch() {
  Search.clear();
  EmailList.clearSearch();
}
