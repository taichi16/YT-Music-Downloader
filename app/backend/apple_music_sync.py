import subprocess
import os
import glob
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
    escaped_paths = [p.replace('"', '\\"') for p in valid_paths]
    
    if playlist_name:
        escaped_pl = playlist_name.replace('"', '\\"')
        # Create playlist if not exists and add files
        files_array = "{" + ", ".join([f'"{p}"' for p in escaped_paths]) + "}"
        script = f'''
        tell application "Music"
            if not (exists playlist "{escaped_pl}") then
                make new user playlist with properties {{name:"{escaped_pl}"}}
            end if
            set targetPlaylist to playlist "{escaped_pl}"
            set fileList to {files_array}
            repeat with f in fileList
                try
                    add POSIX file f to targetPlaylist
                end try
            end repeat
        end tell
        '''
    else:
        files_array = "{" + ", ".join([f'"{p}"' for p in escaped_paths]) + "}"
        script = f'''
        tell application "Music"
            set fileList to {files_array}
            repeat with f in fileList
                try
                    add POSIX file f
                end try
            end repeat
        end tell
        '''

    success, out = run_applescript(script)
    if success:
        return True, f"成功匯入 {len(valid_paths)} 首曲目至 Apple Music"
    else:
        return False, f"匯入 Apple Music 失敗: {out}"

def import_folder_to_apple_music(folder_path: str, playlist_name: Optional[str] = None) -> tuple[bool, str]:
    """Scan a folder for audio files and import them all to Apple Music."""
    if not os.path.isdir(folder_path):
        return False, f"資料夾不存在: {folder_path}"
    
    audio_extensions = ("*.mp3", "*.m4a", "*.flac", "*.wav", "*.aac", "*.aiff")
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

if __name__ == "__main__":
    # Test notification
    print("Testing macOS notification...")
    send_macos_notification("YT Music Downloader", "測試通知", "通知系統正常運作")
