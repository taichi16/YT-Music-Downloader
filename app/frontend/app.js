// Tab Elements
const tabYtBtn = document.getElementById('tabYtBtn');
const tabIphoneBtn = document.getElementById('tabIphoneBtn');
const ytSection = document.getElementById('ytSection');
const iphoneSection = document.getElementById('iphoneSection');

// YouTube Downloader Elements
const urlInput = document.getElementById('urlInput');
const pasteBtn = document.getElementById('pasteBtn');
const fetchBtn = document.getElementById('fetchBtn');
const previewCard = document.getElementById('previewCard');
const previewThumb = document.getElementById('previewThumb');
const previewTitle = document.getElementById('previewTitle');
const previewSubtitle = document.getElementById('previewSubtitle');
const previewCount = document.getElementById('previewCount');
const previewType = document.getElementById('previewType');
const toggleTrackListBtn = document.getElementById('toggleTrackListBtn');
const trackListDrawer = document.getElementById('trackListDrawer');
const trackListUl = document.getElementById('trackListUl');
const trackListSummary = document.getElementById('trackListSummary');
const segmentBtns = document.querySelectorAll('.segment-btn');
const audioOptions = document.getElementById('audioOptions');
const videoOptions = document.getElementById('videoOptions');
const audioFormatSelect = document.getElementById('audioFormatSelect');
const audioQualitySelect = document.getElementById('audioQualitySelect');
const videoQualitySelect = document.getElementById('videoQualitySelect');
const videoFormatSelect = document.getElementById('videoFormatSelect');
const syncAppleMusicToggle = document.getElementById('syncAppleMusicToggle');
const embedThumbnailToggle = document.getElementById('embedThumbnailToggle');
const embedMetadataToggle = document.getElementById('embedMetadataToggle');
const outputFolderSelect = document.getElementById('outputFolderSelect');
const startDownloadBtn = document.getElementById('startDownloadBtn');
const startBtnText = document.getElementById('startBtnText');
const progressPanel = document.getElementById('progressPanel');
const progressStatusTitle = document.getElementById('progressStatusTitle');
const progressStatusDetail = document.getElementById('progressStatusDetail');
const progressPctText = document.getElementById('progressPctText');
const progressBarFill = document.getElementById('progressBarFill');
const progressSpinner = document.getElementById('progressSpinner');
const statTrackCount = document.getElementById('statTrackCount');
const statSpeed = document.getElementById('statSpeed');
const statEta = document.getElementById('statEta');
const statSize = document.getElementById('statSize');
const completionActions = document.getElementById('completionActions');
const completionMessage = document.getElementById('completionMessage');
const openFolderBtn = document.getElementById('openFolderBtn');
const openMusicAppBtn = document.getElementById('openMusicAppBtn');
const aboutBtn = document.getElementById('aboutBtn');
const aboutModal = document.getElementById('aboutModal');
const closeAboutModalBtn = document.getElementById('closeAboutModalBtn');
const aboutCloseBtn = document.getElementById('aboutCloseBtn');
const environmentBanner = document.getElementById('environmentBanner');
const environmentTitle = document.getElementById('environmentTitle');
const environmentDetail = document.getElementById('environmentDetail');

// iPhone Backup Elements
const iphoneDeviceName = document.getElementById('iphoneDeviceName');
const iphoneStatusBadge = document.getElementById('iphoneStatusBadge');
const iphoneDeviceDetail = document.getElementById('iphoneDeviceDetail');
const refreshIphoneBtn = document.getElementById('refreshIphoneBtn');
const iphonePlaylistsGrid = document.getElementById('iphonePlaylistsGrid');
const selectAllPlaylistsBtn = document.getElementById('selectAllPlaylistsBtn');
const deselectAllPlaylistsBtn = document.getElementById('deselectAllPlaylistsBtn');
const startIphoneExportBtn = document.getElementById('startIphoneExportBtn');
const startIphoneExportText = document.getElementById('startIphoneExportText');
const iphoneProgressPanel = document.getElementById('iphoneProgressPanel');
const iphoneProgressTitle = document.getElementById('iphoneProgressTitle');
const iphoneProgressDetail = document.getElementById('iphoneProgressDetail');
const iphoneProgressPct = document.getElementById('iphoneProgressPct');
const iphoneProgressBarFill = document.getElementById('iphoneProgressBarFill');
const iphoneProgressSpinner = document.getElementById('iphoneProgressSpinner');
const iphoneCompletionActions = document.getElementById('iphoneCompletionActions');
const iphoneCompletionMessage = document.getElementById('iphoneCompletionMessage');
const openIphoneFolderBtn = document.getElementById('openIphoneFolderBtn');
const openIphoneMusicAppBtn = document.getElementById('openIphoneMusicAppBtn');

let currentMediaType = 'audio';
let activeJobId = null;
let ytEventSource = null;
let iphoneEventSource = null;
let currentOutputDir = '';
let currentIphoneOutputDir = '';
let detectedPlaylists = [];
let selectedPlaylistNames = new Set();
let hasLoadedPlaylists = false;
let lastFetchedEntries = [];
let lastFetchedUrl = '';
let lastFetchedPlaylistTitle = '';
let diffRequestId = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupWindowDragHandler();
  setupTabs();
  setupYtEvents();
  setupIphoneEvents();
  setupAboutEvents();
  loadDefaultPaths();
  loadEnvironmentReport();
});

async function loadEnvironmentReport() {
  try {
    const res = await fetch('/api/environment');
    const report = await res.json();
    if (!environmentBanner || !report) return;
    const missing = (report.checks || []).filter(c => c.required && !c.ok);
    const platform = report.platform === 'Windows' ? 'Windows 11/Windows' : report.platform;
    if (missing.length) {
      environmentBanner.className = 'environment-banner error';
      environmentTitle.textContent = '執行環境尚未就緒';
      environmentDetail.textContent = `${platform}：${missing.map(c => `${c.label}（${c.install_hint}）`).join('；')}`;
    } else if (report.platform === 'Windows') {
      environmentBanner.className = 'environment-banner warning';
      environmentTitle.textContent = 'Windows 環境已可下載';
      environmentDetail.textContent = 'Windows 版目前不提供 Apple Music 匯入、Finder 或 iPhone 同步；這些功能已停用以避免誤導。';
    } else {
      environmentBanner.className = 'environment-banner success';
      environmentTitle.textContent = '執行環境檢查完成';
      environmentDetail.textContent = `${platform}：下載工具可用。Apple Music／Finder 功能依 macOS 權限與安裝狀態運作。`;
    }
  } catch (error) {
    if (environmentBanner) {
      environmentBanner.className = 'environment-banner error';
      environmentTitle.textContent = '無法檢查執行環境';
      environmentDetail.textContent = '請重新啟動應用程式，並確認本機伺服器可用。';
    }
  }
}

function setupAboutEvents() {
  if (!aboutBtn || !aboutModal) return;
  const close = () => aboutModal.classList.add('hidden');
  aboutBtn.addEventListener('click', () => aboutModal.classList.remove('hidden'));
  closeAboutModalBtn?.addEventListener('click', close);
  aboutCloseBtn?.addEventListener('click', close);
  aboutModal.addEventListener('click', (event) => {
    if (event.target === aboutModal) close();
  });
}

function setupWindowDragHandler() {
  document.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return; // Only primary left click

    const isInteractive = e.target.closest(
      'input, textarea, select, button, a, label, .no-drag, ' +
      '.url-input-container, .main-tabs, .segmented-control, ' +
      '.custom-select, .track-list-drawer, .dup-track-list, ' +
      '.playlists-grid, .modal-card, .toast-content'
    );

    if (!isInteractive) {
      if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.dragWindow) {
        window.webkit.messageHandlers.dragWindow.postMessage('drag');
      }
    }
  });
}

function setupTabs() {
  tabYtBtn.addEventListener('click', () => {
    tabYtBtn.classList.add('active');
    tabIphoneBtn.classList.remove('active');
    ytSection.classList.remove('hidden');
    iphoneSection.classList.add('hidden');
  });

  tabIphoneBtn.addEventListener('click', () => {
    tabIphoneBtn.classList.add('active');
    tabYtBtn.classList.remove('active');
    iphoneSection.classList.remove('hidden');
    ytSection.classList.add('hidden');
    fetchIphoneStatus();
  });

  const headerSyncBtn = document.getElementById('headerSyncBtn');
  if (headerSyncBtn) {
    headerSyncBtn.addEventListener('click', triggerIphoneSync);
  }
}

function setupYtEvents() {
  pasteBtn.addEventListener('click', async () => {
    let text = '';
    try {
      text = await navigator.clipboard.readText();
    } catch (e) {
      try {
        const res = await fetch('/api/clipboard');
        const data = await res.json();
        if (data && data.success) {
          text = data.text;
        }
      } catch (err) {
        console.error('Clipboard fetch failed:', err);
      }
    }

    if (text && text.trim()) {
      urlInput.value = text.trim();
      fetchMetadata(text.trim());
      showToast('⚡️ 已成功貼上剪貼簿內容並自動解析！', true);
    } else {
      showToast('⚠️ 剪貼簿目前沒有文字內容', false);
    }
  });

  fetchBtn.addEventListener('click', () => {
    const url = urlInput.value.trim();
    if (url) fetchMetadata(url);
    else alert('請先輸入或貼上 YouTube 網址');
  });

  urlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const url = urlInput.value.trim();
      if (url) fetchMetadata(url);
    }
    // Command+A or Ctrl+A Select All
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'a') {
      urlInput.select();
    }
  });

  urlInput.addEventListener('focus', () => {
    urlInput.select();
  });

  urlInput.addEventListener('input', () => {
    if (urlInput.value.trim() !== lastFetchedUrl) {
      lastFetchedEntries = [];
      lastFetchedUrl = '';
      lastFetchedPlaylistTitle = '';
    }
  });

  segmentBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      segmentBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentMediaType = btn.dataset.media;
      if (currentMediaType === 'audio') {
        audioOptions.classList.remove('hidden');
        videoOptions.classList.add('hidden');
        startBtnText.textContent = '開始下載並同步';
      } else {
        audioOptions.classList.add('hidden');
        videoOptions.classList.remove('hidden');
        startBtnText.textContent = '開始下載影片';
      }
    });
  });

  toggleTrackListBtn.addEventListener('click', () => {
    const isHidden = trackListDrawer.classList.toggle('hidden');
    toggleTrackListBtn.textContent = isHidden ? '檢視歌曲清單 ▾' : '收合歌曲清單 ▴';
  });

  startDownloadBtn.addEventListener('click', startDownload);

  openFolderBtn.addEventListener('click', () => {
    fetch('/api/open-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: currentOutputDir })
    });
  });

  openMusicAppBtn.addEventListener('click', () => {
    fetch('/api/open-apple-music', { method: 'POST' });
  });

  const syncIphoneDeviceBtn = document.getElementById('syncIphoneDeviceBtn');
  if (syncIphoneDeviceBtn) {
    syncIphoneDeviceBtn.addEventListener('click', triggerIphoneSync);
  }

  // Duplicate Check Modal Events
  const closeDupModalBtn = document.getElementById('closeDupModalBtn');
  const dupCancelBtn = document.getElementById('dupCancelBtn');
  const dupTabNewBtn = document.getElementById('dupTabNewBtn');
  const dupTabExistingBtn = document.getElementById('dupTabExistingBtn');
  const dupListNew = document.getElementById('dupListNew');
  const dupListExisting = document.getElementById('dupListExisting');
  const duplicateCheckModal = document.getElementById('duplicateCheckModal');

  if (closeDupModalBtn) {
    closeDupModalBtn.addEventListener('click', () => {
      duplicateCheckModal.classList.add('hidden');
    });
  }
  if (dupCancelBtn) {
    dupCancelBtn.addEventListener('click', () => {
      duplicateCheckModal.classList.add('hidden');
    });
  }

  if (dupTabNewBtn && dupTabExistingBtn) {
    dupTabNewBtn.addEventListener('click', () => {
      dupTabNewBtn.classList.add('active');
      dupTabExistingBtn.classList.remove('active');
      dupListNew.classList.remove('hidden');
      dupListExisting.classList.add('hidden');
    });

    dupTabExistingBtn.addEventListener('click', () => {
      dupTabExistingBtn.classList.add('active');
      dupTabNewBtn.classList.remove('active');
      dupListExisting.classList.remove('hidden');
      dupListNew.classList.add('hidden');
    });
  }
}

function setupIphoneEvents() {
  refreshIphoneBtn.addEventListener('click', fetchIphoneStatus);

  const scanIphoneDuplicatesBtn = document.getElementById('scanIphoneDuplicatesBtn');
  if (scanIphoneDuplicatesBtn) {
    scanIphoneDuplicatesBtn.addEventListener('click', scanIphoneDuplicates);
  }

  const cleanMacDuplicatesBtn = document.getElementById('cleanMacDuplicatesBtn');
  if (cleanMacDuplicatesBtn) {
    cleanMacDuplicatesBtn.addEventListener('click', async () => {
      cleanMacDuplicatesBtn.disabled = true;
      cleanMacDuplicatesBtn.innerHTML = '<span class="spinner-ring" style="width: 12px; height: 12px; border-width: 2px; display: inline-block; vertical-align: middle; margin-right: 4px;"></span> 正在清理...';
      showToast('正在清理 Mac「音樂」App 中的重複項目...', true);
      try {
        const res = await fetch('/api/mac/deduplicate', { method: 'POST' });
        const data = await res.json();
        cleanMacDuplicatesBtn.disabled = false;
        cleanMacDuplicatesBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
          清理 Mac 重複
        `;
        if (data && data.success) {
          showToast(`🎉 Mac 音樂 App 清理完成！共移除 ${data.removed_count} 首重複檔案 (${data.details})`, true);
          alert(`🎉 Mac 音樂 App 整理完成！\\n共移除: ${data.removed_count} 首重複項目\\n明細: ${data.details}`);
        } else {
          alert('清理失敗: ' + ((data && data.error) || '未知錯誤'));
        }
      } catch (e) {
        cleanMacDuplicatesBtn.disabled = false;
        cleanMacDuplicatesBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
          清理 Mac 重複
        `;
        alert('清理異常: ' + e.message);
      }
    });
  }

  const closeIphoneDupModalBtn = document.getElementById('closeIphoneDupModalBtn');
  const iphoneDupCancelBtn = document.getElementById('iphoneDupCancelBtn');
  const iphoneDupModal = document.getElementById('iphoneDupModal');

  if (closeIphoneDupModalBtn) {
    closeIphoneDupModalBtn.addEventListener('click', () => {
      iphoneDupModal.classList.add('hidden');
    });
  }
  if (iphoneDupCancelBtn) {
    iphoneDupCancelBtn.addEventListener('click', () => {
      iphoneDupModal.classList.add('hidden');
    });
  }

  selectAllPlaylistsBtn.addEventListener('click', () => {
    selectedPlaylistNames = new Set(detectedPlaylists.map(p => p.name));
    renderPlaylistsGrid();
    fetchDiffPreview();
  });

  deselectAllPlaylistsBtn.addEventListener('click', () => {
    selectedPlaylistNames.clear();
    renderPlaylistsGrid();
    fetchDiffPreview();
  });

  startIphoneExportBtn.addEventListener('click', startIphoneExport);

  openIphoneFolderBtn.addEventListener('click', () => {
    fetch('/api/open-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: currentIphoneOutputDir })
    });
  });

  openIphoneMusicAppBtn.addEventListener('click', () => {
    fetch('/api/open-apple-music', { method: 'POST' });
  });

  const cardSyncBtn = document.getElementById('cardSyncBtn');
  if (cardSyncBtn) {
    cardSyncBtn.addEventListener('click', triggerIphoneSync);
  }

  const syncIphoneDeviceBtn2 = document.getElementById('syncIphoneDeviceBtn2');
  if (syncIphoneDeviceBtn2) {
    syncIphoneDeviceBtn2.addEventListener('click', triggerIphoneSync);
  }

  // Direction Switchers
  const dirIphoneToMacCard = document.getElementById('dirIphoneToMacCard');
  const dirMacToIphoneCard = document.getElementById('dirMacToIphoneCard');
  if (dirIphoneToMacCard) {
    dirIphoneToMacCard.addEventListener('click', () => setSyncDirection('iphone_to_mac'));
  }
  if (dirMacToIphoneCard) {
    dirMacToIphoneCard.addEventListener('click', () => setSyncDirection('mac_to_iphone'));
  }

  // Diff Preview Actions
  const refreshDiffBtn = document.getElementById('refreshDiffBtn');
  if (refreshDiffBtn) {
    refreshDiffBtn.addEventListener('click', () => fetchDiffPreview());
  }

  const executeDiffSyncBtn = document.getElementById('executeDiffSyncBtn');
  if (executeDiffSyncBtn) {
    executeDiffSyncBtn.addEventListener('click', executeDiffSync);
  }
}

let toastTimer = null;
function showToast(message, isSuccess = true, duration = 12000) {
  let toast = document.getElementById('appToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'appToast';
    toast.className = 'app-toast';
    document.body.appendChild(toast);
  }

  if (toastTimer) clearTimeout(toastTimer);

  toast.replaceChildren();
  const content = document.createElement('div');
  content.className = `toast-content ${isSuccess ? 'success' : 'error'}`;
  const icon = document.createElement('span');
  icon.className = 'toast-icon';
  icon.textContent = isSuccess ? '⚡️' : '⚠️';
  const text = document.createElement('span');
  text.className = 'toast-text';
  text.textContent = message;
  const close = document.createElement('button');
  close.className = 'toast-close-btn';
  close.title = '關閉提示';
  close.textContent = '✕';
  close.addEventListener('click', () => toast.classList.remove('show'));
  content.append(icon, text, close);
  toast.appendChild(content);
  toast.classList.add('show');

  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, duration);
}

async function triggerIphoneSync() {
  showToast('正在開啟 Finder 同步引導...', true);
  try {
    const res = await fetch('/api/sync-iphone-device', { method: 'POST' });
    const data = await res.json();
    if (data && data.success) {
      showToast(data.message || 'Finder 已開啟，請確認同步範圍。', true);
    } else {
      showToast((data && data.error) || '無法開啟 Finder 同步引導', false);
    }
    return data;
  } catch (e) {
    showToast('開啟 Finder 同步引導失敗', false);
    return { success: false, error: e.message };
  }
}

async function loadDefaultPaths() {
  try {
    const res = await fetch('/api/default-paths');
    const data = await res.json();
    if (data) {
      if (data.default) currentOutputDir = data.default;
      if (data.iphone_export) currentIphoneOutputDir = data.iphone_export;
    }
  } catch (e) {
    console.error('Failed to load default paths:', e);
  }
}

async function fetchIphoneStatus() {
  lastIphoneStatusRefreshAt = Date.now();
  iphoneStatusBadge.className = 'badge badge-connecting';
  iphoneStatusBadge.textContent = '偵測中...';
  iphoneDeviceName.textContent = '正在讀取 iPhone 資料庫...';
  iphoneDeviceDetail.textContent = '請確認傳輸線已連接並在 iPhone 點選「信任」';
  iphonePlaylistsGrid.innerHTML = '<div class="loading-placeholder">正在讀取 iPhone 歌單資料庫...</div>';
  refreshIphoneBtn.disabled = true;

  try {
    const res = await fetch('/api/iphone/status');
    if (!res.ok) {
      throw new Error(`伺服器回應狀態碼: ${res.status}`);
    }
    const data = await res.json();

    if (data && data.connected && data.databaseReadable !== false) {
      iphoneDeviceName.textContent = data.deviceName || 'iPhone';
      iphoneStatusBadge.className = 'badge badge-connected';
      iphoneStatusBadge.textContent = '已連線';
      iphoneDeviceDetail.textContent = `型號: ${data.model} • iOS ${data.iosVersion} • 共 ${data.totalSongs || 0} 首音樂`;

      detectedPlaylists = data.playlists || [];
      const availableNames = new Set(detectedPlaylists.map(p => p.name));
      if (!hasLoadedPlaylists) {
        selectedPlaylistNames = new Set(detectedPlaylists.map(p => p.name));
        hasLoadedPlaylists = true;
      } else {
        selectedPlaylistNames = new Set(
          [...selectedPlaylistNames].filter(name => availableNames.has(name))
        );
      }
      renderPlaylistsGrid();
      startIphoneExportBtn.disabled = false;
      fetchDiffPreview();
    } else {
      const deviceIsConnectedButUnreadable = Boolean(data && data.connected && data.databaseReadable === false);
      iphoneDeviceName.textContent = deviceIsConnectedButUnreadable ? (data.deviceName || 'iPhone') : '未偵測到 iPhone';
      iphoneStatusBadge.className = 'badge badge-error';
      iphoneStatusBadge.textContent = deviceIsConnectedButUnreadable ? '已連線但無法讀取' : '未連線';
      iphoneDeviceDetail.textContent = (data && (data.message || data.error)) || '請用傳輸線接上 iPhone 並在手機解鎖點選「信任」';
      iphonePlaylistsGrid.innerHTML = '<div class="loading-placeholder">未偵測到 iPhone，請插上傳輸線後點擊「重新整理」</div>';
      startIphoneExportBtn.disabled = true;
    }
  } catch (e) {
    console.error('fetchIphoneStatus error:', e);
    iphoneDeviceName.textContent = '連線失敗';
    iphoneStatusBadge.className = 'badge badge-error';
    iphoneStatusBadge.textContent = '重試中';
    iphoneDeviceDetail.textContent = '請點擊右上角「重新整理」按鈕再次連線';
  } finally {
    refreshIphoneBtn.disabled = false;
  }
}

function renderPlaylistsGrid() {
  if (!detectedPlaylists || detectedPlaylists.length === 0) {
    iphonePlaylistsGrid.innerHTML = '<div class="loading-placeholder">iPhone 內未找到自訂播放清單</div>';
    return;
  }

  iphonePlaylistsGrid.innerHTML = detectedPlaylists.map(pl => {
    const isSelected = selectedPlaylistNames.has(pl.name);
    return `
      <div class="playlist-card-item ${isSelected ? 'selected' : ''}" data-name="${escapeHtml(pl.name)}">
        <div class="playlist-card-left">
          <label class="custom-checkbox">
            <input type="checkbox" ${isSelected ? 'checked' : ''}>
            <span class="checkmark"></span>
          </label>
          <span class="playlist-card-name">${escapeHtml(pl.name)}</span>
        </div>
        <span class="playlist-card-count">${pl.count} 首</span>
      </div>
    `;
  }).join('');

  document.querySelectorAll('.playlist-card-item').forEach(card => {
    card.addEventListener('click', () => {
      const name = card.dataset.name;
      togglePlaylistSelect(name);
    });
  });
}

function togglePlaylistSelect(name) {
  if (selectedPlaylistNames.has(name)) {
    selectedPlaylistNames.delete(name);
  } else {
    selectedPlaylistNames.add(name);
  }
  renderPlaylistsGrid();
  fetchDiffPreview();
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

async function startIphoneExport() {
  const playlistsToExport = Array.from(selectedPlaylistNames);
  if (detectedPlaylists.length > 0 && playlistsToExport.length === 0) {
    alert('請至少勾選一個欲匯出的播放清單！');
    return;
  }

  startIphoneExportBtn.disabled = true;
  startIphoneExportText.textContent = '正在備份匯出中...';
  iphoneProgressPanel.classList.remove('hidden');
  iphoneCompletionActions.classList.add('hidden');
  iphoneProgressBarFill.style.width = '0%';
  iphoneProgressPct.textContent = '0%';
  iphoneProgressSpinner.classList.remove('hidden');
  iphoneProgressTitle.textContent = '正在啟動 iPhone 備份...';
  iphoneProgressDetail.textContent = '正在讀取 iPhone 檔案庫...';

  try {
    const res = await fetch('/api/iphone/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        playlists: playlistsToExport,
        export_dir: currentIphoneOutputDir
      })
    });
    const data = await res.json();

    if (data.success && data.job_id) {
      listenToIphoneProgress(data.job_id);
    } else {
      alert(data.error || '無法啟動 iPhone 備份任務');
      resetIphoneExportUI();
    }
  } catch (err) {
    alert('備份啟動失敗: ' + err.message);
    resetIphoneExportUI();
  }
}

function listenToIphoneProgress(jobId) {
  if (iphoneEventSource) iphoneEventSource.close();

  iphoneEventSource = new EventSource(`/api/progress?job_id=${jobId}`);

  iphoneEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      updateIphoneProgressUI(data);
    } catch (e) {
      console.error('SSE error:', e);
    }
  };
}

function updateIphoneProgressUI(data) {
  if (data.progress !== undefined) {
    const pct = Math.min(Math.max(data.progress, 0), 100);
    iphoneProgressBarFill.style.width = `${pct}%`;
    iphoneProgressPct.textContent = `${Math.round(pct)}%`;
  }

  if (data.message) {
    iphoneProgressDetail.textContent = data.message;
  }

  if (data.output_dir) {
    currentIphoneOutputDir = data.output_dir;
  }

  if (data.status === 'completed') {
    if (iphoneEventSource) iphoneEventSource.close();
    iphoneProgressSpinner.classList.add('hidden');
    iphoneProgressTitle.textContent = '🎉 iPhone 音樂備份完成！';
    iphoneProgressDetail.textContent = data.message || '全部歌單與歌曲已成功匯入 Mac「音樂」App。';
    iphoneCompletionMessage.textContent = data.message || '全部歌單與歌曲已成功匯入 Mac「音樂」App！';
    iphoneCompletionActions.classList.remove('hidden');
    startIphoneExportBtn.disabled = false;
    startIphoneExportText.textContent = '一鍵完整備份至 Mac「音樂」App';
  } else if (data.status === 'error') {
    if (iphoneEventSource) iphoneEventSource.close();
    iphoneProgressSpinner.classList.add('hidden');
    iphoneProgressTitle.textContent = '❌ 備份發生錯誤';
    iphoneProgressDetail.textContent = data.message || '請確認傳輸線是否連線。';
    startIphoneExportBtn.disabled = false;
    startIphoneExportText.textContent = '重試備份';
  }
}

function resetIphoneExportUI() {
  startIphoneExportBtn.disabled = false;
  startIphoneExportText.textContent = '一鍵完整備份至 Mac「音樂」App';
  iphoneProgressSpinner.classList.add('hidden');
}

// YouTube Downloader Logic
async function fetchMetadata(url) {
  fetchBtn.disabled = true;
  fetchBtn.textContent = '解析中...';

  try {
    const res = await fetch('/api/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();

    if (data.success) {
      previewTitle.textContent = data.title;
      previewSubtitle.textContent = data.uploader || 'YouTube';
      previewCount.textContent = `共 ${data.count} 首曲目`;
      previewType.textContent = data.is_playlist ? '播放清單 / 專輯' : '單曲 / 影片';
      previewThumb.src = data.thumbnail || 'logo.png';
      previewCard.classList.remove('hidden');

      if (data.entries && data.entries.length > 0) {
        lastFetchedEntries = data.entries;
        lastFetchedUrl = url;
        lastFetchedPlaylistTitle = data.is_playlist ? (data.title || '') : '';
        trackListSummary.textContent = `共 ${data.entries.length} 首歌`;
        trackListUl.innerHTML = data.entries.map(t => `
          <li class="track-item">
            <span class="track-name">${t.index}. ${escapeHtml(t.title)}</span>
            <span class="track-author">${escapeHtml(t.uploader || '')}</span>
          </li>
        `).join('');
      } else {
        lastFetchedEntries = [{
          index: 1,
          title: data.title,
          uploader: data.uploader || ''
        }];
        lastFetchedUrl = url;
        trackListUl.innerHTML = '<li class="track-item">單曲檔案</li>';
      }
    } else {
      alert(data.error || '解析網址失敗，請確認 YouTube 連結。');
    }
  } catch (err) {
    alert('無法連接至下載伺服器: ' + err.message);
  } finally {
    fetchBtn.disabled = false;
    fetchBtn.textContent = '解析資訊';
  }
}

async function startDownload() {
  const url = urlInput.value.trim();
  if (!url) {
    alert('請輸入 YouTube 網址！');
    urlInput.focus();
    return;
  }

  // If sync to Apple Music is enabled and audio mode is selected, run duplicate check
  if (currentMediaType === 'audio' && syncAppleMusicToggle.checked) {
    startDownloadBtn.disabled = true;
    startBtnText.textContent = '🔍 比對音樂庫中...';
    try {
      const dupRes = await fetch('/api/check-duplicates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          entries: lastFetchedUrl === url ? lastFetchedEntries : [],
          playlist_name: lastFetchedUrl === url && lastFetchedPlaylistTitle === 'Kelly的KPOP音樂歌單'
            ? lastFetchedPlaylistTitle : null
        })
      });
      const dupData = await dupRes.json();
      startDownloadBtn.disabled = false;
      startBtnText.textContent = '開始下載並同步';

      if (dupData && dupData.success && dupData.existing_count > 0) {
        showDuplicateModal(url, dupData);
        return;
      }
    } catch (e) {
      console.warn('Duplicate check error, proceeding with normal download:', e);
      startDownloadBtn.disabled = false;
      startBtnText.textContent = '開始下載並同步';
    }
  }

  executeDownload({ url });
}

function showDuplicateModal(url, dupData) {
  const modal = document.getElementById('duplicateCheckModal');
  const existingCountEl = document.getElementById('dupExistingCount');
  const newCountEl = document.getElementById('dupNewCount');
  const tabNewBadge = document.getElementById('dupTabNewBadge');
  const tabExistingBadge = document.getElementById('dupTabExistingBadge');
  const ulNew = document.getElementById('dupUlNew');
  const ulExisting = document.getElementById('dupUlExisting');
  const confirmCountEl = document.getElementById('dupConfirmCount');
  const confirmNewBtn = document.getElementById('dupConfirmNewBtn');
  const forceAllBtn = document.getElementById('dupForceAllBtn');

  existingCountEl.textContent = dupData.existing_count;
  newCountEl.textContent = dupData.new_count;
  tabNewBadge.textContent = dupData.new_count;
  tabExistingBadge.textContent = dupData.existing_count;
  confirmCountEl.textContent = dupData.new_count;

  // Populate New Tracks List
  if (dupData.new_tracks && dupData.new_tracks.length > 0) {
    ulNew.innerHTML = dupData.new_tracks.map(t => `
      <li class="dup-item">
        <div class="dup-item-info">
          <span class="dup-item-title">${t.index ? t.index + '. ' : ''}${escapeHtml(t.title)}</span>
          <span class="dup-item-sub">${escapeHtml(t.uploader || '')}</span>
        </div>
        <span class="dup-item-badge new">🟢 新下載</span>
      </li>
    `).join('');
    confirmNewBtn.disabled = false;
  } else {
    ulNew.innerHTML = '<li class="dup-item"><div class="dup-item-info"><span class="dup-item-sub">所有曲目皆已存在於 Mac「音樂」App 中！</span></div></li>';
    confirmNewBtn.disabled = true;
  }

  // Populate Existing Tracks List
  if (dupData.existing_tracks && dupData.existing_tracks.length > 0) {
    ulExisting.innerHTML = dupData.existing_tracks.map(t => `
      <li class="dup-item">
        <div class="dup-item-info">
          <span class="dup-item-title">${t.index ? t.index + '. ' : ''}${escapeHtml(t.title)}</span>
          <span class="dup-item-sub">Mac 音樂 App 已有：${escapeHtml(t.matched_am_title || '')} (${escapeHtml(t.matched_am_artist || '')})</span>
        </div>
        <span class="dup-item-badge existing">⚪️ 已有 (跳過)</span>
      </li>
    `).join('');
  } else {
    ulExisting.innerHTML = '<li class="dup-item"><div class="dup-item-info"><span class="dup-item-sub">無重複曲目</span></div></li>';
  }

  // Button Action Handlers
  confirmNewBtn.onclick = () => {
    modal.classList.add('hidden');
    const newIndices = dupData.new_tracks.map(t => t.index).filter(Boolean);
    executeDownload({
      url,
      selected_indices: newIndices
    });
  };

  forceAllBtn.onclick = () => {
    modal.classList.add('hidden');
    executeDownload({ url });
  };

  modal.classList.remove('hidden');
}

async function executeDownload(customParams = {}) {
  const url = customParams.url || urlInput.value.trim();
  const payload = {
    url,
    media_type: currentMediaType,
    audio_format: audioFormatSelect.value,
    audio_quality: audioQualitySelect.value,
    video_quality: videoQualitySelect.value,
    video_format: videoFormatSelect.value,
    embed_thumbnail: embedThumbnailToggle.checked,
    embed_metadata: embedMetadataToggle.checked,
    sync_apple_music: syncAppleMusicToggle.checked,
    output_dir: outputFolderSelect.value,
    ...customParams
  };

  startDownloadBtn.disabled = true;
  startBtnText.textContent = '正在下載...';
  progressPanel.classList.remove('hidden');
  completionActions.classList.add('hidden');
  progressBarFill.style.width = '0%';
  progressPctText.textContent = '0%';
  progressSpinner.classList.remove('hidden');
  progressStatusTitle.textContent = '正在啟動下載...';
  progressStatusDetail.textContent = '正在連接 YouTube 與轉檔模組...';

  try {
    const res = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success && data.job_id) {
      activeJobId = data.job_id;
      listenToYtProgress(data.job_id);
    } else {
      alert(data.error || '無法啟動下載任務');
      resetDownloadUI();
    }
  } catch (err) {
    alert('下載啟動失敗: ' + err.message);
    resetDownloadUI();
  }
}

function listenToYtProgress(jobId) {
  if (ytEventSource) ytEventSource.close();
  ytEventSource = new EventSource(`/api/progress?job_id=${jobId}`);

  ytEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      updateYtProgressUI(data);
    } catch (e) {
      console.error('SSE error:', e);
    }
  };
}

function updateYtProgressUI(data) {
  if (data.progress !== undefined) {
    const pct = Math.min(Math.max(data.progress, 0), 100);
    progressBarFill.style.width = `${pct}%`;
    progressPctText.textContent = `${Math.round(pct)}%`;
  }

  if (data.message) progressStatusDetail.textContent = data.message;
  if (data.current_item && data.total_items) {
    statTrackCount.textContent = `${data.current_item} / ${data.total_items}`;
    progressStatusTitle.textContent = `下載中 (${data.current_item}/${data.total_items})`;
  }
  if (data.speed) statSpeed.textContent = data.speed;
  if (data.eta) statEta.textContent = data.eta;
  if (data.size) statSize.textContent = data.size;
  if (data.output_dir) currentOutputDir = data.output_dir;

  if (data.status === 'completed') {
    if (ytEventSource) ytEventSource.close();
    progressSpinner.classList.add('hidden');
    progressStatusTitle.textContent = '🎉 全部下載完成！';
    progressStatusDetail.textContent = data.message || '檔案已準備就緒。';
    completionMessage.textContent = data.message || '曲目已下載完成並匯入 Apple Music！';
    completionActions.classList.remove('hidden');
    startDownloadBtn.disabled = false;
    startBtnText.textContent = '開始下載並同步';
  } else if (data.status === 'error') {
    if (ytEventSource) ytEventSource.close();
    progressSpinner.classList.add('hidden');
    progressStatusTitle.textContent = '❌ 下載發生錯誤';
    progressStatusDetail.textContent = data.message || '請檢查網路連線或連結。';
    startDownloadBtn.disabled = false;
    startBtnText.textContent = '重試下載';
  }
}

function resetDownloadUI() {
  startDownloadBtn.disabled = false;
  startBtnText.textContent = '開始下載並同步';
  progressSpinner.classList.add('hidden');
}

async function scanIphoneDuplicates() {
  const btn = document.getElementById('scanIphoneDuplicatesBtn');
  const originalHtml = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
    檢查重複歌曲
  `;

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `
      <span class="spinner-ring" style="width: 12px; height: 12px; border-width: 2px; display: inline-block; vertical-align: middle; margin-right: 4px;"></span>
      正在比對 iPhone 歌曲...
    `;
  }
  showToast('正在讀取 iPhone 資料庫並比對全機歌曲 (約需 1~3 秒)...', true);

  const reportBanner = document.getElementById('iphoneDupReportBanner');
  const dupReportTitle = document.getElementById('dupReportTitle');
  const dupReportBadge = document.getElementById('dupReportBadge');
  const dupReportSummary = document.getElementById('dupReportSummary');
  const dupReportPlaylistDetails = document.getElementById('dupReportPlaylistDetails');
  const bannerDedupeBtn = document.getElementById('bannerDedupeBtn');
  const bannerViewDupListBtn = document.getElementById('bannerViewDupListBtn');

  if (reportBanner) {
    reportBanner.style.display = 'block';
    if (dupReportSummary) {
      dupReportSummary.innerHTML = '<span class="spinner-ring" style="width: 14px; height: 14px; border-width: 2px; display: inline-block; vertical-align: middle; margin-right: 6px;"></span> 正在從 iPhone 讀取音樂庫資料庫 (MediaLibrary.sqlitedb) 並深度比對歌曲與歌單...';
    }
  }

  try {
    const res = await fetch('/api/iphone/scan-duplicates', { method: 'POST' });
    const data = await res.json();

    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }

    if (data && data.success) {
      // 1. Update Permanent Report Banner
      if (reportBanner) {
        reportBanner.style.display = 'block';
        if (data.duplicate_groups_count > 0 || (data.playlist_breakdown && data.playlist_breakdown.some(p => p.dup_count > 0))) {
          if (dupReportTitle) dupReportTitle.textContent = '🔍 iPhone 重複歌曲檢查報告 (已完成)';
          if (dupReportBadge) {
            dupReportBadge.textContent = `⚠️ 發現 ${data.duplicate_groups_count ?? 0} 組重複歌曲`;
            dupReportBadge.style.background = 'rgba(255, 51, 102, 0.25)';
            dupReportBadge.style.color = '#FF3366';
            dupReportBadge.style.borderColor = 'rgba(255, 51, 102, 0.5)';
          }
          if (dupReportSummary) {
            dupReportSummary.innerHTML = `
              全機 <b>${data.total_songs ?? 0}</b> 首音樂中，偵測到 <b>${data.duplicate_groups_count ?? 0}</b> 組重複歌曲（共 <b>${data.duplicate_files_count ?? 0}</b> 首多餘檔案）。<br>
              各播放清單重複狀況如下，點擊右側按鈕即可一鍵去重複淨化並同步：
            `;
          }
          if (dupReportPlaylistDetails && data.playlist_breakdown) {
            dupReportPlaylistDetails.innerHTML = data.playlist_breakdown.map(p => {
              if (p.dup_count > 0) {
                return `
                  <div style="background: rgba(255, 51, 102, 0.15); border: 1px solid rgba(255, 51, 102, 0.4); padding: 6px 12px; border-radius: 8px; font-size: 12px; color: #FFF;">
                    <b>【${escapeHtml(p.name)}】</b>: 目前 ${p.total} 首 ➔ 實際只有 <span style="color:#34D399; font-weight:bold;">${p.unique} 首</span> (<span style="color:#FF3366; font-weight:bold;">含 ${p.dup_count} 首重複檔</span>)
                  </div>
                `;
              } else {
                return `
                  <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); padding: 6px 12px; border-radius: 8px; font-size: 12px; color: #94A3B8;">
                    【${escapeHtml(p.name)}】: ${p.total} 首 (無重複)
                  </div>
                `;
              }
            }).join('');
          }

          if (bannerDedupeBtn) {
            bannerDedupeBtn.onclick = () => {
              startIphoneExport();
            };
          }
          if (bannerViewDupListBtn) {
            bannerViewDupListBtn.onclick = () => {
              showIphoneDupModal(data);
            };
          }
        } else {
          if (dupReportTitle) dupReportTitle.textContent = '🎉 iPhone 音樂庫檢查完成';
          if (dupReportBadge) {
            dupReportBadge.textContent = '全機無重複';
            dupReportBadge.style.background = 'rgba(52, 211, 153, 0.2)';
            dupReportBadge.style.color = '#34D399';
            dupReportBadge.style.borderColor = 'rgba(52, 211, 153, 0.4)';
          }
          if (dupReportSummary) {
            dupReportSummary.textContent = `全機 ${data.total_songs} 首音樂資料庫相當乾淨，未發現任何重複檔案！`;
          }
          if (dupReportPlaylistDetails) dupReportPlaylistDetails.innerHTML = '';
        }
      }

      // 2. Update Playlist Grid Cards
      if (data.playlist_breakdown && data.playlist_breakdown.length > 0) {
        data.playlist_breakdown.forEach(pl => {
          const cards = document.querySelectorAll('.playlist-card-item');
          cards.forEach(card => {
            if (card.dataset.name === pl.name) {
              const countEl = card.querySelector('.playlist-card-count');
              if (countEl) {
                if (pl.dup_count > 0) {
                  countEl.innerHTML = `<span style="color:#FF3366; font-weight:bold;">${pl.total}首</span> <span style="font-size:10px; color:#FF6688; border-bottom:1px dashed #FF3366;">(含${pl.dup_count}重複 ⚠️)</span>`;
                  card.style.border = '1px solid rgba(255, 51, 102, 0.5)';
                  card.style.background = 'rgba(255, 51, 102, 0.08)';
                } else {
                  countEl.textContent = `${pl.unique}首`;
                }
              }
            }
          });
        });
      }

      // 3. Update Bottom progress panel
      const iphoneProgressPanel = document.getElementById('iphoneProgressPanel');
      const iphoneProgressTitle = document.getElementById('iphoneProgressTitle');
      const iphoneProgressDetail = document.getElementById('iphoneProgressDetail');
      const iphoneProgressPct = document.getElementById('iphoneProgressPct');
      const iphoneProgressBarFill = document.getElementById('iphoneProgressBarFill');
      const iphoneProgressSpinner = document.getElementById('iphoneProgressSpinner');

      if (iphoneProgressPanel) {
        iphoneProgressPanel.classList.remove('hidden');
        if (iphoneProgressSpinner) iphoneProgressSpinner.classList.add('hidden');
        if (iphoneProgressPct) iphoneProgressPct.textContent = '100%';
        if (iphoneProgressBarFill) iphoneProgressBarFill.style.width = '100%';
        if (iphoneProgressTitle) iphoneProgressTitle.textContent = '🔍 iPhone 重複歌曲比對完成！';
        if (iphoneProgressDetail) {
          iphoneProgressDetail.innerHTML = `全機 ${data.total_songs} 首音樂中，發現 ${data.duplicate_groups_count} 組重複歌曲 (共 ${data.duplicate_files_count} 首多餘檔案)。`;
        }
      }

      showToast(`⚡️ 檢查完成！已解析全機 ${data.total_songs ?? 0} 首音樂。`, true);
    } else {
      if (reportBanner && dupReportSummary) {
        dupReportSummary.innerHTML = `<span style="color:#FF3366;">⚠️ 讀取失敗: ${(data && (data.error || data.message)) || '無法讀取 iPhone 資料庫，請確認手機已解鎖並信任此電腦'}</span>`;
      }
      alert((data && (data.error || data.message)) || '無法掃描 iPhone 重複歌曲，請確認手機解鎖並信任此電腦。');
    }
  } catch (e) {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
    if (reportBanner && dupReportSummary) {
      dupReportSummary.innerHTML = `<span style="color:#FF3366;">⚠️ 掃描異常: ${e.message}</span>`;
    }
    alert('掃描失敗: ' + e.message);
  }
}

function showIphoneDupModal(data) {
  const modal = document.getElementById('iphoneDupModal');
  const totalCountEl = document.getElementById('iphoneDupTotalCount');
  const groupsCountEl = document.getElementById('iphoneDupGroupsCount');
  const redundantCountEl = document.getElementById('iphoneDupRedundantCount');
  const ul = document.getElementById('iphoneDupUl');
  const confirmBtn = document.getElementById('iphoneDupConfirmBtn');

  totalCountEl.textContent = data.total_songs || 0;
  groupsCountEl.textContent = data.duplicate_groups_count || 0;
  redundantCountEl.textContent = data.duplicate_files_count || 0;

  if (data.duplicates && data.duplicates.length > 0) {
    ul.innerHTML = data.duplicates.map(g => {
      const playlistStr = g.playlists && g.playlists.length > 0 ? g.playlists.join('、') : '單曲庫';
      return `
        <li class="dup-item">
          <div class="dup-item-info">
            <span class="dup-item-title">${escapeHtml(g.title)}</span>
            <span class="dup-item-sub">演出者: ${escapeHtml(g.artist || '未知的演出者')} • 出現在歌單: [${escapeHtml(playlistStr)}]</span>
          </div>
          <span class="dup-item-badge" style="background: rgba(255, 51, 102, 0.15); color: #FF3366; border: 1px solid rgba(255, 51, 102, 0.3);">
            重複 ${g.count} 次
          </span>
        </li>
      `;
    }).join('');
    confirmBtn.disabled = false;
  } else {
    ul.innerHTML = '<li class="dup-item"><div class="dup-item-info"><span class="dup-item-sub" style="font-size: 13px; color: #34D399; font-weight: 600;">🎉 檢查完成：全機 ' + (data.total_songs || 0) + ' 首音樂均無重複歌曲！</span></div></li>';
    confirmBtn.disabled = true;
  }

  confirmBtn.onclick = () => {
    modal.classList.add('hidden');
    startIphoneExport();
  };

  modal.classList.remove('hidden');
}

// Two-Way Sync Direction & Differential Sync Logic
let currentSyncDirection = 'iphone_to_mac';
let latestDiffData = null;
let lastIphoneStatusRefreshAt = 0;

// Finder performs the actual device sync outside this app. Refresh when the
// user returns from Finder so the delta panel cannot keep showing pre-sync data.
window.addEventListener('focus', () => {
  const now = Date.now();
  if (now - lastIphoneStatusRefreshAt < 5000) return;
  lastIphoneStatusRefreshAt = now;
  fetchIphoneStatus();
});

function setSyncDirection(dir) {
  currentSyncDirection = dir;
  const dirIphoneToMacCard = document.getElementById('dirIphoneToMacCard');
  const dirMacToIphoneCard = document.getElementById('dirMacToIphoneCard');
  const diffPanelTitle = document.getElementById('diffPanelTitle');
  const executeBtn = document.getElementById('executeDiffSyncBtn');

  if (dir === 'iphone_to_mac') {
    if (dirIphoneToMacCard) dirIphoneToMacCard.classList.add('active');
    if (dirMacToIphoneCard) dirMacToIphoneCard.classList.remove('active');
    if (diffPanelTitle) diffPanelTitle.textContent = '以 iPhone 為主備份至 MacBook';
    if (executeBtn) executeBtn.textContent = '⚡️ 僅同步差異部分至 Mac (極速增量)';
  } else {
    if (dirMacToIphoneCard) dirMacToIphoneCard.classList.add('active');
    if (dirIphoneToMacCard) dirIphoneToMacCard.classList.remove('active');
    if (diffPanelTitle) diffPanelTitle.textContent = '以 MacBook 為基準同步更新至 iPhone';
    if (executeBtn) executeBtn.textContent = '⚡️ 在 Finder 確認並同步至 iPhone';
  }

  fetchDiffPreview();
}

async function fetchDiffPreview() {
  const requestId = ++diffRequestId;
  latestDiffData = null;
  const diffAddCount = document.getElementById('diffAddCount');
  const diffRemoveCount = document.getElementById('diffRemoveCount');
  const diffIdenticalCount = document.getElementById('diffIdenticalCount');
  const diffSummaryText = document.getElementById('diffSummaryText');
  const refreshDiffBtn = document.getElementById('refreshDiffBtn');

  if (diffSummaryText) {
    diffSummaryText.innerHTML = '<span class="spinner-ring" style="width:12px;height:12px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px;"></span> 正在比對兩端歌曲與歌單差異...';
  }
  if (refreshDiffBtn) refreshDiffBtn.disabled = true;

  try {
    const res = await fetch('/api/sync/preview-diff', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        direction: currentSyncDirection,
        playlists: Array.from(selectedPlaylistNames)
      })
    });
    const data = await res.json();
    if (requestId !== diffRequestId) return;
    if (refreshDiffBtn) refreshDiffBtn.disabled = false;

    if (data && data.success) {
      latestDiffData = data;
      if (diffAddCount) diffAddCount.textContent = `${data.to_add_count} 首`;
      if (diffIdenticalCount) diffIdenticalCount.textContent = `${data.identical_count} 首`;

      if (data.direction === 'iphone_to_mac') {
        if (diffRemoveCount) diffRemoveCount.textContent = `${data.to_remove_count} 首`;
        if (data.to_add_count === 0) {
          diffSummaryText.innerHTML = `🎉 <b>兩端完全一致！</b>選取的歌單共有 <b>${data.identical_count}</b> 首歌曲，Mac 資料庫中已完整收錄，無須重複拷貝。`;
        } else {
          diffSummaryText.innerHTML = `兩端共有 <b>${data.identical_count}</b> 首相同歌曲（自動略過），僅需增量傳輸 <b>${data.to_add_count}</b> 首未備份歌曲至 Mac。`;
        }
      } else {
        // mac_to_iphone
        const fileDups = data.file_dup_count ?? data.to_remove_count ?? 0;
        const plDups = data.playlist_dup_count ?? 0;
        if (diffRemoveCount) diffRemoveCount.textContent = `${fileDups} 組檔案`;

        if (plDups > 0 || fileDups > 0) {
          diffSummaryText.innerHTML = `比對發現 iPhone 清單內有 <b>${plDups}</b> 個重複項目，以及 <b>${fileDups}</b> 組重複檔案。請先在 Finder 確認同步範圍。`;
        } else {
          diffSummaryText.innerHTML = `Mac 共有 <b>${data.identical_count}</b> 首乾淨歌曲，兩端資料高度一致，將更新 iPhone 歌單結構。`;
        }
      }
    } else {
      if (diffSummaryText) {
        diffSummaryText.innerHTML = `<span style="color: #FF3366;">⚠️ 比對失敗: ${(data && (data.error || data.message)) || '無法讀取 iPhone 資料庫'}</span>`;
      }
    }
  } catch (e) {
    if (requestId !== diffRequestId) return;
    if (refreshDiffBtn) refreshDiffBtn.disabled = false;
    if (diffSummaryText) {
      diffSummaryText.innerHTML = `<span style="color: #FF3366;">⚠️ 比對異常: ${e.message}</span>`;
    }
  }
}

async function executeDiffSync() {
  if (currentSyncDirection === 'iphone_to_mac') {
    // Existing songs can still be missing from a Mac playlist or have a
    // different order, so a zero file delta must not skip playlist repair.
    startIphoneExport();
  } else {
    // mac_to_iphone: Finder must perform the user-confirmed device sync.
    const executeDiffSyncBtn = document.getElementById('executeDiffSyncBtn');
    if (executeDiffSyncBtn) executeDiffSyncBtn.disabled = true;

    const iphoneProgressPanel = document.getElementById('iphoneProgressPanel');
    const iphoneProgressTitle = document.getElementById('iphoneProgressTitle');
    const iphoneProgressDetail = document.getElementById('iphoneProgressDetail');
    const iphoneProgressPct = document.getElementById('iphoneProgressPct');
    const iphoneProgressBarFill = document.getElementById('iphoneProgressBarFill');
    const iphoneProgressSpinner = document.getElementById('iphoneProgressSpinner');

    if (iphoneProgressPanel) {
      iphoneProgressPanel.classList.remove('hidden');
      if (iphoneProgressSpinner) iphoneProgressSpinner.classList.remove('hidden');
      if (iphoneProgressPct) iphoneProgressPct.textContent = '進行中';
      if (iphoneProgressBarFill) iphoneProgressBarFill.style.width = '50%';
      if (iphoneProgressTitle) iphoneProgressTitle.textContent = '⚡️ 正在以 MacBook 為基準同步更新至 iPhone...';
      if (iphoneProgressDetail) {
        iphoneProgressDetail.textContent = '正在喚醒 macOS 設備同步服務 (AMPDevicesAgent) 與「音樂」App...';
      }
      iphoneProgressPanel.scrollIntoView({ behavior: 'smooth' });
    }

    let syncSucceeded = false;
    try {
      const syncResult = await triggerIphoneSync();
      if (!syncResult || !syncResult.success) {
        if (iphoneProgressPct) iphoneProgressPct.textContent = '需確認';
        if (iphoneProgressBarFill) iphoneProgressBarFill.style.width = '0%';
        if (iphoneProgressTitle) iphoneProgressTitle.textContent = 'Finder 同步確認待完成';
        if (iphoneProgressDetail) {
          iphoneProgressDetail.textContent = syncResult?.error || '請在 Finder 確認並執行同步。';
        }
        return;
      }
      syncSucceeded = true;
    } catch (e) {
      console.error('sync error:', e);
    } finally {
      if (iphoneProgressSpinner) iphoneProgressSpinner.classList.add('hidden');
      if (!syncSucceeded) {
        if (executeDiffSyncBtn) executeDiffSyncBtn.disabled = false;
        return;
      }
      if (iphoneProgressPct) iphoneProgressPct.textContent = '100%';
      if (iphoneProgressBarFill) iphoneProgressBarFill.style.width = '100%';
      if (iphoneProgressTitle) iphoneProgressTitle.textContent = 'Finder 同步確認待完成';
      if (iphoneProgressDetail) {
        iphoneProgressDetail.textContent = '請在 Finder 的 iPhone「音樂」頁確認同步範圍後按「同步」。';
      }
      if (executeDiffSyncBtn) executeDiffSyncBtn.disabled = false;
      showToast('請在 Finder 確認並執行 iPhone 音樂同步。', false);
      setTimeout(() => {
        fetchIphoneStatus();
      }, 500);
    }
  }
}
