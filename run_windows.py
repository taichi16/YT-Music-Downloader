"""Windows 11 development launcher for the cross-platform download UI.

This launcher intentionally exposes download functionality only. Apple Music,
Finder and iPhone database operations remain disabled on Windows.
"""

from __future__ import annotations

import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "app" / "backend"))

from environment import get_environment_report  # noqa: E402
from server import start_server  # noqa: E402


def main() -> int:
    report = get_environment_report(str(ROOT / "app" / "backend"))
    print(f"平台：{report['platform']} {report['platform_release']}")
    for check in report["checks"]:
        state = "OK" if check["ok"] else "缺少"
        print(f"[{state}] {check['label']}: {check.get('path') or check['install_hint']}")
    if not report["required_ok"]:
        print("必要工具尚未完成安裝，請依上方提示修正後再啟動。")
        return 2
    if report["platform"] != "Windows":
        print("警告：此啟動器是 Windows 11 入口，目前仍可用於本機下載功能測試。")
    threading.Timer(0.8, lambda: webbrowser.open("http://127.0.0.1:4567")).start()
    start_server(4567)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
