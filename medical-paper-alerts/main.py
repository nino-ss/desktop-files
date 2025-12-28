#!/usr/bin/env python3
"""
医学論文自動通知システム - メインスクリプト

週2回、最新の医学論文を取得し、和訳・解説を付けて通知します。
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fetch_papers import PubMedFetcher
from filter_papers import PaperFilter
from translate_summarize import PaperTranslator
from storage import PaperStorage
from notifier import PaperNotifier

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'logs' / f"{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_directories():
    """必要なディレクトリを作成"""
    base_dir = Path(__file__).parent

    directories = [
        base_dir / 'logs',
        base_dir / 'data' / 'papers',
        base_dir / 'data' / 'summaries',
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def main(dry_run: bool = False, test_mode: bool = False):
    """
    メイン処理

    Args:
        dry_run: True の場合、通知を送らずに論文取得とフィルタリングのみ実行
        test_mode: True の場合、少数の論文のみで動作確認
    """
    logger.info("=" * 60)
    logger.info("医学論文自動通知システム - 実行開始")
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"モード: {'テストモード' if test_mode else 'ドライラン' if dry_run else '通常モード'}")
    logger.info("=" * 60)

    # ディレクトリセットアップ
    setup_directories()

    # 設定ファイルのパス
    config_path = Path(__file__).parent / "config" / "config.yaml"

    try:
        # ステップ1: 論文取得
        logger.info("\n[ステップ1] 論文取得中...")
        fetcher = PubMedFetcher(str(config_path))
        papers_by_category = fetcher.fetch_papers_by_category()

        total_fetched = sum(len(papers) for papers in papers_by_category.values())
        logger.info(f"✓ 合計 {total_fetched}件の論文を取得しました")

        if total_fetched == 0:
            logger.warning("論文が1件も取得できませんでした。処理を終了します。")
            return

        # ステップ2: フィルタリング・厳選
        logger.info("\n[ステップ2] 論文フィルタリング・厳選中...")
        paper_filter = PaperFilter(str(config_path))
        filtered_papers = paper_filter.filter_papers_by_category(papers_by_category)

        total_filtered = sum(len(papers) for papers in filtered_papers.values())
        logger.info(f"✓ {total_filtered}件の論文を厳選しました")

        if total_filtered == 0:
            logger.warning("フィルタリング後の論文が0件です。処理を終了します。")
            return

        # テストモードの場合、各カテゴリ2件まで
        if test_mode:
            logger.info("テストモード: 各カテゴリ2件までに制限します")
            filtered_papers = {
                category: papers[:2]
                for category, papers in filtered_papers.items()
            }

        # ステップ3: 和訳・解説生成
        logger.info("\n[ステップ3] 和訳・解説生成中...")
        translator = PaperTranslator(str(config_path))

        processed_papers_by_category = {}
        for category, papers_with_scores in filtered_papers.items():
            logger.info(f"  カテゴリ '{category}' を処理中...")
            processed = translator.process_papers(papers_with_scores, category)
            processed_papers_by_category[category] = processed

        logger.info("✓ 全ての論文の和訳・解説が完了しました")

        # ステップ4: ストレージに保存
        logger.info("\n[ステップ4] 論文データを保存中...")
        storage = PaperStorage(str(config_path))
        saved_files = storage.save_all(processed_papers_by_category)

        logger.info("✓ 保存完了:")
        for key, filepath in saved_files.items():
            logger.info(f"  {key}: {filepath}")

        # ステップ5: 通知送信
        if dry_run:
            logger.info("\n[ステップ5] ドライランモード: 通知はスキップします")
        else:
            logger.info("\n[ステップ5] 通知送信中...")
            notifier = PaperNotifier(str(config_path))

            markdown_path = saved_files.get('markdown')
            results = notifier.notify_all(processed_papers_by_category, markdown_path)

            logger.info("✓ 通知送信結果:")
            for method, success in results.items():
                status = "成功 ✓" if success else "失敗 ✗"
                logger.info(f"  {method}: {status}")

        # サマリー
        logger.info("\n" + "=" * 60)
        logger.info("処理完了サマリー")
        logger.info("=" * 60)
        logger.info(f"取得論文数: {total_fetched}件")
        logger.info(f"厳選論文数: {total_filtered}件")

        for category, papers in processed_papers_by_category.items():
            logger.info(f"  - {category}: {len(papers)}件")

        logger.info("=" * 60)
        logger.info("実行完了")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(
        description="医学論文自動通知システム"
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='通知を送らずに論文取得とフィルタリングのみ実行'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='テストモード: 少数の論文のみで動作確認'
    )

    args = parser.parse_args()

    # メイン処理実行
    main(dry_run=args.dry_run, test_mode=args.test)
