"""
メインアプリケーション
エントリーポイント、各モジュールの初期化と調整、CLIコマンドの提供
"""

import os
import sys
import logging
import click
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from utils import Config, Notifier, setup_logging
from database import Database
from analyzer import ImageAnalyzer
from privacy import PrivacyMasker
from classifier import Classifier
from similar_detector import SimilarDetector
from image_manager import ImageManager
from monitor import FileMonitor


class MedScreenArchiver:
    """メインアプリケーションクラス"""

    def __init__(self, config_path: str):
        # 設定読み込み
        self.config = Config.load(config_path)

        # ロギング設定
        setup_logging()

        # 各モジュールの初期化
        try:
            self.database = Database(self.config)
            self.analyzer = ImageAnalyzer(self.config)
            self.privacy_masker = PrivacyMasker(self.config)
            self.classifier = Classifier(self.config)
            self.similar_detector = SimilarDetector(self.database, self.config)
            self.image_manager = ImageManager(self.config)
            self.notifier = Notifier(self.config)
            self.monitor = FileMonitor(self.config)

            logging.info("モジュール初期化完了")

        except Exception as e:
            logging.error(f"初期化エラー: {e}")
            raise

    def start_monitoring(self):
        """監視を開始"""
        self.monitor.start(callback=self.process_screenshot)

    def process_screenshot(self, image_path: str):
        """スクリーンショット処理のメインフロー"""
        try:
            logging.info("="*50)
            logging.info(f"スクリーンショット処理開始: {Path(image_path).name}")
            logging.info("="*50)

            # 1. 画像を一時フォルダにコピー
            temp_image_path = self.image_manager.move_to_temp(image_path)

            # 2. 画像解析
            logging.info("ステップ 1/6: 画像解析")
            analysis_result = self.analyzer.analyze(temp_image_path)

            # 3. 個人情報マスキング
            logging.info("ステップ 2/6: 個人情報マスキング")
            masked_result = self.privacy_masker.mask(analysis_result)

            # マスキング結果の検証
            validation = self.privacy_masker.validate_masking(masked_result['full_text'])
            if not validation['is_safe']:
                logging.warning(f"マスキング警告: {validation['warnings']}")

            # 4. 分類
            logging.info("ステップ 3/6: カテゴリ分類")
            category = self.classifier.classify(masked_result)

            # 5. 類似資料検出
            logging.info("ステップ 4/6: 類似資料検出")
            similar_resources = self.similar_detector.find_similar(
                masked_result['keywords'],
                category
            )

            # 6. データ保存
            logging.info("ステップ 5/6: データベース保存")
            record_id = self.database.save(
                masked_result,
                category,
                similar_resources,
                self.classifier
            )

            # 7. 類似資料にリンク追加
            if similar_resources:
                logging.info("類似資料にリンクを追加")
                md_record = self.database.get_record_by_id(record_id)
                if md_record:
                    self.similar_detector.update_old_resources_with_new(
                        similar_resources,
                        md_record['md_path'],
                        masked_result['title']
                    )

            # 8. 通知
            logging.info("ステップ 6/6: 通知")
            self.notifier.notify_completion(record_id, similar_resources)

            if similar_resources:
                self.notifier.notify_similar_found(len(similar_resources))

            logging.info("="*50)
            logging.info(f"処理完了: ID={record_id}, カテゴリ={category}")
            logging.info(f"一時画像: {temp_image_path}")
            logging.info("手動で画像を保存または削除してください")
            logging.info("="*50)

        except Exception as e:
            logging.error(f"処理エラー: {e}", exc_info=True)
            self.notifier.notify_error(image_path, str(e))

    def search(self, query: str, filters: dict) -> list:
        """検索機能"""
        return self.database.search(query, filters)

    def init_database(self):
        """データベース初期化"""
        self.database.initialize()
        logging.info("データベース初期化が完了しました")


# CLIコマンド定義

@click.group()
def cli():
    """医療スクリーンショット自動整理システム (MedScreenArchiver)"""
    pass


@cli.command()
@click.option('--config', default='config/config.yaml', help='設定ファイルパス')
def start(config):
    """監視を開始"""
    try:
        # 設定ファイルのパス解決
        if not Path(config).is_absolute():
            config = Path(__file__).parent.parent / config

        app = MedScreenArchiver(str(config))
        app.start_monitoring()

    except KeyboardInterrupt:
        logging.info("\\nプログラムを終了します")
        sys.exit(0)
    except Exception as e:
        logging.error(f"エラー: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--config', default='config/config.yaml', help='設定ファイルパス')
def init(config):
    """データベース初期化"""
    try:
        # 設定ファイルのパス解決
        if not Path(config).is_absolute():
            config = Path(__file__).parent.parent / config

        app = MedScreenArchiver(str(config))
        app.init_database()

    except Exception as e:
        logging.error(f"エラー: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument('query', default='')
@click.option('--category', help='カテゴリ絞り込み')
@click.option('--from-date', 'from_date', help='開始日 (YYYY-MM-DD)')
@click.option('--to-date', 'to_date', help='終了日 (YYYY-MM-DD)')
@click.option('--needs-review', is_flag=True, help='要確認情報のみ')
@click.option('--limit', type=int, default=10, help='表示件数')
@click.option('--config', default='config/config.yaml', help='設定ファイルパス')
def search(query, category, from_date, to_date, needs_review, limit, config):
    """資料を検索"""
    try:
        # 設定ファイルのパス解決
        if not Path(config).is_absolute():
            config = Path(__file__).parent.parent / config

        app = MedScreenArchiver(str(config))

        filters = {
            'category': category,
            'from_date': from_date,
            'to_date': to_date,
            'needs_review': needs_review,
            'limit': limit
        }

        results = app.search(query, filters)

        if not results:
            click.echo("検索結果がありません")
            return

        click.echo(f"\\n検索結果: {len(results)} 件\\n")
        click.echo("-" * 80)

        for i, result in enumerate(results, 1):
            click.echo(f"{i}. [{result['id']}] {result.get('md_path', '')}")
            click.echo(f"   カテゴリ: {result.get('category', '不明')}")
            click.echo(f"   作成日時: {result.get('created_at', '不明')}")
            if result.get('summary'):
                summary = result['summary'][:100] + '...' if len(result['summary']) > 100 else result['summary']
                click.echo(f"   要約: {summary}")
            click.echo("-" * 80)

    except Exception as e:
        logging.error(f"エラー: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument('record_id', type=int)
@click.option('--config', default='config/config.yaml', help='設定ファイルパス')
def save_image(record_id, config):
    """一時画像をアーカイブに保存"""
    try:
        # 設定ファイルのパス解決
        if not Path(config).is_absolute():
            config = Path(__file__).parent.parent / config

        app = MedScreenArchiver(str(config))

        # レコード取得
        record = app.database.get_record_by_id(record_id)
        if not record:
            click.echo(f"エラー: ID {record_id} のレコードが見つかりません")
            return

        # 元の画像パスから一時フォルダのパスを推定
        original_path = Path(record['file_path'])
        temp_path = app.image_manager.temp_folder / original_path.name

        if not temp_path.exists():
            click.echo(f"エラー: 一時画像が見つかりません: {temp_path}")
            return

        # アーカイブに保存
        archive_path = app.image_manager.save_to_archive(str(temp_path), record_id)

        if archive_path:
            # データベース更新
            app.database.update_image_path(record_id, archive_path)
            click.echo(f"画像を保存しました: {archive_path}")
        else:
            click.echo("エラー: 画像保存に失敗しました")

    except Exception as e:
        logging.error(f"エラー: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument('record_id', type=int)
@click.option('--config', default='config/config.yaml', help='設定ファイルパス')
def delete_image(record_id, config):
    """一時画像を削除"""
    try:
        # 設定ファイルのパス解決
        if not Path(config).is_absolute():
            config = Path(__file__).parent.parent / config

        app = MedScreenArchiver(str(config))

        # レコード取得
        record = app.database.get_record_by_id(record_id)
        if not record:
            click.echo(f"エラー: ID {record_id} のレコードが見つかりません")
            return

        # 元の画像パスから一時フォルダのパスを推定
        original_path = Path(record['file_path'])
        temp_path = app.image_manager.temp_folder / original_path.name

        if temp_path.exists():
            app.image_manager.delete_temp_image(str(temp_path))
            click.echo(f"画像を削除しました: {temp_path}")
        else:
            click.echo(f"一時画像が見つかりません: {temp_path}")

    except Exception as e:
        logging.error(f"エラー: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--config', default='config/config.yaml', help='設定ファイルパス')
def list_temp(config):
    """一時フォルダの画像一覧を表示"""
    try:
        # 設定ファイルのパス解決
        if not Path(config).is_absolute():
            config = Path(__file__).parent.parent / config

        app = MedScreenArchiver(str(config))

        images = app.image_manager.list_temp_images()
        stats = app.image_manager.get_temp_folder_size()

        if not images:
            click.echo("一時フォルダに画像はありません")
            return

        click.echo(f"\\n一時フォルダ: {app.image_manager.temp_folder}")
        click.echo(f"画像数: {stats['file_count']} 件")
        click.echo(f"合計サイズ: {stats['total_size_mb']} MB\\n")
        click.echo("-" * 80)

        for i, img in enumerate(images, 1):
            click.echo(f"{i}. {img['name']}")
            click.echo(f"   サイズ: {img['size_mb']} MB")
            click.echo(f"   作成: {img['created']}")
            click.echo("-" * 80)

    except Exception as e:
        logging.error(f"エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
