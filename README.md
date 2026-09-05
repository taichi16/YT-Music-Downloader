# YT Music Downloader & iPhone Music Suite (macOS)

![macOS 11.0+](https://img.shields.io/badge/macOS-11.0%2B-blue?logo=apple)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-v2.0.0--Portable-cyber)

這是一款專為 **macOS** 設計的高顏值玻璃擬態原生應用程式，結合了 **YouTube 音樂/歌單極速下載**、**iPhone 音樂資料庫完整備份**、**自動匯入 Mac 音樂 (Apple Music)**，以及 **背景一鍵智慧增量同步至 iPhone** 功能。

---

## 🌟 軟體主要功能

1. **YouTube & YT Music 極速下載**：
   - 支援單一影片或完整播放清單下載。
   - 內建 MP3 (320kbps)、M4A、FLAC、WAV 及 MP4 影片格式選擇。
   - 自動內嵌高畫質專輯封面圖案與完整的 ID3 歌曲標籤。

2. **iPhone 音樂資料庫全量備份與分類**：
   - 直接連結 iPhone（支援 USB 與 Wi‑Fi 傳輸）。
   - 自動解析 iPhone 內建 `MediaLibrary` 資料庫，將所有歌單完整匯出至 Mac，並自動建立 Apple Music 播放清單。

3. **⚡️ 背景一鍵同步至 iPhone (Smart Incremental Sync)**：
   - 點擊 **`⚡️ 一鍵同步至 iPhone`**，背景自動比對 Mac 音樂庫與 iPhone。
   - **智慧去重與增量寫入**：只更新新下載的音樂，已存在的歌曲絕不重複複製。
   - **純背景運作**：無需手動打開或操作 Finder 視窗。

4. **歌單文字檔匯出**：
   - 下載後可自動解析並產出清晰的 `歌單清單.txt`（包含序號、歌名與演出者）。

---

## 📦 免安裝獨立可攜版 (Standalone Portable Package)

本專案提供 **完全零相依套件 (Zero-Dependency)** 的獨立免安裝打包版！打包檔中已完整內嵌所有必需元件：

- 包含獨立封裝的 **yt-dlp** 串流解析核心
- 包含獨立封裝的 **ffmpeg / ffprobe** 音訊轉檔與封面內嵌工具
- 包含獨立 **Swift 原生 UI** 與 **Python 後端**

### 🚀 如何在任何 Mac 上解壓即用：
1. 下載 [`YT_Music_Downloader_macOS_Portable.zip`](./YT_Music_Downloader_macOS_Portable.zip)。
2. 解壓縮後將 **`YT Music Downloader.app`** 拖移至「應用程式 (Applications)」資料夾。
3. **雙擊即可直接開啟使用**！無需開啟終端機，無需安裝 Homebrew、Python 或任何第三方套件！

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
