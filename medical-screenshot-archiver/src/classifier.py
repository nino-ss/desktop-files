"""
自動分類モジュール
解析結果からカテゴリを判定し、適切なフォルダに保存
"""

import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class Classifier:
    """自動分類クラス"""

    def __init__(self, config: dict):
        self.config = config
        self.categories = config['classification']['categories']
        self.base_folder = Path(config['storage']['base_folder']).expanduser()

        # 医学用語辞書を読み込み
        terms_path = Path(__file__).parent.parent / 'data' / 'medical_terms.json'
        if terms_path.exists():
            with open(terms_path, 'r', encoding='utf-8') as f:
                self.medical_terms = json.load(f)
        else:
            logging.warning(f"医学用語辞書が見つかりません: {terms_path}")
            self.medical_terms = {}

        # カテゴリキーワードマッピング
        self.category_keywords = {
            '婦人科/GSM関連': ['GSM', '萎縮性腟炎', 'エストロゲン', '閉経後', '外陰腟', '性交痛', 'genitourinary'],
            '婦人科/骨盤臓器脱': ['骨盤臓器脱', 'POP', '子宮脱', '膀胱瘤', '直腸瘤', 'pelvic organ prolapse'],
            '婦人科/更年期障害': ['更年期', 'HRT', 'ホルモン補充療法', '閉経', 'menopause'],
            '産科': ['妊娠', '出産', '分娩', '妊婦', '胎児', 'pregnancy', 'delivery'],
            '泌尿器科': ['排尿障害', '尿失禁', '過活動膀胱', 'OAB', '前立腺', 'urinary'],
            '一般': [],  # デフォルトカテゴリ
        }

    def classify(self, analysis_result: dict) -> str:
        """カテゴリを判定"""
        # AIの推定カテゴリを優先
        suggested_category = analysis_result.get('category_suggestion')
        if suggested_category and suggested_category in self.categories:
            logging.info(f"カテゴリ判定: {suggested_category} (AI推定)")
            return suggested_category

        # キーワードから判定
        keywords = analysis_result.get('keywords', [])
        medical_terms = analysis_result.get('medical_terms', {})

        category = self._match_category(keywords, medical_terms)

        if category:
            logging.info(f"カテゴリ判定: {category} (キーワードマッチ)")
            return category

        # デフォルトカテゴリ
        logging.info("カテゴリ判定: 一般 (デフォルト)")
        return '一般'

    def _match_category(self, keywords: List[str], medical_terms: dict) -> Optional[str]:
        """キーワードとカテゴリをマッチング"""
        # カテゴリごとのスコアを計算
        scores = {category: 0 for category in self.categories}

        # キーワードマッチング
        for category, category_kws in self.category_keywords.items():
            for kw in keywords:
                kw_lower = kw.lower()
                for ckw in category_kws:
                    if ckw.lower() in kw_lower or kw_lower in ckw.lower():
                        scores[category] += 2
                        break

        # 疾患名マッチング
        for disease in medical_terms.get('diseases', []):
            disease_lower = disease.lower()
            for category, category_kws in self.category_keywords.items():
                for ckw in category_kws:
                    if ckw.lower() in disease_lower or disease_lower in ckw.lower():
                        scores[category] += 3
                        break

        # 治療法マッチング
        for treatment in medical_terms.get('treatments', []):
            treatment_lower = treatment.lower()
            for category, category_kws in self.category_keywords.items():
                for ckw in category_kws:
                    if ckw.lower() in treatment_lower or treatment_lower in ckw.lower():
                        scores[category] += 2
                        break

        # 最高スコアのカテゴリを返す
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)

        return None

    def get_save_path(self, category: str, title: str, timestamp: datetime) -> Path:
        """保存パスを取得"""
        # カテゴリフォルダ
        category_folder = self.base_folder / category
        category_folder.mkdir(parents=True, exist_ok=True)

        # ファイル名生成（日付 + タイトル）
        date_str = timestamp.strftime('%Y%m%d')
        safe_title = self._sanitize_filename(title)
        filename = f"{date_str}_{safe_title}.md"

        # 重複チェック
        filepath = category_folder / filename
        counter = 1
        while filepath.exists():
            filename = f"{date_str}_{safe_title}_{counter}.md"
            filepath = category_folder / filename
            counter += 1

        return filepath

    def _sanitize_filename(self, title: str, max_length: int = 50) -> str:
        """ファイル名をサニタイズ"""
        # 使用不可文字を削除
        sanitized = re.sub(r'[\\/:*?"<>|]', '', title)

        # スペースをアンダースコアに
        sanitized = sanitized.replace(' ', '_')

        # 長さ制限
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        # 空文字対策
        if not sanitized:
            sanitized = "untitled"

        return sanitized.strip('_')

    def get_categories(self) -> List[str]:
        """利用可能なカテゴリ一覧を取得"""
        return self.categories.copy()

    def get_category_stats(self) -> Dict[str, int]:
        """カテゴリ別の資料数を取得"""
        stats = {}

        for category in self.categories:
            category_folder = self.base_folder / category
            if category_folder.exists():
                md_files = list(category_folder.glob('*.md'))
                stats[category] = len(md_files)
            else:
                stats[category] = 0

        return stats
