"""Runtime capability and dependency checks for supported desktop platforms."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


def _find_tool(name: str, bundled_dir: Path | None = None) -> str | None:
    candidates = []
    if bundled_dir:
        candidates.append(bundled_dir / name)
        if os.name == "nt":
            candidates.append(bundled_dir / f"{name}.exe")
    found = shutil.which(name)
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _find_python_tool(name: str, bundled_dir: Path | None = None) -> str | None:
    """Also check the active virtual environment used by the desktop app."""
    found = _find_tool(name, bundled_dir)
    if found:
        return found
    venv_bin = Path(sys.executable).resolve().parent
    for candidate in (venv_bin / name, venv_bin / f"{name}.exe"):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def get_environment_report(base_dir: str | None = None) -> dict:
    """Return actionable, non-sensitive checks used by the UI and launchers."""
    base = Path(base_dir or Path(__file__).resolve().parent)
    bundled_bin = base / "bin"
    system = platform.system()
    is_macos = system == "Darwin"
    is_windows = system == "Windows"
    checks = []

    for name, label in (("yt-dlp", "yt-dlp"), ("ffmpeg", "FFmpeg"), ("ffprobe", "FFprobe")):
        path = _find_tool(name, bundled_bin)
        checks.append({
            "id": name,
            "label": label,
            "ok": bool(path),
            "path": path,
            "required": True,
            "install_hint": "請將工具加入 PATH，或放入應用程式的 backend/bin 資料夾。",
        })

    python_ok = sys.version_info >= (3, 10)
    checks.append({
        "id": "python",
        "label": "Python 3.10+",
        "ok": python_ok,
        "path": sys.executable,
        "required": True,
        "install_hint": "請安裝 Python 3.10 或更新版本，並重新啟動應用程式。",
    })

    if is_windows:
        checks.extend([
            {"id": "windows_media", "label": "Windows 音樂匯入支援", "ok": False,
             "required": False, "install_hint": "Windows 版目前支援下載；Apple Music／iPhone 同步尚未提供。"},
            {"id": "pymobiledevice3", "label": "iPhone 傳輸模組", "ok": False,
             "required": False, "install_hint": "Windows 不使用 macOS 的 Finder／Apple Music 私有資料庫流程。"},
        ])
    else:
        checks.extend([
            {"id": "music_app", "label": "macOS 音樂 App", "ok": is_macos,
             "required": False, "install_hint": "需在 macOS 使用 Apple Music 匯入與 Finder 同步。"},
            {"id": "pymobiledevice3", "label": "pymobiledevice3", "ok": bool(_find_python_tool("pymobiledevice3", bundled_bin)),
             "required": False, "install_hint": "iPhone 備份功能需要安裝 pymobiledevice3。"},
        ])

    required_ok = all(item["ok"] for item in checks if item["required"])
    return {
        "success": True,
        "platform": system,
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "required_ok": required_ok,
        "checks": checks,
        "capabilities": {
            "download": required_ok,
            "apple_music_import": is_macos,
            "finder_iphone_sync": is_macos,
            "windows_supported": is_windows and required_ok,
        },
    }
