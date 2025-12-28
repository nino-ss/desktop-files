#!/usr/bin/env python3
"""
論文和訳・解説モジュール
Claude APIを使用して論文の抄録を和訳し、専門的な解説を生成します
"""

import os
import yaml
import logging
from typing import Dict, List
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("Warning: anthropic package not installed. Run: pip install anthropic")
    Anthropic = None

logger = logging.getLogger(__name__)


class PaperTranslator:
    """論文を和訳・解説するクラス"""

    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)

        if Anthropic is None:
            logger.warning("Anthropic クライアントが利用できません")
            self.client = None
        else:
            api_key = self.config['claude_api'].get('api_key') or os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.warning("Claude API keyが設定されていません")
                self.client = None
            else:
                self.client = Anthropic(api_key=api_key)

        self.model = self.config['claude_api'].get('model', 'claude-3-5-sonnet-20241022')
        self.max_tokens = self.config['claude_api'].get('max_tokens', 4096)

    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def translate_and_explain(self, paper: Dict, category: str) -> Dict[str, str]:
        """
        論文の抄録を和訳し、専門的な解説を生成

        Args:
            paper: 論文情報
            category: カテゴリ名

        Returns:
            和訳と解説を含む辞書
        """
        if not self.client:
            return {
                'japanese_title': '（和訳機能が利用できません）',
                'japanese_abstract': '（和訳機能が利用できません）',
                'expert_commentary': '（解説機能が利用できません）',
                'clinical_significance': '（解説機能が利用できません）'
            }

        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        journal = paper.get('journal', '')
        authors = ", ".join(paper.get('authors', [])[:5])

        # カテゴリごとの専門分野を定義
        field_descriptions = {
            'female_urology': '女性泌尿器科・骨盤底機能',
            'female_sexual_function': '女性性機能医学',
            'general_sexual_function': '性機能医学',
            'pelvic_floor': '骨盤底機能・骨盤底リハビリテーション'
        }
        field = field_descriptions.get(category, '医学')

        # プロンプト作成
        prompt = f"""あなたは{field}の専門医です。以下の医学論文について、日本の医師向けに和訳と専門的な解説を提供してください。

【論文情報】
タイトル: {title}
著者: {authors}
ジャーナル: {journal}

【抄録（英語）】
{abstract}

以下の形式で回答してください：

## 1. タイトル和訳
（論文タイトルの正確な日本語訳）

## 2. 抄録和訳
（抄録の正確な日本語訳。医学用語は適切な日本語訳を使用し、必要に応じて英語も併記）

## 3. 専門家による解説
（以下の観点から200-300字程度で解説）
- この研究の臨床的意義
- 既存の知見との関係性
- 研究デザインや方法論の特徴
- 結果の解釈上の注意点

## 4. 臨床への示唆
（日常診療にどう活かせるか、100-150字程度）

## 5. キーポイント（3つ）
- ポイント1
- ポイント2
- ポイント3

専門的かつ分かりやすく、臨床医が実際に活用できる形で解説してください。"""

        try:
            # Claude APIを呼び出し
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text

            # レスポンスをパース
            result = self._parse_response(response_text)
            result['raw_response'] = response_text

            logger.info(f"論文 {paper.get('pmid')} の和訳・解説を生成しました")

            return result

        except Exception as e:
            logger.error(f"Claude API呼び出しエラー: {e}")
            return {
                'japanese_title': '（和訳エラー）',
                'japanese_abstract': '（和訳エラー）',
                'expert_commentary': '（解説エラー）',
                'clinical_significance': '（解説エラー）',
                'error': str(e)
            }

    def _parse_response(self, response_text: str) -> Dict[str, str]:
        """
        Claude APIのレスポンスをパース

        Args:
            response_text: Claude APIからのレスポンステキスト

        Returns:
            パースされた辞書
        """
        result = {
            'japanese_title': '',
            'japanese_abstract': '',
            'expert_commentary': '',
            'clinical_significance': '',
            'key_points': []
        }

        # セクションごとに分割
        sections = response_text.split('##')

        for section in sections:
            section = section.strip()
            if not section:
                continue

            lines = section.split('\n', 1)
            if len(lines) < 2:
                continue

            header = lines[0].strip()
            content = lines[1].strip()

            if 'タイトル和訳' in header or '1.' in header:
                result['japanese_title'] = content
            elif '抄録和訳' in header or '2.' in header:
                result['japanese_abstract'] = content
            elif '専門家による解説' in header or '3.' in header:
                result['expert_commentary'] = content
            elif '臨床への示唆' in header or '4.' in header:
                result['clinical_significance'] = content
            elif 'キーポイント' in header or '5.' in header:
                # キーポイントを抽出
                points = [line.strip('- ').strip() for line in content.split('\n') if line.strip().startswith('-')]
                result['key_points'] = points

        return result

    def process_papers(
        self,
        papers_with_scores: List[tuple],
        category: str
    ) -> List[Dict]:
        """
        複数の論文を処理

        Args:
            papers_with_scores: (論文, スコア)のタプルリスト
            category: カテゴリ名

        Returns:
            和訳・解説を含む論文情報のリスト
        """
        processed_papers = []

        for paper, score in papers_with_scores:
            logger.info(f"論文 {paper.get('pmid')} を処理中...")

            # 和訳・解説を生成
            translation = self.translate_and_explain(paper, category)

            # 論文情報に和訳・解説を追加
            processed_paper = {
                **paper,
                'relevance_score': score,
                'japanese_title': translation.get('japanese_title', ''),
                'japanese_abstract': translation.get('japanese_abstract', ''),
                'expert_commentary': translation.get('expert_commentary', ''),
                'clinical_significance': translation.get('clinical_significance', ''),
                'key_points': translation.get('key_points', []),
                'category': category
            }

            processed_papers.append(processed_paper)

        return processed_papers


def main():
    """メイン関数"""
    import json
    from pathlib import Path

    # 設定ファイルのパス
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    # 翻訳者初期化
    translator = PaperTranslator(str(config_path))

    # サンプル論文でテスト
    sample_paper = {
        'pmid': '12345678',
        'title': 'Novel treatments for urinary incontinence in women',
        'authors': ['Smith J', 'Johnson A'],
        'journal': 'International Urogynecology Journal',
        'abstract': 'This study evaluates new therapeutic approaches for female urinary incontinence...',
        'doi': '10.1234/example',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/',
    }

    result = translator.translate_and_explain(sample_paper, 'female_urology')

    print("=== 和訳・解説結果 ===\n")
    print(f"タイトル和訳:\n{result.get('japanese_title', 'N/A')}\n")
    print(f"抄録和訳:\n{result.get('japanese_abstract', 'N/A')}\n")
    print(f"専門家による解説:\n{result.get('expert_commentary', 'N/A')}\n")
    print(f"臨床への示唆:\n{result.get('clinical_significance', 'N/A')}\n")


if __name__ == "__main__":
    main()
