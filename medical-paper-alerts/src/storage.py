#!/usr/bin/env python3
"""
論文ストレージ管理モジュール
論文データをMarkdown/JSON形式で保存し、文献引用に活用しやすくします
"""

import json
import yaml
import logging
from typing import List, Dict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class PaperStorage:
    """論文をストレージに保存・管理するクラス"""

    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self.base_dir = Path(__file__).parent.parent / "data"
        self.papers_dir = self.base_dir / "papers"
        self.summaries_dir = self.base_dir / "summaries"

        # ディレクトリ作成
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def save_papers_json(
        self,
        papers: List[Dict],
        category: str,
        timestamp: datetime = None
    ) -> Path:
        """
        論文データをJSON形式で保存

        Args:
            papers: 論文リスト
            category: カテゴリ名
            timestamp: タイムスタンプ

        Returns:
            保存したファイルのパス
        """
        if timestamp is None:
            timestamp = datetime.now()

        # カテゴリディレクトリ
        category_dir = self.papers_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # ファイル名
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = category_dir / filename

        # 保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON保存: {filepath}")
        return filepath

    def generate_markdown_summary(
        self,
        papers_by_category: Dict[str, List[Dict]],
        timestamp: datetime = None
    ) -> str:
        """
        論文まとめをMarkdown形式で生成

        Args:
            papers_by_category: カテゴリ名をキー、論文リストを値とする辞書
            timestamp: タイムスタンプ

        Returns:
            Markdown形式のテキスト
        """
        if timestamp is None:
            timestamp = datetime.now()

        # カテゴリ名の日本語マッピング
        category_names_ja = {
            'female_urology': '女性泌尿器科',
            'female_sexual_function': '女性性機能',
            'general_sexual_function': '一般性機能',
            'pelvic_floor': '骨盤底機能'
        }

        # Markdownヘッダー
        md = f"# 医学論文まとめ - {timestamp.strftime('%Y年%m月%d日')}\n\n"
        md += f"作成日時：{timestamp.strftime('%Y年%m月%d日 %H:%M')}\n\n"
        md += "---\n\n"

        # カテゴリごとに論文を整理
        for category, papers in papers_by_category.items():
            if not papers:
                continue

            category_ja = category_names_ja.get(category, category)
            md += f"## {category_ja}\n\n"

            for i, paper in enumerate(papers, 1):
                md += self._format_paper_markdown(paper, i)
                md += "\n---\n\n"

        # 目次・サマリー
        md += self._generate_toc(papers_by_category, category_names_ja)

        return md

    def _format_paper_markdown(self, paper: Dict, index: int) -> str:
        """
        1つの論文をMarkdown形式でフォーマット

        Args:
            paper: 論文情報
            index: 論文番号

        Returns:
            Markdown形式のテキスト
        """
        md = f"### {index}. {paper.get('japanese_title', paper.get('title', ''))}\n\n"

        # 基本情報
        md += "**基本情報**\n\n"
        md += f"- **原題**: {paper.get('title', 'N/A')}\n"

        authors = paper.get('authors', [])
        authors_str = ", ".join(authors[:5])
        if len(authors) > 5:
            authors_str += " et al."
        md += f"- **著者**: {authors_str}\n"

        md += f"- **ジャーナル**: {paper.get('journal', 'N/A')}\n"
        md += f"- **発行日**: {paper.get('publication_date', 'N/A')}\n"
        md += f"- **PMID**: {paper.get('pmid', 'N/A')}\n"

        # リンク
        if paper.get('url'):
            md += f"- **PubMed**: [{paper['pmid']}]({paper['url']})\n"
        if paper.get('doi_url'):
            md += f"- **DOI**: {paper['doi_url']}\n"

        md += "\n"

        # 和訳抄録
        if paper.get('japanese_abstract'):
            md += "**抄録（日本語）**\n\n"
            md += f"{paper['japanese_abstract']}\n\n"

        # 専門家による解説
        if paper.get('expert_commentary'):
            md += "**専門家による解説**\n\n"
            md += f"{paper['expert_commentary']}\n\n"

        # 臨床への示唆
        if paper.get('clinical_significance'):
            md += "**臨床への示唆**\n\n"
            md += f"{paper['clinical_significance']}\n\n"

        # キーポイント
        if paper.get('key_points'):
            md += "**キーポイント**\n\n"
            for point in paper['key_points']:
                md += f"- {point}\n"
            md += "\n"

        # BibTeX（文献引用用）
        if self.config['storage'].get('include_bibtex', True):
            md += "**BibTeX引用**\n\n"
            md += "```bibtex\n"
            md += self._generate_bibtex(paper)
            md += "```\n\n"

        return md

    def _generate_bibtex(self, paper: Dict) -> str:
        """
        BibTeX形式の引用情報を生成

        Args:
            paper: 論文情報

        Returns:
            BibTeX形式のテキスト
        """
        pmid = paper.get('pmid', 'unknown')
        title = paper.get('title', '')
        authors = paper.get('authors', [])
        journal = paper.get('journal', '')
        year = paper.get('publication_date', '').split('-')[0] if paper.get('publication_date') else ''
        doi = paper.get('doi', '')

        # 著者をBibTeX形式に
        author_str = " and ".join(authors) if authors else "Unknown"

        bibtex = f"@article{{pmid{pmid},\n"
        bibtex += f"  title = {{{title}}},\n"
        bibtex += f"  author = {{{author_str}}},\n"
        bibtex += f"  journal = {{{journal}}},\n"
        if year:
            bibtex += f"  year = {{{year}}},\n"
        if doi:
            bibtex += f"  doi = {{{doi}}},\n"
        bibtex += f"  pmid = {{{pmid}}}\n"
        bibtex += "}\n"

        return bibtex

    def _generate_toc(
        self,
        papers_by_category: Dict[str, List[Dict]],
        category_names_ja: Dict[str, str]
    ) -> str:
        """
        目次とサマリーを生成

        Args:
            papers_by_category: カテゴリごとの論文リスト
            category_names_ja: カテゴリ名の日本語マッピング

        Returns:
            Markdown形式の目次
        """
        md = "## 📚 カテゴリ別サマリー\n\n"

        for category, papers in papers_by_category.items():
            if not papers:
                continue

            category_ja = category_names_ja.get(category, category)
            md += f"### {category_ja}\n"
            md += f"- 論文数: {len(papers)}件\n"

            # 主要ジャーナル
            journals = {}
            for paper in papers:
                journal = paper.get('journal', 'Unknown')
                journals[journal] = journals.get(journal, 0) + 1

            top_journals = sorted(journals.items(), key=lambda x: x[1], reverse=True)[:3]
            md += "- 主要ジャーナル: "
            md += ", ".join([f"{j} ({c}件)" for j, c in top_journals])
            md += "\n\n"

        return md

    def save_markdown_summary(
        self,
        papers_by_category: Dict[str, List[Dict]],
        timestamp: datetime = None
    ) -> Path:
        """
        Markdown形式の論文まとめを保存

        Args:
            papers_by_category: カテゴリ名をキー、論文リストを値とする辞書
            timestamp: タイムスタンプ

        Returns:
            保存したファイルのパス
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Markdown生成
        md_content = self.generate_markdown_summary(papers_by_category, timestamp)

        # ファイル名
        filename = f"{timestamp.strftime('%Y%m%d')}_論文まとめ.md"
        filepath = self.summaries_dir / filename

        # 保存
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Markdown保存: {filepath}")
        return filepath

    def save_all(
        self,
        papers_by_category: Dict[str, List[Dict]],
        timestamp: datetime = None
    ) -> Dict[str, Path]:
        """
        論文データをJSON・Markdown両方で保存

        Args:
            papers_by_category: カテゴリ名をキー、論文リストを値とする辞書
            timestamp: タイムスタンプ

        Returns:
            保存したファイルパスの辞書
        """
        if timestamp is None:
            timestamp = datetime.now()

        result = {}

        storage_format = self.config['storage'].get('format', 'both')

        # JSON保存
        if storage_format in ['json', 'both']:
            for category, papers in papers_by_category.items():
                if papers:
                    json_path = self.save_papers_json(papers, category, timestamp)
                    result[f"{category}_json"] = json_path

        # Markdown保存
        if storage_format in ['markdown', 'both']:
            md_path = self.save_markdown_summary(papers_by_category, timestamp)
            result['markdown'] = md_path

        return result


def main():
    """メイン関数"""
    from pathlib import Path

    # 設定ファイルのパス
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    # ストレージ初期化
    storage = PaperStorage(str(config_path))

    # サンプルデータ
    sample_papers = {
        'female_urology': [
            {
                'pmid': '12345678',
                'title': 'Novel treatments for urinary incontinence',
                'japanese_title': '尿失禁の新しい治療法',
                'authors': ['Smith J', 'Johnson A'],
                'journal': 'International Urogynecology Journal',
                'publication_date': '2025-12-01',
                'doi': '10.1234/example',
                'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/',
                'doi_url': 'https://doi.org/10.1234/example',
                'japanese_abstract': 'この研究では、尿失禁に対する新しい治療アプローチを評価しました...',
                'expert_commentary': 'この研究は、女性尿失禁治療における重要な進展を示しています...',
                'clinical_significance': '日常診療において、患者選択の際に有用な情報を提供します...',
                'key_points': [
                    '新しい治療法の有効性が示された',
                    '副作用が少ない',
                    '長期的な効果が期待できる'
                ]
            }
        ]
    }

    # 保存
    saved_files = storage.save_all(sample_papers)

    print("=== 保存完了 ===")
    for key, filepath in saved_files.items():
        print(f"{key}: {filepath}")


if __name__ == "__main__":
    main()
