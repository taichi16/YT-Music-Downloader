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
let eventSource = null;
let currentOutputDir = '';
let currentIphoneOutputDir = '';
let detectedPlaylists = [];
let selectedPlaylistNames = new Set();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupYtEvents();
  setupIphoneEvents();
  loadDefaultPaths();
});

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
}

function setupYtEvents() {
  pasteBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        urlInput.value = text.trim();
        fetchMetadata(text.trim());
      }
    } catch (e) {
      alert('請直接在輸入框使用 ⌘+V 貼上網址');
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
}

function setupIphoneEvents() {
  refreshIphoneBtn.addEventListener('click', fetchIphoneStatus);

  selectAllPlaylistsBtn.addEventListener('click', () => {
    selectedPlaylistNames = new Set(detectedPlaylists.map(p => p.name));
    renderPlaylistsGrid();
  });

  deselectAllPlaylistsBtn.addEventListener('click', () => {
    selectedPlaylistNames.clear();
    renderPlaylistsGrid();
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

    if (data && data.connected) {
      iphoneDeviceName.textContent = data.deviceName || 'iPhone';
      iphoneStatusBadge.className = 'badge badge-connected';
      iphoneStatusBadge.textContent = '已連線';
      iphoneDeviceDetail.textContent = `型號: ${data.model} • iOS ${data.iosVersion} • 共 ${data.totalSongs || 0} 首音樂`;

      detectedPlaylists = data.playlists || [];
      selectedPlaylistNames = new Set(detectedPlaylists.map(p => p.name));
      renderPlaylistsGrid();
      startIphoneExportBtn.disabled = false;
    } else {
      iphoneDeviceName.textContent = '未偵測到 iPhone';
      iphoneStatusBadge.className = 'badge badge-error';
      iphoneStatusBadge.textContent = '未連線';
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
          <label class="custom-checkbox" onclick="event.stopPropagation()">
            <input type="checkbox" ${isSelected ? 'checked' : ''} onchange="togglePlaylistSelect('${escapeHtml(pl.name)}')">
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
}

function escapeHtml(str) {
  return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
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
  if (eventSource) eventSource.close();

  eventSource = new EventSource(`/api/progress?job_id=${jobId}`);

  eventSource.onmessage = (event) => {
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
    if (eventSource) eventSource.close();
    iphoneProgressSpinner.classList.add('hidden');
    iphoneProgressTitle.textContent = '🎉 iPhone 音樂備份完成！';
    iphoneProgressDetail.textContent = data.message || '全部歌單與歌曲已成功匯入 Mac「音樂」App。';
    iphoneCompletionMessage.textContent = data.message || '全部歌單與歌曲已成功匯入 Mac「音樂」App！';
    iphoneCompletionActions.classList.remove('hidden');
    startIphoneExportBtn.disabled = false;
    startIphoneExportText.textContent = '一鍵完整備份至 Mac「音樂」App';
  } else if (data.status === 'error') {
    if (eventSource) eventSource.close();
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
        trackListSummary.textContent = `共 ${data.entries.length} 首歌`;
        trackListUl.innerHTML = data.entries.map(t => `
          <li class="track-item">
            <span class="track-name">${t.index}. ${t.title}</span>
            <span class="track-author">${t.uploader || ''}</span>
          </li>
        `).join('');
      } else {
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
    output_dir: outputFolderSelect.value
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
  if (eventSource) eventSource.close();
  eventSource = new EventSource(`/api/progress?job_id=${jobId}`);

  eventSource.onmessage = (event) => {
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
    if (eventSource) eventSource.close();
    progressSpinner.classList.add('hidden');
    progressStatusTitle.textContent = '🎉 全部下載完成！';
    progressStatusDetail.textContent = data.message || '檔案已準備就緒。';
    completionMessage.textContent = data.message || '曲目已下載完成並匯入 Apple Music！';
    completionActions.classList.remove('hidden');
    startDownloadBtn.disabled = false;
    startBtnText.textContent = '開始下載並同步';
  } else if (data.status === 'error') {
    if (eventSource) eventSource.close();
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
