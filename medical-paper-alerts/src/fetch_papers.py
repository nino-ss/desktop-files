#!/usr/bin/env python3
"""
論文取得モジュール
PubMed APIを使用して医学論文を検索・取得します
"""

import os
import sys
import yaml
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from Bio import Entrez
import requests
from bs4 import BeautifulSoup

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PubMedFetcher:
    """PubMedから論文を取得するクラス"""

    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)

        # Entrezの設定
        Entrez.email = self.config['pubmed']['email']
        if self.config['pubmed'].get('api_key'):
            Entrez.api_key = self.config['pubmed']['api_key']

    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def search_papers(self, query: str, days_back: int = 7, max_results: int = 50) -> List[str]:
        """
        PubMedで論文を検索

        Args:
            query: 検索クエリ
            days_back: 過去何日分の論文を検索するか
            max_results: 最大取得件数

        Returns:
            論文ID（PMID）のリスト
        """
        try:
            # 日付範囲の計算
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            date_query = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[pdat]"
            full_query = f"{query} AND {date_query}"

            logger.info(f"検索クエリ: {full_query}")

            # PubMed検索
            handle = Entrez.esearch(
                db="pubmed",
                term=full_query,
                retmax=max_results,
                sort="relevance"
            )

            results = Entrez.read(handle)
            handle.close()

            id_list = results.get("IdList", [])
            logger.info(f"{len(id_list)}件の論文が見つかりました")

            return id_list

        except Exception as e:
            logger.error(f"論文検索エラー: {e}")
            return []

    def fetch_paper_details(self, pmid_list: List[str]) -> List[Dict]:
        """
        論文の詳細情報を取得

        Args:
            pmid_list: 論文ID（PMID）のリスト

        Returns:
            論文詳細情報のリスト
        """
        if not pmid_list:
            return []

        try:
            # 論文詳細を取得
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(pmid_list),
                rettype="xml"
            )

            records = Entrez.read(handle)
            handle.close()

            papers = []
            for record in records.get('PubmedArticle', []):
                paper = self._parse_paper_record(record)
                if paper:
                    papers.append(paper)

            logger.info(f"{len(papers)}件の論文詳細を取得しました")
            return papers

        except Exception as e:
            logger.error(f"論文詳細取得エラー: {e}")
            return []

    def _parse_paper_record(self, record: dict) -> Optional[Dict]:
        """
        PubMed XMLレコードをパース

        Args:
            record: PubMed XMLレコード

        Returns:
            論文情報の辞書
        """
        try:
            article = record['MedlineCitation']['Article']
            pmid = str(record['MedlineCitation']['PMID'])

            # タイトル
            title = article.get('ArticleTitle', '')

            # 著者
            authors = []
            author_list = article.get('AuthorList', [])
            for author in author_list[:5]:  # 最初の5人まで
                if 'LastName' in author and 'Initials' in author:
                    authors.append(f"{author['LastName']} {author['Initials']}")

            # 抄録
            abstract = ""
            if 'Abstract' in article:
                abstract_texts = article['Abstract'].get('AbstractText', [])
                if isinstance(abstract_texts, list):
                    abstract = " ".join(str(text) for text in abstract_texts)
                else:
                    abstract = str(abstract_texts)

            # ジャーナル情報
            journal = article.get('Journal', {})
            journal_title = journal.get('Title', '')

            # 発行日
            pub_date = article.get('ArticleDate', [{}])
            if pub_date and isinstance(pub_date, list):
                pub_date = pub_date[0]

            year = pub_date.get('Year', '')
            month = pub_date.get('Month', '')
            day = pub_date.get('Day', '')
            publication_date = f"{year}-{month}-{day}" if year else ""

            # DOI
            doi = ""
            article_ids = record.get('PubmedData', {}).get('ArticleIdList', [])
            for article_id in article_ids:
                if article_id.attributes.get('IdType') == 'doi':
                    doi = str(article_id)
                    break

            # キーワード
            keywords = []
            keyword_list = record['MedlineCitation'].get('KeywordList', [])
            if keyword_list:
                keywords = [str(kw) for kw in keyword_list[0][:10]]  # 最初の10個まで

            # MeSH用語
            mesh_terms = []
            mesh_list = record['MedlineCitation'].get('MeshHeadingList', [])
            for mesh in mesh_list[:10]:  # 最初の10個まで
                if 'DescriptorName' in mesh:
                    mesh_terms.append(str(mesh['DescriptorName']))

            return {
                'pmid': pmid,
                'title': title,
                'authors': authors,
                'journal': journal_title,
                'publication_date': publication_date,
                'abstract': abstract,
                'doi': doi,
                'keywords': keywords,
                'mesh_terms': mesh_terms,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                'doi_url': f"https://doi.org/{doi}" if doi else "",
                'fetched_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"論文レコードのパースエラー: {e}")
            return None

    def fetch_papers_by_category(self) -> Dict[str, List[Dict]]:
        """
        カテゴリごとに論文を取得

        Returns:
            カテゴリ名をキー、論文リストを値とする辞書
        """
        results = {}

        days_back = self.config['filtering']['days_back']
        max_results = self.config['pubmed']['max_results']

        for category, queries in self.config['search_queries'].items():
            logger.info(f"カテゴリ '{category}' の論文を検索中...")

            all_papers = []
            seen_pmids = set()

            for query in queries:
                # 論文IDを検索
                pmid_list = self.search_papers(query, days_back, max_results)

                # 重複を除外
                unique_pmids = [pmid for pmid in pmid_list if pmid not in seen_pmids]
                seen_pmids.update(unique_pmids)

                # 論文詳細を取得
                if unique_pmids:
                    papers = self.fetch_paper_details(unique_pmids)
                    all_papers.extend(papers)

            results[category] = all_papers
            logger.info(f"カテゴリ '{category}': {len(all_papers)}件の論文を取得")

        return results


def main():
    """メイン関数"""
    # 設定ファイルのパス
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    # 論文取得
    fetcher = PubMedFetcher(str(config_path))
    papers_by_category = fetcher.fetch_papers_by_category()

    # 結果をJSONで保存
    import json
    output_dir = Path(__file__).parent.parent / "data" / "papers"

    for category, papers in papers_by_category.items():
        output_file = output_dir / category / f"{datetime.now().strftime('%Y%m%d')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)

        logger.info(f"保存: {output_file}")


if __name__ == "__main__":
    main()
