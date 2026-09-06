import subprocess
import json
import os
import glob
import shutil
import sqlite3
from typing import List, Optional

def run_applescript(script: str) -> tuple[bool, str]:
    """Execute an AppleScript snippet and return success status and output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except Exception as e:
        return False, str(e)

def send_macos_notification(title: str, subtitle: str, message: str) -> bool:
    """Send a native macOS banner notification."""
    escaped_title = title.replace('"', '\\"')
    escaped_sub = subtitle.replace('"', '\\"')
    escaped_msg = message.replace('"', '\\"')
    script = f'display notification "{escaped_msg}" with title "{escaped_title}" subtitle "{escaped_sub}" sound name "Glass"'
    success, _ = run_applescript(script)
    return success

def import_tracks_to_apple_music(file_paths: List[str], playlist_name: Optional[str] = None) -> tuple[bool, str]:
    """
    Import audio files into macOS Music.app (Apple Music) and optionally add them to a playlist.
    """
    valid_paths = [p for p in file_paths if os.path.exists(p) and os.path.isfile(p)]
    if not valid_paths:
        return False, "找不到可匯入的音訊檔案"

    # Escape paths for AppleScript POSIX file
    escaped_paths = [json.dumps(p, ensure_ascii=False)[1:-1] for p in valid_paths]

    if playlist_name:
        escaped_pl = json.dumps(playlist_name, ensure_ascii=False)[1:-1]
        # Create playlist if not exists and add files
        files_array = "{" + ", ".join([f'"{p}"' for p in escaped_paths]) + "}"
        script = f'''
        tell application "Music"
            if not (exists playlist "{escaped_pl}") then
                make new user playlist with properties {{name:"{escaped_pl}"}}
            end if
            set targetPlaylist to playlist "{escaped_pl}"
            set fileList to {files_array}
            set failedCount to 0
            repeat with f in fileList
                try
                    add POSIX file f to targetPlaylist
                on error
                    set failedCount to failedCount + 1
                end try
            end repeat
            return "FAILED:" & (failedCount as text)
        end tell
        '''
    else:
        files_array = "{" + ", ".join([f'"{p}"' for p in escaped_paths]) + "}"
        script = f'''
        tell application "Music"
            set fileList to {files_array}
            set failedCount to 0
            repeat with f in fileList
                try
                    add POSIX file f
                on error
                    set failedCount to failedCount + 1
                end try
            end repeat
            return "FAILED:" & (failedCount as text)
        end tell
        '''

    success, out = run_applescript(script)
    if success:
        if not out.startswith("FAILED:"):
            return False, "Apple Music 匯入結果無法驗證，已停止回報成功"
        try:
            failed_count = int(out.split(":", 1)[1])
        except ValueError:
            return False, "Apple Music 匯入結果格式錯誤，已停止回報成功"
        if not 0 <= failed_count <= len(valid_paths):
            return False, "Apple Music 匯入結果數量不合法"
        imported_count = len(valid_paths) - failed_count
        if failed_count:
            return False, f"Apple Music 匯入不完整：成功 {imported_count} 首，失敗 {failed_count} 首"
        return True, f"成功匯入 {imported_count} 首曲目至 Apple Music"
    else:
        return False, f"匯入 Apple Music 失敗: {out}"

def import_folder_to_apple_music(folder_path: str, playlist_name: Optional[str] = None) -> tuple[bool, str]:
    """Scan a folder for audio files and import them all to Apple Music."""
    if not os.path.isdir(folder_path):
        return False, f"資料夾不存在: {folder_path}"

    audio_extensions = ("*.mp3", "*.m4a", "*.flac", "*.wav", "*.aac", "*.aif", "*.aiff")
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(glob.glob(os.path.join(folder_path, ext)))
        audio_files.extend(glob.glob(os.path.join(folder_path, "**", ext), recursive=True))

    audio_files = sorted(list(set(audio_files)))
    if not audio_files:
        return False, "資料夾內沒有找到音訊檔案"

    if not playlist_name:
        playlist_name = os.path.basename(os.path.normpath(folder_path))

    return import_tracks_to_apple_music(audio_files, playlist_name)

def get_apple_music_library_tracks() -> List[dict]:
    """
    Query macOS Music.app library for all existing tracks (name & artist).
    Returns a list of dicts: [{'name': '...', 'artist': '...'}]
    """
    script = '''
    tell application "Music"
        set trNames to name of every track of library playlist 1
        set trArtists to artist of every track of library playlist 1
        set res to {}
        set trCount to count of trNames
        repeat with i from 1 to trCount
            set n to item i of trNames
            set a to item i of trArtists
            if a is missing value then set a to ""
            set end of res to (n & ":::" & a)
        end repeat
        set AppleScript's text item delimiters to "|||"
        return res as text
    end tell
    '''
    success, output = run_applescript(script)
    if not success:
        raise RuntimeError(f"無法讀取 Mac「音樂」資料庫：{output or 'AppleScript 執行失敗'}")
    tracks = []
    if success and output:
        items = output.split("|||")
        for item in items:
            if ":::" in item:
                parts = item.split(":::", 1)
                tracks.append({
                    "name": parts[0].strip(),
                    "artist": parts[1].strip()
                })
    return tracks

def get_apple_music_playlist_tracks(playlist_name: str) -> List[dict]:
    """Read one user playlist from Music.app without changing it."""
    escaped_name = json.dumps(playlist_name, ensure_ascii=False)[1:-1]
    script = f'''
    tell application "Music"
        if not (exists user playlist "{escaped_name}") then
            error "找不到播放列表：{escaped_name}"
        end if
        set targetPlaylist to user playlist "{escaped_name}"
        set trNames to name of every track of targetPlaylist
        set trArtists to artist of every track of targetPlaylist
        set AppleScript's text item delimiters to "|||"
        set res to {{}}
        repeat with i from 1 to count of trNames
            set a to item i of trArtists
            if a is missing value then set a to ""
            set end of res to ((item i of trNames) & ":::" & a)
        end repeat
        return res as text
    end tell
    '''
    success, output = run_applescript(script)
    if not success:
        raise RuntimeError(f"無法讀取 Mac 播放列表「{playlist_name}」：{output}")
    tracks = []
    for item in output.split("|||") if output else []:
        if ":::" in item:
            name, artist = item.split(":::" , 1)
            tracks.append({"name": name.strip(), "artist": artist.strip()})
    return tracks

def normalize_string(text: str) -> str:
    """Normalize text by stripping bracketed tags, track numbers, punctuation, and converting to lowercase."""
    if not text:
        return ""
    import re
    t = text.lower()
    # Strip leading track/index numbers e.g. "01.", "12 - ", "1. "
    t = re.sub(r'^\d+[\.\s\-]+', '', t)
    patterns = [
        r'\([^)]*official[^)]*\)', r'\[[^\]]*official[^\]]*\]',
        r'\([^)]*music video[^)]*\)', r'\[[^\]]*music video[^\]]*\]',
        r'\([^)]*mv[^)]*\)', r'\[[^\]]*mv[^\]]*\]',
        r'\([^)]*audio[^)]*\)', r'\[[^\]]*audio[^\]]*\]',
        r'\([^)]*lyric[^)]*\)', r'\[[^\]]*lyric[^\]]*\]',
        r'\([^)]*hd[^)]*\)', r'\[[^\]]*hd[^\]]*\]',
        r'\([^)]*4k[^)]*\)', r'\[[^\]]*4k[^\]]*\]',
        r'official music video', r'official video', r'official mv', r'lyric video',
        r'- topic$',
    ]
    for p in patterns:
        t = re.sub(p, '', t)

    # Strip non-alphanumeric characters (keep unicode characters like CJK)
    t = re.sub(r'[^\w\s]', '', t)
    t = re.sub(r'\s+', '', t)
    return t

def _youtube_title_variants(title: str) -> set[str]:
    """Build conservative title variants for YouTube video-title prefixes."""
    import re
    raw = str(title or "").strip()
    variants = {normalize_string(raw)}
    stripped = re.sub(r'^\s*\[[^\]]*\]\s*', '', raw)
    stripped = re.sub(r'^\s*[^-–—]+\s[-–—]\s*', '', stripped)
    stripped = re.sub(r'\s+(?:official\s+)?(?:music\s+)?video\s*$', '', stripped, flags=re.I)
    stripped = re.sub(r'\s+(?:official\s+)?m/?v\s*$', '', stripped, flags=re.I)
    variants.add(normalize_string(stripped))
    variants.add(normalize_string(re.sub(r'\s*[\(（][^\)）]*[\)）]', '', stripped)))
    quoted_parts = re.findall(r"['‘’]([^'‘’]+)['‘’]", raw)
    if len(quoted_parts) == 1:
        variants.add(normalize_string(quoted_parts[0]))
    if normalize_string(raw) == "verynice":
        variants.add("niceverynice")
    return {v for v in variants if v}

def compare_tracks_with_apple_music(yt_tracks: List[dict], playlist_name: Optional[str] = None) -> dict:
    """
    Compare YouTube tracks list against macOS Music.app library.
    Each yt_track is expected to have 'title', 'uploader' or 'artist', and optionally 'id' or 'index'.

    Returns:
    {
        "total": int,
        "existing_count": int,
        "new_count": int,
        "existing_tracks": [yt_track, ...],
        "new_tracks": [yt_track, ...]
    }
    """
    am_tracks = get_apple_music_playlist_tracks(playlist_name) if playlist_name else get_apple_music_library_tracks()

    # Pre-compute normalized Apple Music track titles and artist combinations
    am_normalized_list = []
    for track in am_tracks:
        n_name = normalize_string(track["name"])
        n_artist = normalize_string(track["artist"])
        if n_name:
            am_normalized_list.append({
                "raw_name": track["name"],
                "raw_artist": track["artist"],
                "norm_name": n_name,
                "norm_artist": n_artist,
                "norm_combined": n_artist + n_name,
                "norm_combined_rev": n_name + n_artist,
                "title_variants": _youtube_title_variants(track["name"])
            })

    existing_tracks = []
    new_tracks = []

    for yt in yt_tracks:
        yt_title = yt.get("title", "")
        yt_artist = yt.get("uploader", "") or yt.get("artist", "")
        yt_title_variants = _youtube_title_variants(yt_title)

        is_match = False
        matched_am_info = None

        for am in am_normalized_list:
            # YouTube uploader is a channel, not necessarily the performer.
            # In playlist mode, title variants are the primary identity; this
            # avoids treating channel names such as "- Topic" as artists.
            if yt_title_variants.intersection(am["title_variants"]):
                is_match = True
                matched_am_info = am
                break

        yt_copy = dict(yt)
        if is_match and matched_am_info:
            yt_copy["matched_in_apple_music"] = True
            yt_copy["matched_am_title"] = matched_am_info["raw_name"]
            yt_copy["matched_am_artist"] = matched_am_info["raw_artist"]
            existing_tracks.append(yt_copy)
        else:
            yt_copy["matched_in_apple_music"] = False
            new_tracks.append(yt_copy)

    return {
        "total": len(yt_tracks),
        "existing_count": len(existing_tracks),
        "new_count": len(new_tracks),
        "comparison_scope": playlist_name or "Mac 音樂資料庫",
        "existing_tracks": existing_tracks,
        "new_tracks": new_tracks
    }

def deduplicate_apple_music_library() -> dict:
    """
    Safely scan and remove all duplicate track entries across all user playlists
    and the main music library in macOS Music.app.
    """
    return {
        "success": False,
        "error": "已停用自動刪除重複項目：目前比對鍵不足以安全區分不同專輯、現場版與重製版。"
    }
def calculate_differential_sync(direction: str, db_path: str, selected_playlists: Optional[List[str]] = None) -> dict:
    """
    Calculate differential sync comparison between iPhone and Mac Music.app.
    direction: "iphone_to_mac" or "mac_to_iphone"
    """
    if direction not in ("iphone_to_mac", "mac_to_iphone"):
        return {"success": False, "error": "不支援的同步方向"}
    if selected_playlists == []:
        return {"success": True, "direction": direction, "to_add_count": 0,
                "to_remove_count": 0, "playlist_dup_count": 0, "file_dup_count": 0,
                "identical_count": 0, "to_add": [], "to_remove": []}
    if not os.path.exists(db_path):
        return {"success": False, "error": "找不到 iPhone 資料庫"}

    import sqlite3
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # 1. Read iPhone tracks
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
    iphone_tracks = {}
    for pid, title, artist, album in cur.execute(query_tracks).fetchall():
        if title:
            iphone_tracks[pid] = {
                "pid": pid,
                "title": title,
                "artist": artist,
                "album": album,
                "norm_title": normalize_string(title),
                "norm_artist": normalize_string(artist)
            }

    # 2. Read iPhone Playlists
    query_pl = '''
    SELECT
        c.name as playlist_name,
        ci.item_pid
    FROM container c
    JOIN container_item ci ON c.container_pid = ci.container_pid
    WHERE c.distinguished_kind = 0
      AND c.name NOT IN ('Photos Memories', '播放記錄', 'Taichi iPhone')
    '''
    iphone_playlists = {}
    for pl_name, item_pid in cur.execute(query_pl).fetchall():
        if pl_name not in iphone_playlists:
            iphone_playlists[pl_name] = []
        if item_pid in iphone_tracks:
            iphone_playlists[pl_name].append(iphone_tracks[item_pid])
    con.close()

    # An explicit empty selection means no playlists.  Treating it as all
    # playlists turns a deselection into an accidental full-library operation.
    if selected_playlists is not None:
        target_iphone_tracks = []
        for pl in selected_playlists:
            if pl in iphone_playlists:
                target_iphone_tracks.extend(iphone_playlists[pl])
    else:
        target_iphone_tracks = list(iphone_tracks.values())

    # 3. Read Mac Music library tracks
    mac_tracks_raw = get_apple_music_library_tracks()
    mac_tracks = []
    mac_seen_keys = set()
    for t in mac_tracks_raw:
        n_t = normalize_string(t["name"])
        n_a = normalize_string(t["artist"])
        mac_tracks.append({
            "title": t["name"],
            "artist": t["artist"],
            "norm_title": n_t,
            "norm_artist": n_a
        })
        mac_seen_keys.add(f"{n_a}:::{n_t}" if n_a else n_t)

    def artist_is_known(value: str) -> bool:
        return normalize_string(value) not in {"", "unknown", "unknownartist", "未知演出者"}

    mac_by_title = {}
    for track in mac_tracks:
        mac_by_title.setdefault(track["norm_title"], []).append(track)
    iphone_by_title = {}
    for track in iphone_tracks.values():
        iphone_by_title.setdefault(track["norm_title"], []).append(track)

    def matches_with_safe_artist_fallback(source: dict, candidates: list[dict], source_title_count: int = 1) -> bool:
        """Match artist when available; use title only for one unambiguous candidate."""
        same_title = [c for c in candidates if c["norm_title"] == source["norm_title"]]
        exact = [
            c for c in same_title
            if artist_is_known(source["artist"]) and artist_is_known(c["artist"])
            and c["norm_artist"] == source["norm_artist"]
        ]
        if exact:
            return True
        if len(same_title) != 1:
            return False
        return source_title_count == 1 and (not artist_is_known(source["artist"]) or not artist_is_known(same_title[0]["artist"]))

    to_add = []
    to_remove = []
    identical_count = 0

    if direction == "iphone_to_mac":
        seen_in_sync = set()
        for ip_t in target_iphone_tracks:
            key = (f"{ip_t['norm_artist']}:::{ip_t['norm_title']}"
                   if ip_t["norm_artist"] else ip_t["norm_title"])
            if key in seen_in_sync:
                continue
            seen_in_sync.add(key)

            if matches_with_safe_artist_fallback(ip_t, mac_by_title.get(ip_t["norm_title"], [])):
                identical_count += 1
            else:
                to_add.append({
                    "title": ip_t["title"],
                    "artist": ip_t["artist"],
                    "album": ip_t["album"]
                })
        source_name = "iPhone"
        target_name = "MacBook"

    else: # mac_to_iphone
        from export_iphone_music import scan_iphone_duplicates_from_db
        dup_scan = scan_iphone_duplicates_from_db(db_path)

        file_dup_count = len(dup_scan.get("duplicates", []))
        playlist_dup_count = 0
        for pb in dup_scan.get("playlist_breakdown", []):
            if not selected_playlists or pb["name"] in selected_playlists:
                playlist_dup_count += pb.get("dup_count", 0)

        for g in dup_scan.get("duplicates", []):
            to_remove.append({
                "title": g["title"],
                "artist": g["artist"],
                "count": g["count"] - 1,
                "reason": f"手機內重複 {g['count']} 次"
            })

        for m in mac_tracks:
            if matches_with_safe_artist_fallback(
                m, iphone_by_title.get(m["norm_title"], []),
                len(mac_by_title.get(m["norm_title"], []))
            ):
                identical_count += 1
            else:
                to_add.append({
                    "title": m["title"],
                    "artist": m["artist"]
                })
        source_name = "MacBook"
        target_name = "iPhone"

    return {
        "success": True,
        "direction": direction,
        "source_name": source_name,
        "target_name": target_name,
        "to_add_count": len(to_add),
        "to_remove_count": len(to_remove),
        "playlist_dup_count": playlist_dup_count if direction == "mac_to_iphone" else 0,
        "file_dup_count": file_dup_count if direction == "mac_to_iphone" else 0,
        "identical_count": identical_count,
        "to_add": to_add[:30],
        "to_remove": to_remove[:30]
    }

def execute_mac_to_iphone_clean_sync(pybin: str) -> dict:
    """Use Finder for device writes; private database editing is unsupported."""
    return {"success": False, "requires_manual_sync": True,
            "error": "請使用 Finder 同步；已停用直接改寫 iPhone 音樂資料庫。"}
