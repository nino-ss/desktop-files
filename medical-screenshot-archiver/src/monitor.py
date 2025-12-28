"""
ファイル監視モジュール
スクリーンショットフォルダの監視、新規画像ファイルの検知
"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable


class ScreenshotHandler(FileSystemEventHandler):
    """ファイルシステムイベントハンドラ"""

    def __init__(self, callback: Callable, wait_seconds: int = 5, file_types: list = None):
        self.callback = callback
        self.wait_seconds = wait_seconds
        self.file_types = file_types or ['.png', '.jpg', '.jpeg']
        self.pending_files = {}  # {filepath: timestamp}

    def on_created(self, event):
        """ファイル作成時のハンドラ"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # 対象ファイル形式チェック
        if file_path.suffix.lower() not in self.file_types:
            return

        logging.info(f"新規ファイル検知: {file_path.name}")

        # 待機リストに追加
        self.pending_files[str(file_path)] = time.time()

    def process_pending(self):
        """待機中のファイルを処理"""
        current_time = time.time()
        files_to_process = []

        for file_path, timestamp in list(self.pending_files.items()):
            if current_time - timestamp >= self.wait_seconds:
                files_to_process.append(file_path)
                del self.pending_files[file_path]

        for file_path in files_to_process:
            if Path(file_path).exists():
                logging.info(f"処理開始: {Path(file_path).name}")
                try:
                    self.callback(file_path)
                except Exception as e:
                    logging.error(f"処理エラー: {file_path}, {e}")


class FileMonitor:
    """ファイル監視クラス"""

    def __init__(self, config: dict):
        self.watch_folder = Path(config['monitor']['watch_folder']).expanduser()
        self.wait_seconds = config['monitor']['wait_seconds']
        self.file_types = config['monitor']['file_types']
        self.observer = None
        self.handler = None

        # 監視フォルダが存在しない場合は作成
        if not self.watch_folder.exists():
            logging.warning(f"監視フォルダが存在しません。作成します: {self.watch_folder}")
            self.watch_folder.mkdir(parents=True, exist_ok=True)

    def start(self, callback: Callable):
        """監視開始"""
        self.handler = ScreenshotHandler(callback, self.wait_seconds, self.file_types)
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(self.watch_folder),
            recursive=False
        )
        self.observer.start()

        logging.info(f"="*50)
        logging.info(f"監視開始: {self.watch_folder}")
        logging.info(f"待機時間: {self.wait_seconds} 秒")
        logging.info(f"対象形式: {', '.join(self.file_types)}")
        logging.info(f"="*50)

        try:
            while True:
                time.sleep(1)
                self.handler.process_pending()
        except KeyboardInterrupt:
            logging.info("キーボード割り込みを検知")
            self.stop()

    def stop(self):
        """監視停止"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        logging.info("監視停止")
