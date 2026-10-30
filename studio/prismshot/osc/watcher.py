# SPDX-License-Identifier: Apache-2.0
"""写真フォルダに増えたファイルを通知する。"""

from __future__ import annotations

from pathlib import Path


class PhotoWatcher:
    """フォルダが無い、または監視を開始できないときも例外で落とさない。"""

    def __init__(self, directory: Path, callback) -> None:
        self.directory = directory
        self._callback = callback
        self._observer = None

    def start(self) -> bool:
        """監視を開始する。始められなければ False。"""
        if not self.directory.is_dir():
            return False
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except Exception:
            return False
        owner = self

        class Handler(FileSystemEventHandler):
            """作成と移動完了だけを画面へ渡す。"""

            def on_created(self, event) -> None:
                if event.is_directory:
                    return
                owner._callback(Path(event.src_path))

            def on_moved(self, event) -> None:
                if event.is_directory:
                    return
                owner._callback(Path(event.dest_path))

        try:
            observer = Observer()
            # 日付フォルダに保存される写真も拾う。
            observer.schedule(Handler(), str(self.directory), recursive=True)
            observer.start()
        except Exception:
            return False
        self._observer = observer
        return True

    def stop(self) -> None:
        """監視スレッドを止める。"""
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join(timeout=2)
        self._observer = None
