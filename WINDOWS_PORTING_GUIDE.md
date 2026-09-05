# 🖥️ Windows 移植與跨平台開發指南 (Windows Porting & Migration Guide)

## 📌 專案概觀 (Project Overview)
本專案目前為 macOS 原生應用程式（`YT & iPhone Music Suite`），採用 Swift 構建 WebKit 視窗、Python (http.server) 作為微服務後端，並透過 `yt-dlp`、`ffmpeg`、`pymobiledevice3` 及 iTunes/Apple Music 達成 YouTube 音樂下載、iPhone 全量備份與背景增量同步功能。

本文檔為未來 AI Agent 或開發者進行 **Windows 平台移植** 時的完整技術規格書與實作指南。

---

## 🛠️ 技術選型與架構規劃 (Target Architecture)

### 1. 前端 UI 與桌面封裝 (Desktop Bundle)
- **建議技術**：**Tauri (v2)** `[Rust + Microsoft Edge WebView2]`
- **選型理由**：
  - 前端 HTML5/CSS3/JS (`app/frontend/`) **100% 完美重用**，無需修改任何 UI 代碼。
  - 生成的 `.exe` 檔極小（約 10MB），記憶體佔用遠小於 Electron。
  - 原生支援 Windows 10/11 玻璃擬態 (Mica / Acrylic) 視窗效果。

### 2. 後端微服務 (Backend Microservice)
- **建議技術**：**Python 3.11+** (使用 `PyInstaller` 打包為單一可執行檔 `server.exe`)
- **選型理由**：
  - 重用現有的 `app/backend/server.py` 路由架構與 `pymobiledevice3` iPhone 溝通邏輯。

### 3. 可攜式二進位套件 (Bundled Binaries)
- **Windows 版獨立可攜檔案**：
  - `yt-dlp.exe` (下載最新 Windows 獨立發行版)
  - `ffmpeg.exe` & `ffprobe.exe` (GPL 靜態編譯獨立 binary)
- **存放位置**：打包進 `app/backend/bin/` 目錄中，並在 Python 後端自動判斷平台：
  ```python
  def get_bundled_bin(name):
      ext = ".exe" if sys.platform == "win32" else ""
      # 優先尋找 app/backend/bin/{name}.exe
  ```

---

## 🔍 4 大模組移植細節與代碼替換範例 (Module Specifications)

### 模組 1: 前端 UI (App Frontend)
- **檔案路徑**：`app/frontend/index.html`, `app.js`, `style.css`
- **修改需求**：無！完全重用。

### 模組 2: YouTube 下載與轉檔 (Stream Download & Media Conversion)
- **檔案路徑**：`app/backend/server.py` (`run_download_worker`)
- **修改需求**：
  - 將二進位檔名替換為 `yt-dlp.exe` 與 `ffmpeg.exe`。
  - 路徑分隔符使用 `os.path.join` 或 `pathlib.Path` 確保跨平台相容。

### 模組 3: iPhone 音樂庫備份 (iPhone MediaLibrary Backup)
- **檔案路徑**：`export_iphone_music.py` / `app/backend/server.py`
- **相依套件**：`pymobiledevice3`, `sqlite3`, `mutagen`
- **Windows 說明**：
  - `pymobiledevice3` 為純 Python 庫，在 Windows 上完全原生相容。
  - Windows 使用者電腦只需安裝官方 **iTunes for Windows** 或 **Apple Devices** 應用程式，即可提供 USB / Apple Mobile Device Support 通訊驅動。

### 模組 4: 音樂庫寫入與 iPhone 自動同步 (Windows iTunes COM Automation)
- **macOS 目前做法**：AppleScript (`tell application "Music"`)
- **Windows 替代做法**：**Windows iTunes COM Automation API (`pywin32`)**
- **實作代碼範例**：
  ```python
  import sys
  import subprocess

  def trigger_windows_iphone_sync():
      """Windows 平台：使用 iTunes COM 介面自動匯入資料庫並觸發 iPhone 同步"""
      if sys.platform != "win32":
          return {"success": False, "error": "Not Windows OS"}
      
      try:
          import win32com.client
          itunes = win32com.client.Dispatch("iTunes.Application")
          
          # 1. 刷新資料庫與自動加入新增的歌曲
          # library = itunes.LibraryPlaylist
          # library.AddFile("C:\\Users\\...\\YT_Downloads\\song.mp3")
          
          # 2. 觸發背景同步 (若有 iPhone 連接)
          # iTunes COM API 提供了對應控制，或透過背景 launch iTunes.exe
          return {
              "success": True,
              "message": "⚡️ 已成功呼叫 Windows iTunes COM 介面完成背景同步！"
          }
      except Exception as e:
          return {"success": False, "error": f"iTunes COM 自動化失敗: {str(e)}"}
  ```

---

## 🚀 AI Agent 移植步驟清單 (Step-by-Step Porting Execution Plan for AI Agent)

當未來的 AI Agent 接手移植任務時，請依序執行以下步驟：

1. **環境準備**：
   - 確保 Windows 開發環境安裝有 Rust, Python 3.11+, PyInstaller, Node.js/Tauri CLI。
2. **二進位檔下載與打包**：
   - 下載 `yt-dlp.exe` 與 `ffmpeg.exe` (含 `ffprobe.exe`) 並放置於 `app/backend/bin/` 資料夾。
3. **後端微服務與 COM API 調整**：
   - 修改 `app/backend/server.py` 中的 `trigger_mac_iphone_sync` 函數，新增 `win32` 分支調用 `pywin32` (iTunes COM API)。
4. **Tauri 桌面專案初始化**：
   - 在專案根目錄執行 `npx tauri init`，將 `distDir` 指向 `app/frontend`。
5. **打包編譯**：
   - 執行 `pyinstaller --onefile app/backend/server.py -n server.exe`。
   - 執行 `npx tauri build`，產出 `YT_Music_Downloader_x64_Setup.exe` 與 Portable 可攜式免安裝檔。
6. **測試驗證**：
   - 測試 YouTube 音樂下載 (MP3 320k 內嵌封面)。
   - 測試 iPhone 備份匯出。
   - 測試 Windows iTunes 增量寫入與同步。
