"""Read-only, validated AFC snapshots; never write to a device database."""
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import shutil


def pull_validated_database(pybin, destination):
    destination = Path(destination)
    remote = '/iTunes_Control/iTunes/MediaLibrary.sqlitedb'
    with tempfile.TemporaryDirectory(prefix='iphone_snapshot_') as working:
        captures = []
        for number in range(2):
            folder = Path(working) / str(number)
            folder.mkdir()
            db = folder / 'MediaLibrary.sqlitedb'
            subprocess.run([pybin, 'afc', 'pull', remote, str(db)], check=True,
                           capture_output=True, timeout=30)
            # AFC may report a missing file without a nonzero exit code.
            if not db.is_file() or not db.stat().st_size:
                raise RuntimeError('無法取得 iPhone 音樂資料庫')
            wal = folder / 'MediaLibrary.sqlitedb-wal'
            result = subprocess.run([pybin, 'afc', 'pull', remote + '-wal', str(wal)],
                                    capture_output=True, timeout=30)
            if result.returncode and wal.exists():
                raise RuntimeError('無法完整取得 iPhone 音樂資料庫 WAL')
            captures.append((db.read_bytes(), wal.read_bytes() if wal.exists() else None))
        if captures[0] != captures[1]:
            raise RuntimeError('iPhone 音樂資料庫正在變更，請等待同步完成再重試')
        db = Path(working) / '1' / 'MediaLibrary.sqlitedb'
        try:
            with sqlite3.connect(db) as source:
                if source.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                    raise RuntimeError('iPhone 音樂資料庫完整性檢查失敗，已停止匯出與預覽')
                dangling = source.execute('SELECT COUNT(*) FROM container_item ci LEFT JOIN item i ON ci.item_pid=i.item_pid WHERE i.item_pid IS NULL').fetchone()[0]
                if dangling:
                    raise RuntimeError(f'iPhone 清單包含 {dangling} 個無法對應的曲目，已停止處理')
                with sqlite3.connect(destination) as target:
                    source.backup(target)
        except sqlite3.Error as exc:
            raise RuntimeError('iPhone 音樂資料庫無法驗證，已停止處理') from exc
