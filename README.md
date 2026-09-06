# YT Music Downloader & iPhone Music Suite (macOS)

![macOS 11.0+](https://img.shields.io/badge/macOS-11.0%2B-blue?logo=apple)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-v2.0.0--Portable-cyber)

這是一款專為 **macOS** 設計的原生應用程式，結合 YouTube 音樂／歌單下載、iPhone 音樂檔案備份，以及匯入 Mac「音樂」App 的功能。

---

## 🌟 軟體主要功能

1. **YouTube & YT Music 極速下載**：
   - 支援單一影片或完整播放清單下載。
   - 內建 MP3 (320kbps)、M4A、FLAC、WAV 及 MP4 影片格式選擇。
   - 自動內嵌高畫質專輯封面圖案與完整的 ID3 歌曲標籤。

2. **iPhone 音樂資料庫備份與分類**：
   - 直接連結 iPhone（支援 USB 與 Wi‑Fi 傳輸）。
   - 讀取 iPhone 音樂資料庫與音檔，依可用的中繼資料建立匯出資料夾，並可匯入 Mac「音樂」App。

3. **Finder 同步引導**：
   - 應用程式會開啟 Finder；使用者應在 iPhone 的「音樂」頁面確認同步範圍後按「同步」。
   - 為避免損壞私有 iOS 音樂資料庫，應用程式不會直接寫入 iPhone 的 `MediaLibrary.sqlitedb`。

4. **歌單文字檔匯出**：
   - 下載後可自動解析並產出清晰的 `歌單清單.txt`（包含序號、歌名與演出者）。

---

## 📦 免安裝獨立可攜版 (Standalone Portable Package)

目前打包流程會隨附部分工具，但尚未完成乾淨 macOS 環境的可攜性驗收；請先在目標 Mac 測試啟動與下載功能。

- 包含獨立封裝的 **yt-dlp** 串流解析核心
- 包含獨立封裝的 **ffmpeg / ffprobe** 音訊轉檔與封面內嵌工具
- 包含獨立 **Swift 原生 UI** 與 **Python 後端**

### 🚀 如何在任何 Mac 上解壓即用：
1. 下載 [`YT_Music_Downloader_macOS_Portable.zip`](./YT_Music_Downloader_macOS_Portable.zip)。
2. 解壓縮後將 **`YT Music Downloader.app`** 拖移至「應用程式 (Applications)」資料夾。
3. 第一次使用前，請確認應用程式可以正常啟動；若缺少依賴，請使用原始碼環境完成安裝與驗證。

---

## 🛠️ 開發引用的資源與開源技術

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**：負責從 YouTube / YouTube Music 解析與下載高品質音訊與影片。
- **[FFmpeg](https://ffmpeg.org/)**：負責音訊轉檔、合併多軌、ID3 標籤寫入與專輯封面內嵌。
- **Swift / WebKit / Cocoa**：構建玻璃擬態與動態科技風介面 (Glassmorphism & Ambient Glow)。
- **pymobiledevice3**：透過 Apple 官方 AFC 協定解析與備份 iPhone `MediaLibrary` 資料庫。
- **Python (http.server & mutagen)**：提供本機端微服務與 MP3 音訊標籤處理。

---

## 📂 專案結構 (Repository Structure)

```text
YT Music Downloader/
├─ YT Music Downloader.app/                # macOS 原生應用程式 Bundle (已內嵌 yt-dlp/ffmpeg)
├─ YT_Music_Downloader_macOS_Portable.zip  # 全自動免安裝獨立可攜版壓縮檔
├─ main.swift                              # Swift UI 進入點
├─ build_app.sh                            # 一鍵自動打包腳本 (含 binary 內嵌)
├─ export_iphone_music.py                  # iPhone 音樂備份獨立腳本
├─ app/
│   ├─ backend/
│   │   ├─ server.py                        # 後端微服務 API (連接 Apple Music & 同步)
│   │   └─ bin/                            # 內嵌之 yt-dlp & ffmpeg 可執行檔
│   └─ frontend/                           # HTML5 / CSS3 / JS 科技風 UI
└─ README.md                               # 專案說明文件
```

---

## 📜 授權條款 (License)

本專案採用 [MIT License](LICENSE) 授權發行。自由供個人學習與非商業用途使用。

### 同步驗證與復原限制（2026-09-06）

下載完成後只匯入 yt-dlp 回報且存在的本次完成檔案。iPhone 匯出使用獨立目錄，完整對應選取清單的音檔後，依原清單順序建立名稱含匯入批次的新清單；不會覆蓋原有 Mac 清單。缺檔、對應不唯一或資料庫驗證失敗時停止匯入。

讀取 iPhone 資料庫時會連續取得資料庫與 WAL，比對內容穩定性、SQLite 完整性及清單關聯。這是本機驗證，並非 iOS 官方的原子快照介面；出現錯誤時不能據此宣稱同步完成。Mac → iPhone 的最終範圍以 Finder 設定為準，App 差異預覽不是 Finder 的執行計畫。

回歸測試：在專案目錄執行 `.venv/bin/python3 tests/regression_sync.py`。測試使用隔離資料與模擬外部工具，不改寫真實音樂資料庫。此封裝仍依賴本機 Python／相關工具環境，不保證在其他 Mac 零依賴執行。

## Windows 11 移植狀態

Windows 11 可支援 YouTube／YouTube Music 解析、下載與 FFmpeg 轉檔。執行 `run_windows.bat` 會先檢查 Python 3.10+、yt-dlp、FFmpeg 與 FFprobe，缺少必要工具時直接列出安裝提示並停止啟動。Windows 版目前不支援 Apple Music 匯入、Finder 同步或 iPhone 音樂資料庫操作；介面會明確顯示此限制，不把這些功能誤報為可用。完整的 Windows 安裝程式、簽署與乾淨環境驗收仍屬後續交付工作，詳見 `WINDOWS_PORTING_GUIDE.md`。

## 關於

應用程式內的「關於」按鈕會說明使用的開發工具、基本使用方式與作者資訊。作者：**YuJhao Wang**。
