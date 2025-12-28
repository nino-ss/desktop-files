"""
ユーティリティモジュール
設定管理、通知、ロギング機能を提供
"""

import logging
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class Config:
    """設定管理クラス"""

    @staticmethod
    def load(config_path: str) -> dict:
        """設定ファイルを読み込み"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config


class Notifier:
    """通知クラス"""

    def __init__(self, config: dict):
        self.enabled = config['notification']['enabled']
        self.method = config['notification']['method']

    def notify_completion(self, record_id: int, similar_resources: List[dict]):
        """処理完了通知"""
        if not self.enabled:
            return

        title = "スクリーンショット解析完了"

        if similar_resources:
            message = f"ID: {record_id}\\n類似資料が {len(similar_resources)} 件見つかりました"
        else:
            message = f"ID: {record_id}\\n新規資料として保存されました"

        self._send_notification(title, message)

    def notify_error(self, image_path: str, error: str):
        """エラー通知"""
        if not self.enabled:
            return

        title = "解析エラー"
        message = f"{Path(image_path).name}\\n{error}"

        self._send_notification(title, message)

    def notify_similar_found(self, count: int):
        """類似資料検出通知"""
        if not self.enabled:
            return

        title = "類似資料検出"
        message = f"同一キーワードの古い資料が {count} 件見つかりました"

        self._send_notification(title, message)

    def _send_notification(self, title: str, message: str):
        """macOS通知を送信"""
        if self.method == 'macos':
            try:
                subprocess.run([
                    'osascript', '-e',
                    f'display notification "{message}" with title "{title}"'
                ], check=True)
            except Exception as e:
                logging.error(f"通知送信エラー: {e}")

        # ログにも記録
        logging.info(f"通知: {title} - {message}")


def setup_logging(log_dir: str = 'logs'):
    """ロギング設定"""
    Path(log_dir).mkdir(exist_ok=True)

    log_file = Path(log_dir) / f'medscreen_{datetime.now().strftime("%Y%m%d")}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.info("="*50)
    logging.info("医療スクリーンショット自動整理システム 起動")
    logging.info("="*50)
