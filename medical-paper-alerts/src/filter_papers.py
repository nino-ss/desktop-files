#!/usr/bin/env python3
"""
論文フィルタリング・厳選モジュール
取得した論文を評価し、関連性の高いものを厳選します
"""

import yaml
import logging
from typing import List, Dict, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class PaperFilter:
    """論文をフィルタリング・厳選するクラス"""

    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self.preferred_journals = set(
            self.config['filtering'].get('preferred_journals', [])
        )

    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def calculate_relevance_score(self, paper: Dict, category: str) -> float:
        """
        論文の関連性スコアを計算

        Args:
            paper: 論文情報
            category: カテゴリ名

        Returns:
            関連性スコア (0.0 - 1.0)
        """
        score = 0.0
        max_score = 0.0

        # 1. ジャーナルスコア (30点)
        max_score += 30
        if paper.get('journal', '') in self.preferred_journals:
            score += 30
        elif paper.get('journal', ''):
            score += 10  # その他のジャーナルでも基本点

        # 2. 抄録の存在 (20点)
        max_score += 20
        abstract = paper.get('abstract', '')
        if len(abstract) > 500:
            score += 20
        elif len(abstract) > 200:
            score += 10

        # 3. キーワード一致度 (25点)
        max_score += 25
        keywords = paper.get('keywords', [])
        mesh_terms = paper.get('mesh_terms', [])
        all_terms = [k.lower() for k in keywords + mesh_terms]

        # カテゴリごとの重要キーワード
        category_keywords = {
            'female_urology': [
                'urinary incontinence', 'pelvic organ prolapse', 'overactive bladder',
                'urogynecology', 'lower urinary tract', 'bladder dysfunction'
            ],
            'female_sexual_function': [
                'sexual dysfunction', 'sexual arousal', 'sexual desire',
                'dyspareunia', 'sexual health', 'genito-pelvic pain'
            ],
            'general_sexual_function': [
                'sexual dysfunction', 'erectile dysfunction', 'sexual medicine',
                'premature ejaculation', 'sexual health'
            ],
            'pelvic_floor': [
                'pelvic floor', 'levator ani', 'pelvic floor muscle',
                'pelvic rehabilitation', 'pelvic floor dysfunction'
            ]
        }

        important_keywords = category_keywords.get(category, [])
        matches = sum(1 for kw in important_keywords if any(kw in term for term in all_terms))
        if important_keywords:
            score += (matches / len(important_keywords)) * 25

        # 4. DOIの存在 (15点)
        max_score += 15
        if paper.get('doi'):
            score += 15

        # 5. 新しさ (10点) - より新しい論文を優先
        max_score += 10
        pub_date = paper.get('publication_date', '')
        if pub_date:
            try:
                pub_datetime = datetime.fromisoformat(pub_date)
                days_old = (datetime.now() - pub_datetime).days
                if days_old <= 7:
                    score += 10
                elif days_old <= 14:
                    score += 7
                elif days_old <= 30:
                    score += 5
            except:
                pass

        # 正規化 (0.0 - 1.0)
        normalized_score = score / max_score if max_score > 0 else 0.0

        return normalized_score

    def calculate_impact_score(self, paper: Dict) -> float:
        """
        論文のインパクトスコアを計算（高インパクトジャーナルを優先）

        Args:
            paper: 論文情報

        Returns:
            インパクトスコア (0.0 - 1.0)
        """
        # 簡易的なインパクトファクターマッピング
        journal_impact = {
            'Nature Reviews Urology': 1.0,
            'European Urology': 0.95,
            'The Journal of Sexual Medicine': 0.85,
            'BJU International': 0.8,
            'Neurourology and Urodynamics': 0.75,
            'International Urogynecology Journal': 0.7,
            'Sexual Medicine': 0.65,
        }

        journal = paper.get('journal', '')
        return journal_impact.get(journal, 0.5)  # デフォルト0.5

    def filter_and_rank_papers(
        self,
        papers: List[Dict],
        category: str,
        max_papers: int = None
    ) -> List[Tuple[Dict, float]]:
        """
        論文をフィルタリング・ランキング

        Args:
            papers: 論文リスト
            category: カテゴリ名
            max_papers: 最大取得件数

        Returns:
            (論文, 総合スコア)のタプルリスト
        """
        if not papers:
            return []

        if max_papers is None:
            max_papers = self.config['selection']['max_papers_per_notification']

        min_relevance = self.config['filtering']['min_relevance_score']
        prioritize_impact = self.config['selection']['prioritize_high_impact']

        # スコア計算
        scored_papers = []
        for paper in papers:
            relevance_score = self.calculate_relevance_score(paper, category)

            # 最低関連性スコアでフィルタリング
            if relevance_score < min_relevance:
                continue

            # 総合スコア計算
            if prioritize_impact:
                impact_score = self.calculate_impact_score(paper)
                total_score = (relevance_score * 0.7) + (impact_score * 0.3)
            else:
                total_score = relevance_score

            scored_papers.append((paper, total_score))

        # スコアでソート（降順）
        scored_papers.sort(key=lambda x: x[1], reverse=True)

        # 上位N件を返す
        return scored_papers[:max_papers]

    def filter_papers_by_category(
        self,
        papers_by_category: Dict[str, List[Dict]]
    ) -> Dict[str, List[Tuple[Dict, float]]]:
        """
        カテゴリごとに論文をフィルタリング

        Args:
            papers_by_category: カテゴリ名をキー、論文リストを値とする辞書

        Returns:
            カテゴリ名をキー、(論文, スコア)のタプルリストを値とする辞書
        """
        results = {}

        for category, papers in papers_by_category.items():
            logger.info(f"カテゴリ '{category}' の論文をフィルタリング中...")

            filtered = self.filter_and_rank_papers(papers, category)
            results[category] = filtered

            logger.info(
                f"カテゴリ '{category}': {len(papers)}件中{len(filtered)}件を厳選"
            )

        return results

    def get_paper_summary(self, paper: Dict, score: float) -> str:
        """
        論文の簡潔なサマリーを生成

        Args:
            paper: 論文情報
            score: スコア

        Returns:
            サマリーテキスト
        """
        authors_str = ", ".join(paper.get('authors', [])[:3])
        if len(paper.get('authors', [])) > 3:
            authors_str += " et al."

        summary = f"""
タイトル: {paper.get('title', 'N/A')}
著者: {authors_str}
ジャーナル: {paper.get('journal', 'N/A')}
発行日: {paper.get('publication_date', 'N/A')}
関連性スコア: {score:.2f}
PMID: {paper.get('pmid', 'N/A')}
URL: {paper.get('url', 'N/A')}
"""
        if paper.get('doi_url'):
            summary += f"DOI: {paper.get('doi_url')}\n"

        return summary.strip()


def main():
    """メイン関数"""
    import json
    from pathlib import Path

    # 設定ファイルのパス
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    # フィルター初期化
    paper_filter = PaperFilter(str(config_path))

    # サンプルデータ読み込み（実際には fetch_papers.py の出力を使用）
    data_dir = Path(__file__).parent.parent / "data" / "papers"

    papers_by_category = {}
    for category_dir in data_dir.iterdir():
        if category_dir.is_dir():
            category = category_dir.name

            # 最新のJSONファイルを読み込み
            json_files = sorted(category_dir.glob("*.json"), reverse=True)
            if json_files:
                with open(json_files[0], 'r', encoding='utf-8') as f:
                    papers_by_category[category] = json.load(f)

    # フィルタリング
    filtered_papers = paper_filter.filter_papers_by_category(papers_by_category)

    # 結果表示
    for category, papers in filtered_papers.items():
        print(f"\n{'='*60}")
        print(f"カテゴリ: {category}")
        print(f"{'='*60}\n")

        for i, (paper, score) in enumerate(papers, 1):
            print(f"{i}. {paper_filter.get_paper_summary(paper, score)}\n")


if __name__ == "__main__":
    main()
