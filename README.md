# YT Music Downloader

## About

這是一個 **macOS 原生應用程式**，結合了以下資源與技術，讓使用者能夠輕鬆下載 YouTube 音樂歌單、管理 iPhone 音樂以及同步至 macOS `Music.app`。

### 開發引用的資源
- **yt‑dlp**：用於從 YouTube 解析與下載影片與音訊。
- **ffmpeg**：負責音訊轉檔與封面嵌入。
- **Swift** (`main.swift`)：提供 macOS App 的 UI 前端，採用玻璃擬態、動態動畫與自訂字體，打造高級感介面。
- **Python** (`export_iphone_music.py`、`app/backend/server.py`)：負責與 iPhone 通訊、讀取音樂檔、產生播放清單文字檔，使用 `mutagen` 解析 MP3 ID3 標籤。
- **Homebrew**：安裝上述工具與相依套件。

### 程式功能
1. **YouTube 下載**：輸入 YouTube 播放清單 URL，即可一次性下載全部影片的 MP3，並自動加入 ID3 標籤與封面。
2. **iPhone 音樂匯出**：使用 `pymobiledevice3` 連接 iPhone，將裝置內的音樂檔匯出至 `~/Music/iPhone_Exported_Music/`，並可直接匯入 macOS `Music.app`。
3. **播放清單匯出**：將下載的播放清單自動解析為 `.txt` 文字檔，每首以 `序號. 歌名 - 演出者` 格式呈現，方便檢視與分享。
4. **同步功能**：匯出後的 MP3 會自動加入 macOS `Music.app`，可利用系統同步至其他 Apple 裝置。

## Usage
```bash
# 1. 安裝相依套件
brew install yt-dlp ffmpeg

# 2. 下載 YouTube 播放清單
python3 export_iphone_music.py "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID"

# 3. 匯出 iPhone 音樂（連接 iPhone 後）
python3 export_iphone_music.py --export-iphone
```

## Repository Structure
```
YT Music Downloader/
├─ main.swift            # Swift UI 程式入口
├─ export_iphone_music.py# 主要 Python 腳本
├─ app/
│   ├─ backend/
│   │   └─ server.py    # 後端服務，提供本機 API
│   └─ frontend/        # Web App 介面檔
├─ build_app.sh          # 編譯 Swift 程式的腳本
└─ README.md             # 本說明文件
```

## License
MIT License – 允許自由使用、修改與發行。
