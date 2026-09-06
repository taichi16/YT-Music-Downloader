# Windows 11 移植評估

## 可行性

YouTube／YouTube Music 解析、下載、FFmpeg 轉檔與檔案輸出可移植到 Windows 11。現有 macOS 原生外殼 `main.swift` 使用 Cocoa／WebKit，不能直接在 Windows 編譯；Windows 需要獨立啟動器（例如 Python 本機伺服器加瀏覽器，或改用 Tauri／WebView2）。

Apple Music 匯入、Finder 同步及讀取 iPhone `MediaLibrary.sqlitedb` 是 macOS／Apple 私有流程，不能視為 Windows 11 可支援功能。Windows 版應明確停用這些按鈕，不以安裝某個套件宣稱可完成 iPhone 音樂同步。

## 執行環境檢查

應用程式啟動時檢查 Python 3.10+、`yt-dlp`、`ffmpeg`、`ffprobe`。Windows 若缺少必要工具，介面會顯示缺少項目與安裝提示；這些檢查不會上傳系統資訊或個人資料。

目前檢查結果由 `GET /api/environment` 提供。Windows 的下載功能在必要工具完整時可用；Apple Music／Finder／iPhone 功能會標示為不支援。

## 尚未包含的 Windows 交付工作

Windows 版正式交付仍需建立 Windows 啟動器、簽署／打包安裝程式、在乾淨 Windows 11 虛擬機測試 PATH、權限、防毒軟體攔截、睡眠／網路中斷與長時間下載復原。這些工作完成前，不應宣稱已提供可直接安裝的 Windows 版本。
