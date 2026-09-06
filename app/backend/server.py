import os
import sys
import json
import sqlite3
import shutil
import subprocess
import threading
import time
import queue
import re
import urllib.parse
import tempfile
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
from pathlib import Path
import hashlib

# Add paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
venv_candidates = [
    os.path.join(root_dir, ".venv", "lib", "python3.14", "site-packages"),
    os.path.join(root_dir, ".venv", "lib", "python3.13", "site-packages"),
    os.path.join(root_dir, ".venv", "lib", "python3.12", "site-packages"),
    "/Users/taichi/AI/music/.venv/lib/python3.14/site-packages"
]
for p in (backend_dir, root_dir, app_dir) + tuple(venv_candidates):
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from iphone_snapshot import pull_validated_database
from environment import get_environment_report

try:
    from backend.apple_music_sync import (
        import_folder_to_apple_music,
        import_tracks_to_apple_music,
        send_macos_notification,
        run_applescript,
        compare_tracks_with_apple_music,
        get_apple_music_library_tracks
    )
except ImportError:
    from apple_music_sync import (
        import_folder_to_apple_music,
        import_tracks_to_apple_music,
        send_macos_notification,
        run_applescript,
        compare_tracks_with_apple_music,
        get_apple_music_library_tracks
    )

try:
    from export_iphone_music import scan_iphone_duplicates_from_db
except ImportError:
    def scan_iphone_duplicates_from_db(db_path: str) -> dict:
        return {"error": "找不到 export_iphone_music 模組"}

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Music/YT_Downloads")
IPHONE_EXPORT_DIR = os.path.expanduser("~/Music/iPhone_Exported_Music")

def get_bundled_bin(name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "bin", name),
        os.path.join(os.path.dirname(base_dir), "Resources", "bin", name),
        os.path.join(os.path.dirname(base_dir), "bin", name),
        shutil.which(name),
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}"
    ]
    for c in candidates:
        if c and os.path.exists(c) and os.access(c, os.X_OK):
            return c
    return name

def get_pymobiledevice_bin():
    candidates = [
        get_bundled_bin("pymobiledevice3"),
        "/Users/taichi/AI/music/.venv/bin/pymobiledevice3",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".venv", "bin", "pymobiledevice3"),
        shutil.which("pymobiledevice3"),
        os.path.expanduser("~/.venv/bin/pymobiledevice3")
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return shutil.which("pymobiledevice3") or "pymobiledevice3"

def trigger_mac_iphone_sync():
    """Open Finder for the supported user-confirmed music sync flow.

    Direct writes to iOS MediaLibrary.sqlitedb are deliberately disabled: it is
    private implementation state and an interrupted write can corrupt the
    relationship between the library and media files.
    """
    info = get_connected_iphone_info()
    if not info.get("connected"):
        return {"success": False, "error": "未偵測到連接的 iPhone，請插上傳輸線並在手機解鎖點選「信任」"}

    try:
        subprocess.run(["open", "-a", "Finder"], check=True, timeout=5)
        return {
            "success": False,
            "requires_manual_sync": True,
            "error": "已開啟 Finder。請選取 iPhone，於「音樂」頁確認同步範圍後按「同步」。應用程式不再直接改寫 iPhone 音樂資料庫。"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_apple_music_sync_manifest():
    """Retrieve all user playlists and track counts from Mac Music.app for sync preview."""
    as_code = """
    tell application "Music"
        set res to {}
        repeat with pl in (get user playlists)
            try
                set plName to name of pl
                set trCount to count of tracks of pl
                if plName is not "Library" and trCount > 0 then
                    set end of res to (plName & ":::" & trCount)
                end if
            end try
        end repeat
        set AppleScript's text item delimiters to "|||"
        set resStr to res as text
        return resStr
    end tell
    """
    try:
        res = subprocess.run(["osascript", "-e", as_code], capture_output=True, text=True, timeout=6)
        raw = res.stdout.strip()
        playlists = []
        if raw:
            for item in raw.split("|||"):
                if ":::" in item:
                    parts = item.split(":::", 1)
                    playlists.append({
                        "name": parts[0].strip(),
                        "count": int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                    })
        return {"success": True, "playlists": playlists}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Store active download/export jobs
JOBS: Dict[str, Dict[str, Any]] = {}
JOB_QUEUES: Dict[str, list[queue.Queue]] = {}
JOBS_LOCK = threading.Lock()

def sanitize_filename(s):
    """Create a single, collision-resistant path component for exports."""
    raw = str(s or "").strip()
    cleaned = "".join(c for c in raw if c not in r'/\:*?"<>|').strip(". ")
    if not cleaned:
        cleaned = "Unknown"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"{cleaned[:100]}-{digest}"

def safe_directory(path: str | None, fallback: str) -> str:
    """Restrict app output to the user's Music or Downloads folders."""
    candidate = Path(os.path.expanduser(path or fallback)).resolve()
    allowed_roots = [
        Path(os.path.expanduser("~/Music")).resolve(),
        Path(os.path.expanduser("~/Downloads")).resolve(),
    ]
    if not any(candidate == root or root in candidate.parents for root in allowed_roots):
        raise ValueError("輸出位置必須位於使用者的 Music 或 Downloads 資料夾內")
    return str(candidate)

def broadcast_job_event(job_id: str, event_data: dict):
    with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(event_data)
        if job_id in JOB_QUEUES:
            for q in JOB_QUEUES[job_id]:
                q.put(event_data)

def request_origin_allowed(handler) -> bool:
    origin = handler.headers.get("Origin", "")
    return not origin or origin in ("http://127.0.0.1:4567", "http://localhost:4567")

def get_connected_iphone_info():
    """Detect connected iPhone and query playlists from its MediaLibrary database."""
    pybin = get_pymobiledevice_bin()
    if not os.path.exists(pybin) and not shutil.which(pybin):
        return {"connected": False, "message": "尚未安裝 iPhone 傳輸協議模組"}

    try:
        res = subprocess.run([pybin, "usbmux", "list"], capture_output=True, text=True, timeout=5)
        if not res.stdout.strip() or "UniqueDeviceID" not in res.stdout:
            return {"connected": False, "message": "未偵測到連接的 iPhone，請插上傳輸線並在手機點選「信任」"}

        devices = json.loads(res.stdout)
        usb_devices = [d for d in devices if d.get("ConnectionType") == "USB" or d.get("DeviceClass") == "iPhone"]
        if not usb_devices:
            return {"connected": False, "message": "未偵測到連接的 iPhone，請插上傳輸線並在手機點選「信任」"}

        dev = usb_devices[0]
        dev_name = dev.get("DeviceName", "iPhone")
        dev_model = dev.get("ProductType", "iPhone")
        dev_ios = dev.get("ProductVersion", "")

        # Try to pull MediaLibrary database to list playlists
        temp_dir = tempfile.mkdtemp(prefix="music_status_")
        db_path = os.path.join(temp_dir, "MediaLibrary.sqlitedb")

        playlists = []
        total_songs = 0
        try:
            pull_validated_database(pybin, db_path)
            if os.path.exists(db_path):
                con = sqlite3.connect(db_path)
                cur = con.cursor()
                query = '''
                SELECT
                    c.name as playlist_name,
                    COUNT(ci.item_pid) as track_count
                FROM container c
                LEFT JOIN container_item ci ON c.container_pid = ci.container_pid
                WHERE c.distinguished_kind = 0
                  AND c.name NOT IN ('Photos Memories', '播放記錄', 'Taichi iPhone')
                GROUP BY c.container_pid
                HAVING track_count > 0
                ORDER BY track_count DESC
                '''
                rows = cur.execute(query).fetchall()
                for name, count in rows:
                    if name:
                        playlists.append({"name": name, "count": count})
                        total_songs += count

                total_distinct = cur.execute('SELECT COUNT(*) FROM item').fetchone()[0]
                total_songs = total_distinct if total_distinct > 0 else total_songs
                con.close()
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "connected": True,
                "databaseReadable": False,
                "error": "iPhone 已連線，但無法讀取音樂資料庫。請在 iPhone 上輸入解鎖密碼，保持螢幕解鎖後重新連接。",
                "diagnostic": str(exc)
            }

        shutil.rmtree(temp_dir, ignore_errors=True)
        if not os.path.exists(db_path) and not playlists and total_songs == 0:
            return {"connected": True, "databaseReadable": False, "error": "無法驗證 iPhone 音樂資料庫"}

        return {
            "connected": True,
            "deviceName": dev_name,
            "model": dev_model,
            "iosVersion": dev_ios,
            "playlists": playlists,
            "totalSongs": total_songs
        }
    except Exception as e:
        return {"connected": False, "message": str(e)}

def run_iphone_export_worker(job_id: str, params: dict):
    """Background worker exporting all songs and playlists from iPhone."""
    pybin = get_pymobiledevice_bin()
    selected_playlists = params.get("playlists")
    temp_dir = None
    if selected_playlists == []:
        broadcast_job_event(job_id, {"status": "error", "message": "未選取任何播放清單"})
        return
    try:
        export_dir = safe_directory(params.get("export_dir"), IPHONE_EXPORT_DIR)
        os.makedirs(export_dir, exist_ok=True)
        export_dir = tempfile.mkdtemp(prefix="export_", dir=export_dir)
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"temp_pull_{job_id}")
        os.makedirs(temp_dir, exist_ok=True)
    except Exception as e:
        broadcast_job_event(job_id, {"status": "error", "progress": 0, "message": f"無法準備匯出工作：{e}"})
        return

    broadcast_job_event(job_id, {
        "status": "starting",
        "progress": 5,
        "message": "正在讀取 iPhone 歌單資料庫..."
    })

    try:
        db_path = os.path.join(temp_dir, "MediaLibrary.sqlitedb")
        pull_validated_database(pybin, db_path)

        broadcast_job_event(job_id, {
            "status": "pulling_files",
            "progress": 15,
            "message": "正在從 iPhone 複製音訊檔案至 Mac（約需 30~50 秒）..."
        })

        music_pull_dir = os.path.join(temp_dir, "Music")
        subprocess.run([pybin, "afc", "pull", "/iTunes_Control/Music", music_pull_dir], check=True)

        broadcast_job_event(job_id, {
            "status": "parsing_tags",
            "progress": 50,
            "message": "檔案複製完成！正在解析歌曲 ID3 標籤與歌單對應..."
        })

        con = sqlite3.connect(db_path)
        cur = con.cursor()
        query_tracks = '''
        SELECT
            i.item_pid,
            ie.title,
            COALESCE(ia.item_artist, 'Unknown') as artist_name,
            COALESCE(al.album, 'Unknown') as album_name
        FROM item i
        LEFT JOIN item_extra ie ON i.item_pid = ie.item_pid
        LEFT JOIN item_artist ia ON i.item_artist_pid = ia.item_artist_pid
        LEFT JOIN album al ON i.album_pid = al.album_pid
        '''
        tracks_by_pid = {}
        for pid, title, artist, album in cur.execute(query_tracks).fetchall():
            tracks_by_pid[pid] = {
                "title": title or "Unknown",
                "artist": artist or "Unknown",
                "album": album or "Unknown"
            }

        query_playlists = '''
        SELECT
            c.name as playlist_name,
            ci.item_pid
        FROM container c
        JOIN container_item ci ON c.container_pid = ci.container_pid
        WHERE c.distinguished_kind = 0
          AND c.name NOT IN ('Photos Memories', '播放記錄', 'Taichi iPhone')
        ORDER BY c.name, ci.position
        '''
        playlists_map = {}
        for pl_name, item_pid in cur.execute(query_playlists).fetchall():
            if selected_playlists is not None and pl_name not in selected_playlists:
                continue
            if pl_name not in playlists_map:
                playlists_map[pl_name] = []
            if item_pid in tracks_by_pid:
                playlists_map[pl_name].append(tracks_by_pid[item_pid])

        con.close()

        import glob
        local_files = []
        for ext in ("*.mp3", "*.m4a", "*.aac", "*.wav", "*.aif", "*.aiff"):
            local_files.extend(glob.glob(os.path.join(music_pull_dir, "**", ext), recursive=True))

        total_files = len(local_files)
        if playlists_map and total_files == 0:
            raise RuntimeError("iPhone 資料庫有播放清單，但沒有找到可對應的實體音檔")
        broadcast_job_event(job_id, {
            "status": "exporting_tracks",
            "progress": 65,
            "total_items": total_files,
            "message": f"找到共 {total_files} 首歌曲，正在依播放清單分類整理..."
        })

        import mutagen
        from mutagen.easyid3 import EasyID3
        from mutagen.mp4 import MP4

        all_exported_folders = []
        for pl_name in playlists_map.keys():
            pl_dir = os.path.join(export_dir, sanitize_filename(pl_name))
            os.makedirs(pl_dir, exist_ok=True)
            all_exported_folders.append((pl_name, pl_dir))

        matched_items = {name: set() for name in playlists_map}
        ordered_files = {name: {} for name in playlists_map}
        copied_count = 0
        for i, src_path in enumerate(local_files):
            filename = os.path.basename(src_path)
            title = ""
            artist = ""

            try:
                if src_path.lower().endswith(".mp3"):
                    audio = EasyID3(src_path)
                    title = audio.get("title", [""])[0]
                    artist = audio.get("artist", [""])[0]
                elif src_path.lower().endswith(".m4a") or src_path.lower().endswith(".mp4"):
                    audio = MP4(src_path)
                    title = audio.tags.get("\xa9nam", [""])[0] if audio.tags else ""
                    artist = audio.tags.get("\xa9ART", [""])[0] if audio.tags else ""
            except Exception:
                pass

            if not title:
                try:
                    res = subprocess.run([
                        "ffprobe", "-v", "quiet", "-show_entries",
                        "format_tags=title,artist",
                        "-of", "default=noprint_wrappers=1:nokey=0", src_path
                    ], capture_output=True, text=True)
                    for l in res.stdout.strip().split("\n"):
                        if l.startswith("TAG:title="):
                            title = l.split("=", 1)[1].strip()
                        elif l.startswith("TAG:artist="):
                            artist = l.split("=", 1)[1].strip()
                except Exception:
                    pass

            ext = os.path.splitext(src_path)[1].lower()
            if artist and title:
                dest_filename = f"{sanitize_filename(artist)} - {sanitize_filename(title)}{ext}"
            elif title:
                dest_filename = f"{sanitize_filename(title)}{ext}"
            else:
                dest_filename = filename

            matched = False
            for pl_name, items in playlists_map.items():
                for item_index, it in enumerate(items):
                    title_match = it["title"].strip().lower() == title.strip().lower()
                    artist_match = bool(artist) and it.get("artist", "").strip().casefold() == artist.strip().casefold()
                    if it["title"].strip() and title_match and artist_match:
                        pl_dir = os.path.join(export_dir, sanitize_filename(pl_name))
                        target_file = os.path.join(pl_dir, dest_filename)
                        if item_index in ordered_files[pl_name]:
                            raise RuntimeError(f"音檔對應不唯一：{pl_name} / {title}")
                        if not os.path.exists(target_file):
                            shutil.copy2(src_path, target_file)
                            copied_count += 1
                        ordered_files[pl_name][item_index] = target_file
                        matched_items[pl_name].add(item_index)
                        matched = True

            if not matched and selected_playlists is None:
                misc_dir = os.path.join(export_dir, "其他歌曲")
                os.makedirs(misc_dir, exist_ok=True)
                target_file = os.path.join(misc_dir, dest_filename)
                if not os.path.exists(target_file):
                    shutil.copy2(src_path, target_file)
                    copied_count += 1

            if i % 10 == 0:
                pct = 65 + round((i / total_files) * 20, 1)
                broadcast_job_event(job_id, {
                    "progress": pct,
                    "current_item": i + 1,
                    "total_items": total_files,
                    "message": f"整理歌曲 [{i+1}/{total_files}]: {title or filename}"
                })

        missing = {name: len(items) - len(matched_items[name])
                   for name, items in playlists_map.items()
                   if len(items) != len(matched_items[name])}
        if missing or not playlists_map:
            raise RuntimeError("播放清單音檔對應不完整，未匯入 Mac：" + json.dumps(missing, ensure_ascii=False))
        shutil.rmtree(temp_dir, ignore_errors=True)

        broadcast_job_event(job_id, {
            "status": "syncing_music",
            "progress": 90,
            "message": "正在將所有歌單自動匯入 Mac「音樂」App..."
        })

        import_failures = []
        for pl_name, pl_dir in all_exported_folders:
            if os.path.exists(pl_dir) and os.listdir(pl_dir):
                ok, msg = import_tracks_to_apple_music(
                    [ordered_files[pl_name][i] for i in sorted(ordered_files[pl_name])],
                    playlist_name=pl_name + "（iPhone 匯入 " + os.path.basename(export_dir) + "）")
                if not ok:
                    import_failures.append(f"{pl_name}: {msg}")
        if import_failures:
            raise RuntimeError("Apple Music 匯入不完整：" + "；".join(import_failures))

        send_macos_notification(
            "YT Music Downloader",
            "iPhone 音樂備份完成！",
            f"已成功匯出 {copied_count} 首歌曲並建立所有播放清單。"
        )

        broadcast_job_event(job_id, {
            "status": "completed",
            "progress": 100,
            "message": f"🎉 成功備份 {copied_count} 首歌曲與全部歌單至 Mac「音樂」App！",
            "output_dir": export_dir,
            "total_items": copied_count
        })

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        broadcast_job_event(job_id, {
            "status": "error",
            "progress": 0,
            "message": f"匯出失敗: {str(e)}"
        })

# YouTube download worker logic
def extract_metadata(url: str) -> dict:
    cmd = [get_bundled_bin("yt-dlp"), "--dump-single-json", "--flat-playlist", "--no-warnings", url]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        is_playlist = "_type" in data and data["_type"] == "playlist" or "entries" in data
        entries = []
        if is_playlist and "entries" in data and data["entries"]:
            for i, entry in enumerate(data["entries"]):
                if entry:
                    entries.append({
                        "index": i + 1,
                        "id": entry.get("id"),
                        "title": entry.get("title", f"曲目 {i+1}"),
                        "uploader": entry.get("uploader") or entry.get("channel") or "",
                        "duration": entry.get("duration")
                    })
        thumbnail = data.get("thumbnail")
        if not thumbnail and is_playlist and "thumbnails" in data and data["thumbnails"]:
            thumbnail = data["thumbnails"][-1].get("url")

        return {
            "success": True,
            "title": data.get("title", "未命名清單/影片"),
            "uploader": data.get("uploader") or data.get("channel") or "YouTube",
            "is_playlist": is_playlist,
            "count": len(entries) if is_playlist else 1,
            "thumbnail": thumbnail or "",
            "entries": entries
        }
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr.strip() or "無法解析此網址，請確認連結。"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_download_worker(job_id: str, params: dict):
    url = params.get("url")
    media_type = params.get("media_type", "audio")
    audio_format = params.get("audio_format", "mp3")
    audio_quality = params.get("audio_quality", "320k")
    video_quality = params.get("video_quality", "best")
    video_format = params.get("video_format", "mp4")
    embed_thumbnail = params.get("embed_thumbnail", True)
    embed_metadata = params.get("embed_metadata", True)
    sync_apple_music = params.get("sync_apple_music", True)
    try:
        output_dir = safe_directory(params.get("output_dir"), DEFAULT_DOWNLOAD_DIR)
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        broadcast_job_event(job_id, {"status": "error", "progress": 0, "message": f"無法準備下載工作：{e}"})
        return
    broadcast_job_event(job_id, {
        "status": "starting",
        "progress": 0,
        "message": "正在連線並解析串流資訊...",
        "output_dir": output_dir
    })

    cmd = [get_bundled_bin("yt-dlp"), "--newline", "--abort-on-error",
           "--print", "after_move:FINAL_FILE:%(filepath)j", "--no-simulate",
           "--ffmpeg-location", os.path.dirname(get_bundled_bin("ffmpeg"))]
    if media_type == "audio":
        cmd.extend(["-x", "--audio-format", audio_format])
        if audio_format in ["mp3", "m4a"]:
            quality_map = {"320k": "0", "256k": "2", "192k": "4", "128k": "6"}
            cmd.extend(["--audio-quality", quality_map.get(audio_quality, "0")])
    else:
        if video_quality == "2160p":
            cmd.extend(["-f", "bestvideo[height<=2160]+bestaudio/best[height<=2160]"])
        elif video_quality == "1440p":
            cmd.extend(["-f", "bestvideo[height<=1440]+bestaudio/best[height<=1440]"])
        elif video_quality == "1080p":
            cmd.extend(["-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"])
        elif video_quality == "720p":
            cmd.extend(["-f", "bestvideo[height<=720]+bestaudio/best[height<=720]"])
        else:
            cmd.extend(["-f", "bestvideo+bestaudio/best"])
        cmd.extend(["--merge-output-format", video_format])

    if embed_thumbnail:
        cmd.append("--embed-thumbnail")
    if embed_metadata:
        cmd.append("--embed-metadata")

    selected_indices = params.get("selected_indices")
    if selected_indices == []:
        broadcast_job_event(job_id, {"status": "error", "message": "未選取任何曲目"})
        return
    if selected_indices and isinstance(selected_indices, list) and len(selected_indices) > 0:
        items_str = ",".join(str(idx) for idx in selected_indices)
        cmd.extend(["--playlist-items", items_str])

    output_template = os.path.join(output_dir, "%(playlist,uploader)s/%(playlist_index&{:02d} - |)s%(title)s.%(ext)s")
    cmd.extend(["-o", output_template])
    cmd.append(url)

    total_items = 1
    current_item = 1
    playlist_folder = output_dir
    completed_files = []

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        for raw_line in process.stdout:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("FINAL_FILE:"):
                completed_path = Path(json.loads(line[len("FINAL_FILE:"):])).resolve()
                if Path(output_dir).resolve() not in completed_path.parents or not completed_path.is_file():
                    raise RuntimeError("下載輸出檔案不存在或超出指定目錄")
                if str(completed_path) not in completed_files:
                    completed_files.append(str(completed_path))

            m_items = re.search(r"Downloading (\d+) items of (\d+)", line)
            if m_items:
                total_items = int(m_items.group(2))

            m_curr = re.search(r"Downloading item (\d+) of (\d+)", line)
            if m_curr:
                current_item = int(m_curr.group(1))
                total_items = int(m_curr.group(2))
                broadcast_job_event(job_id, {
                    "current_item": current_item,
                    "total_items": total_items,
                    "message": f"正在下載第 {current_item}/{total_items} 首..."
                })

            m_dest = re.search(r"Destination: (.*)", line)
            if m_dest:
                dest_file = m_dest.group(1).strip()
                folder_cand = os.path.dirname(dest_file)
                if folder_cand and os.path.isdir(folder_cand):
                    playlist_folder = folder_cand

            m_prog = re.search(r"\[download\]\s+([\d\.]+)%\s+of\s+([^\s]+)\s+at\s+([^\s]+)\s+ETA\s+([^\s]+)", line)
            if m_prog:
                item_pct = float(m_prog.group(1))
                file_size = m_prog.group(2)
                speed = m_prog.group(3)
                eta = m_prog.group(4)
                overall_progress = round(((current_item - 1) + (item_pct / 100.0)) / total_items * 100, 1)
                broadcast_job_event(job_id, {
                    "status": "downloading",
                    "progress": min(overall_progress, 99.0),
                    "item_progress": item_pct,
                    "speed": speed,
                    "eta": eta,
                    "size": file_size,
                    "current_item": current_item,
                    "total_items": total_items,
                    "message": f"下載中 [{current_item}/{total_items}] ({item_pct}%) - 速度: {speed} - 預估剩餘: {eta}"
                })

        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"下載工具失敗，結束碼：{process.returncode}")

        if not completed_files:
            raise RuntimeError("下載工具未提供可驗證的完成音檔，已停止匯入")
        total_items = len(completed_files)
        playlist_folder = os.path.dirname(completed_files[0])
        music_sync_msg = ""
        if media_type == "audio" and sync_apple_music:
            broadcast_job_event(job_id, {
                "status": "syncing_music",
                "progress": 99.5,
                "message": "正在匯入本次下載的音檔至 Mac「音樂」資料庫..."
            })
            time.sleep(0.5)
            folder_name = os.path.basename(playlist_folder)
            success, msg = import_tracks_to_apple_music(completed_files, playlist_name=folder_name)
            if not success:
                raise RuntimeError(msg)
            music_sync_msg = msg
            sync_result = trigger_mac_iphone_sync()
            if not sync_result.get("success"):
                music_sync_msg += f"；iPhone 同步未執行：{sync_result.get('error', '未知錯誤')}"

        send_macos_notification(
            "YT Music Downloader",
            "下載與轉檔完成！",
            f"已下載 {total_items} 首曲目，並已完成處理。"
        )

        broadcast_job_event(job_id, {
            "status": "completed",
            "progress": 100,
            "message": "全部下載完成！" + (f" ({music_sync_msg})" if music_sync_msg else ""),
            "output_dir": playlist_folder,
            "total_items": total_items
        })

    except Exception as e:
        broadcast_job_event(job_id, {
            "status": "error",
            "progress": 0,
            "message": f"下載失敗: {str(e)}"
        })

class AppRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        origin = self.headers.get("Origin", "")
        if origin in ("http://127.0.0.1:4567", "http://localhost:4567"):
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        if not request_origin_allowed(self):
            self.send_response(403)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if not request_origin_allowed(self):
            self.send_response(403)
            self.end_headers()
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/default-paths":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "default": DEFAULT_DOWNLOAD_DIR,
                "iphone_export": IPHONE_EXPORT_DIR,
                "music": os.path.expanduser("~/Music"),
                "downloads": os.path.expanduser("~/Downloads")
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path == "/api/environment":
            self.send_json_response(200, get_environment_report(backend_dir))
            return

        if path == "/api/clipboard":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            try:
                clipboard_cmd = ["powershell", "-NoProfile", "-Command", "Get-Clipboard"] if os.name == "nt" else ["pbpaste"]
                res = subprocess.run(clipboard_cmd, capture_output=True, text=True, timeout=2)
                text = res.stdout.strip()
                self.wfile.write(json.dumps({"success": True, "text": text}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if path == "/api/iphone/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            info = get_connected_iphone_info()
            self.wfile.write(json.dumps(info, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/sync-manifest":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            res = get_apple_music_sync_manifest()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/progress":
            query = urllib.parse.parse_qs(parsed.query)
            job_id = query.get("job_id", [""])[0]
            if not job_id or job_id not in JOBS:
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            q = queue.Queue()
            with JOBS_LOCK:
                if job_id not in JOB_QUEUES:
                    JOB_QUEUES[job_id] = []
                JOB_QUEUES[job_id].append(q)
                initial_state = JOBS[job_id]

            self.wfile.write(f"data: {json.dumps(initial_state)}\n\n".encode("utf-8"))
            self.wfile.flush()

            try:
                while True:
                    try:
                        event = q.get(timeout=20)
                        self.wfile.write(f"data: {json.dumps(event)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        if event.get("status") in ["completed", "error"]:
                            break
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except (ConnectionResetError, BrokenPipeError):
                pass
            finally:
                with JOBS_LOCK:
                    if job_id in JOB_QUEUES and q in JOB_QUEUES[job_id]:
                        JOB_QUEUES[job_id].remove(q)
            return

        if path == "/" or path == "":
            path = "/index.html"

        static_root = Path(STATIC_DIR).resolve()
        file_path = (static_root / path.lstrip("/")).resolve()
        if static_root in file_path.parents and file_path.is_file():
            self.send_response(200)
            if str(file_path).endswith(".html"):
                self.send_header("Content-Type", "text/html; charset=utf-8")
            elif str(file_path).endswith(".css"):
                self.send_header("Content-Type", "text/css; charset=utf-8")
            elif str(file_path).endswith(".js"):
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
            elif str(file_path).endswith(".png"):
                self.send_header("Content-Type", "image/png")
            elif str(file_path).endswith(".svg"):
                self.send_header("Content-Type", "image/svg+xml")
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if not request_origin_allowed(self):
            self.send_json_response(403, {"success": False, "error": "拒絕非本機來源請求"})
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/info":
            url = payload.get("url", "").strip()
            if not url:
                self.send_json_response(400, {"success": False, "error": "請提供 YouTube 網址"})
                return
            res = extract_metadata(url)
            self.send_json_response(200 if res.get("success") else 400, res)
            return

        if path == "/api/check-duplicates":
            url = payload.get("url", "").strip()
            entries = payload.get("entries")
            if not entries and url:
                info = extract_metadata(url)
                if info.get("success"):
                    entries = info.get("entries") or [{
                        "index": 1,
                        "title": info.get("title", ""),
                        "uploader": info.get("uploader", "")
                    }]
                else:
                    self.send_json_response(400, {"success": False, "error": info.get("error", "解析失敗")})
                    return

            if not entries:
                self.send_json_response(400, {"success": False, "error": "缺乏可比對的曲目資訊"})
                return

            try:
                playlist_name = payload.get("playlist_name")
                res = compare_tracks_with_apple_music(entries, playlist_name=playlist_name)
                res["success"] = True
                self.send_json_response(200, res)
            except Exception as e:
                self.send_json_response(502, {"success": False, "error": str(e)})
            return

        if path == "/api/download":
            url = payload.get("url", "").strip()
            if not url:
                self.send_json_response(400, {"success": False, "error": "請提供 YouTube 網址"})
                return

            job_id = f"job_yt_{int(time.time() * 1000)}"
            with JOBS_LOCK:
                JOBS[job_id] = {
                    "job_id": job_id,
                    "status": "pending",
                    "progress": 0,
                    "message": "佇列中..."
                }

            t = threading.Thread(target=run_download_worker, args=(job_id, payload), daemon=True)
            t.start()
            self.send_json_response(200, {"success": True, "job_id": job_id})
            return

        if path == "/api/iphone/scan-duplicates":
            pybin = get_pymobiledevice_bin()
            temp_dir = tempfile.mkdtemp(prefix="music_status_")
            db_path = os.path.join(temp_dir, "MediaLibrary.sqlitedb")

            try:
                pull_validated_database(pybin, db_path)
                if os.path.exists(db_path):
                    from export_iphone_music import scan_iphone_duplicates_from_db
                    res = scan_iphone_duplicates_from_db(db_path)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    res["success"] = True
                    self.send_json_response(200, res)
                else:
                    self.send_json_response(400, {"success": False, "error": "無法從 iPhone 讀取音樂資料庫，請確認手機已解鎖並信任"})
            except Exception as e:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.send_json_response(500, {"success": False, "error": str(e)})
            return

        if path == "/api/mac/deduplicate":
            try:
                from apple_music_sync import deduplicate_apple_music_library
                res = deduplicate_apple_music_library()
                self.send_json_response(200, res)
            except Exception as e:
                self.send_json_response(500, {"success": False, "error": str(e)})
            return

        if path == "/api/sync/preview-diff":
            direction = payload.get("direction", "iphone_to_mac")
            selected_pls = payload.get("playlists")

            pybin = get_pymobiledevice_bin()
            temp_dir = tempfile.mkdtemp(prefix="music_diff_")
            db_path = os.path.join(temp_dir, "MediaLibrary.sqlitedb")

            try:
                pull_validated_database(pybin, db_path)
                if not os.path.exists(db_path):
                    self.send_json_response(400, {"success": False, "error": "無法讀取 iPhone 音樂資料庫；不使用舊的本機快照"})
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return

                if os.path.exists(db_path):
                    from apple_music_sync import calculate_differential_sync
                    res = calculate_differential_sync(direction, db_path, selected_pls)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    self.send_json_response(200, res)
                else:
                    self.send_json_response(400, {"success": False, "error": "無法讀取 iPhone 音樂資料庫，請確認手機已解鎖並信任此電腦"})
            except Exception as e:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.send_json_response(500, {"success": False, "error": str(e)})
            return

        if path == "/api/iphone/export":
            job_id = f"job_iphone_{int(time.time() * 1000)}"
            with JOBS_LOCK:
                JOBS[job_id] = {
                    "job_id": job_id,
                    "status": "pending",
                    "progress": 0,
                    "message": "正在準備 iPhone 備份任務..."
                }

            t = threading.Thread(target=run_iphone_export_worker, args=(job_id, payload), daemon=True)
            t.start()
            self.send_json_response(200, {"success": True, "job_id": job_id})
            return

        if path == "/api/open-folder":
            folder_path = payload.get("path", DEFAULT_DOWNLOAD_DIR)
            folder_path = os.path.expanduser(folder_path)
            if os.path.exists(folder_path):
                subprocess.run(["open", folder_path])
                self.send_json_response(200, {"success": True})
            else:
                self.send_json_response(404, {"success": False, "error": "路徑不存在"})
            return

        if path == "/api/open-apple-music":
            subprocess.run(["open", "-a", "Music"])
            self.send_json_response(200, {"success": True})
            return

        if path == "/api/sync-iphone-device":
            res = trigger_mac_iphone_sync()
            self.send_json_response(200, res)
            return

        self.send_response(404)
        self.end_headers()

    def send_json_response(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass

def start_server(port=4567):
    server = ThreadingHTTPServer(("127.0.0.1", port), AppRequestHandler)
    print(f"🎵 YT & iPhone Music Suite Server running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    port = 4567
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    start_server(port)
