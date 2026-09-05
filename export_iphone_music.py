import os
import sys
import shutil
import sqlite3
import subprocess
import glob
from pathlib import Path

EXPORT_BASE_DIR = os.path.expanduser("~/Music/iPhone_Exported_Music")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_iphone_export")
PYMOBILEDEVICE = os.path.join(os.path.dirname(__file__), ".venv", "bin", "pymobiledevice3")

def sanitize(s):
    if not s:
        return "Unknown"
    return "".join([c for c in s if c not in r'/\:*?"<>|']).strip()

def export_all_with_playlists():
    print("🚀 連接 iPhone 並開始備份所有歌曲與播放清單...")
    os.makedirs(EXPORT_BASE_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    db_path = os.path.join(TEMP_DIR, "MediaLibrary.sqlitedb")
    if not os.path.exists(db_path):
        print("📋 正在讀取 iPhone 歌單資料庫 (MediaLibrary)...")
        try:
            subprocess.run([PYMOBILEDEVICE, "afc", "pull", "/iTunes_Control/iTunes/MediaLibrary.sqlitedb", db_path], check=True)
        except Exception as e:
            print(f"❌ 讀取資料庫失敗: {e}")
            return False

    music_pull_dir = os.path.join(TEMP_DIR, "Music")
    if not os.path.exists(music_pull_dir) or not os.listdir(music_pull_dir):
        print("⏳ 正在從 iPhone 複製全部音訊檔案到 Mac（請稍候約 30~60 秒）...")
        try:
            subprocess.run([PYMOBILEDEVICE, "afc", "pull", "/iTunes_Control/Music", music_pull_dir], check=True)
        except Exception as e:
            print(f"❌ 複製音訊失敗: {e}")
            return False
    else:
        print("⚡️ 偵測到本機暫存音訊檔案，直接進行快速整理...")

    # 3. Read SQLite mapping: Playlist -> Songs
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
            "pid": pid,
            "title": title or "Unknown",
            "artist": artist or "Unknown",
            "album": album or "Unknown"
        }

    # Query Playlists
    query_playlists = '''
    SELECT 
        c.container_pid,
        c.name as playlist_name,
        ci.item_pid
    FROM container c
    JOIN container_item ci ON c.container_pid = ci.container_pid
    WHERE c.distinguished_kind = 0 
      AND c.name NOT IN ('Photos Memories', '播放記錄', 'Taichi iPhone')
    ORDER BY c.name, ci.position
    '''

    playlists_map = {}
    for c_pid, pl_name, item_pid in cur.execute(query_playlists).fetchall():
        if pl_name not in playlists_map:
            playlists_map[pl_name] = []
        if item_pid in tracks_by_pid:
            playlists_map[pl_name].append(tracks_by_pid[item_pid])

    con.close()

    # 4. Scan all downloaded files
    local_files = []
    for ext in ("*.mp3", "*.m4a", "*.aac", "*.wav", "*.aif"):
        local_files.extend(glob.glob(os.path.join(music_pull_dir, "**", ext), recursive=True))

    print(f"✅ 成功解析 {len(playlists_map)} 個播放清單，找到 {len(local_files)} 首音訊檔案！")

    import mutagen
    from mutagen.easyid3 import EasyID3
    from mutagen.mp4 import MP4

    all_exported_folders = []
    for pl_name in playlists_map.keys():
        pl_dir = os.path.join(EXPORT_BASE_DIR, sanitize(pl_name))
        os.makedirs(pl_dir, exist_ok=True)
        all_exported_folders.append((pl_name, pl_dir))
        print(f"📁 建立清單【{pl_name}】...")

    total_copied = 0
    for src_path in local_files:
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
            dest_filename = f"{sanitize(artist)} - {sanitize(title)}{ext}"
        elif title:
            dest_filename = f"{sanitize(title)}{ext}"
        else:
            dest_filename = filename

        matched_any = False
        for pl_name, items in playlists_map.items():
            for it in items:
                if it["title"].strip() and (it["title"].strip().lower() == title.strip().lower() or it["title"] in title):
                    pl_dir = os.path.join(EXPORT_BASE_DIR, sanitize(pl_name))
                    target_file = os.path.join(pl_dir, dest_filename)
                    if not os.path.exists(target_file):
                        shutil.copy2(src_path, target_file)
                        total_copied += 1
                    matched_any = True
                    break

        if not matched_any:
            misc_dir = os.path.join(EXPORT_BASE_DIR, "其他歌曲")
            os.makedirs(misc_dir, exist_ok=True)
            target_file = os.path.join(misc_dir, dest_filename)
            if not os.path.exists(target_file):
                shutil.copy2(src_path, target_file)
                total_copied += 1

    # Cleanup temp
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    print(f"\n🎉 匯出完成！所有歌曲已按歌單分類存放至：\n📂 {EXPORT_BASE_DIR}")

    # 5. Import each playlist into Mac Music.app
    print("\n📥 正在自動將所有歌單與歌曲匯入 Mac 內建「音樂」App...")
    try:
        from app.backend.apple_music_sync import import_folder_to_apple_music
        for pl_name, pl_dir in all_exported_folders:
            if os.path.exists(pl_dir) and os.listdir(pl_dir):
                ok, msg = import_folder_to_apple_music(pl_dir, playlist_name=pl_name)
                print(f"  • 清單【{pl_name}】: {msg}")
    except Exception as e:
        print(f"匯入 Apple Music 提示: {e}")

    # Open Finder
    subprocess.run(["open", EXPORT_BASE_DIR])
    return True

if __name__ == "__main__":
    export_all_with_playlists()
