"""
画像管理モジュール
画像の保存・削除インターフェース、一時フォルダからアーカイブへの移動を提供
"""

import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class ImageManager:
    """画像管理クラス"""

    def __init__(self, config: dict):
        self.config = config
        self.temp_folder = Path(config['storage']['temp_folder']).expanduser()
        self.archive_folder = Path(config['storage']['base_folder']).expanduser() / '_archives' / 'images'

        # フォルダ作成
        self.temp_folder.mkdir(parents=True, exist_ok=True)
        self.archive_folder.mkdir(parents=True, exist_ok=True)

    def move_to_temp(self, image_path: str) -> str:
        """画像を一時フォルダに移動"""
        src = Path(image_path)

        if not src.exists():
            logging.error(f"画像ファイルが存在しません: {image_path}")
            return image_path

        dst = self.temp_folder / src.name

        # 重複回避
        counter = 1
        while dst.exists():
            dst = self.temp_folder / f"{src.stem}_{counter}{src.suffix}"
            counter += 1

        try:
            shutil.copy2(str(src), str(dst))  # copy2で移動（元ファイルも残す）
            logging.info(f"一時保存: {dst}")
            return str(dst)

        except Exception as e:
            logging.error(f"一時保存エラー: {e}")
            return image_path

    def save_to_archive(self, temp_image_path: str, record_id: int) -> str:
        """画像をアーカイブに保存"""
        src = Path(temp_image_path)

        if not src.exists():
            logging.error(f"一時画像が存在しません: {temp_image_path}")
            return ""

        # アーカイブファイル名（record_idを含む）
        dst = self.archive_folder / f"{record_id}_{src.name}"

        try:
            shutil.move(str(src), str(dst))
            logging.info(f"アーカイブ保存: {dst}")
            return str(dst)

        except Exception as e:
            logging.error(f"アーカイブ保存エラー: {e}")
            return ""

    def delete_temp_image(self, temp_image_path: str):
        """一時画像を削除"""
        path = Path(temp_image_path)

        if path.exists():
            try:
                path.unlink()
                logging.info(f"画像削除: {temp_image_path}")
            except Exception as e:
                logging.error(f"画像削除エラー: {e}")
        else:
            logging.warning(f"削除対象の画像が見つかりません: {temp_image_path}")

    def list_temp_images(self) -> List[dict]:
        """一時フォルダの画像リスト"""
        images = []

        for img_path in self.temp_folder.glob('*'):
            if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                images.append({
                    'path': str(img_path),
                    'name': img_path.name,
                    'size': img_path.stat().st_size,
                    'size_mb': round(img_path.stat().st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(img_path.stat().st_ctime).isoformat()
                })

        return sorted(images, key=lambda x: x['created'], reverse=True)

    def get_temp_folder_size(self) -> Dict[str, any]:
        """一時フォルダのサイズ情報を取得"""
        total_size = 0
        file_count = 0

        for img_path in self.temp_folder.glob('*'):
            if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                total_size += img_path.stat().st_size
                file_count += 1

        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count
        }

    def cleanup_old_temp_images(self, days: int = 7):
        """古い一時画像を削除"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        for img_path in self.temp_folder.glob('*'):
            if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                if img_path.stat().st_ctime < cutoff_time:
                    try:
                        img_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logging.error(f"古い画像削除エラー: {img_path}, {e}")

        logging.info(f"古い一時画像を削除: {deleted_count} 件")
        return deleted_count
