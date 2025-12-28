"""
個人情報マスキングモジュール
患者個人情報の検出と削除、性別・年齢のみを保持
"""

import re
import logging
from typing import Dict, List
from datetime import datetime


class PrivacyMasker:
    """個人情報マスキングクラス"""

    def __init__(self, config: dict):
        self.config = config

        # 個人情報検出パターン
        self.patterns = {
            'name': [
                r'患者名[:：\s]*([^\s\n]+)',
                r'氏名[:：\s]*([^\s\n]+)',
                r'Name[:：\s]*([A-Za-z\s]+)',
                r'患者[:：\s]*([^\s\n]{2,4})',  # 「患者: 山田太郎」など
            ],
            'patient_id': [
                r'患者ID[:：\s]*([0-9A-Z\-]+)',
                r'ID[:：\s]*([0-9A-Z\-]+)',
                r'カルテ番号[:：\s]*([0-9\-]+)',
                r'診察券番号[:：\s]*([0-9\-]+)',
            ],
            'birth_date': [
                r'生年月日[:：\s]*(\d{4}[年/\-]\d{1,2}[月/\-]\d{1,2}日?)',
                r'DOB[:：\s]*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})',
                r'生年月日[:：\s]*([\d]{8})',  # YYYYMMDD形式
            ],
            'address': [
                r'住所[:：\s]*([^\n]+)',
                r'Address[:：\s]*([^\n]+)',
            ],
            'phone': [
                r'電話[:：\s]*(\d{2,4}[-\s]?\d{2,4}[-\s]?\d{4})',
                r'TEL[:：\s]*(\d{2,4}[-\s]?\d{2,4}[-\s]?\d{4})',
            ],
        }

    def mask(self, analysis_result: dict) -> dict:
        """個人情報をマスキング"""
        masked_result = analysis_result.copy()

        # AIが検出した個人識別情報
        patient_identifiers = analysis_result.get('case_info', {}).get('patient_identifiers', [])

        logging.info(f"個人情報マスキング開始: {len(patient_identifiers)} 件の識別情報を検出")

        # フルテキストからマスキング
        full_text = analysis_result.get('full_text', '')
        masked_text, masked_count = self._mask_text(full_text, patient_identifiers)
        masked_result['full_text'] = masked_text

        # サマリーからもマスキング
        summary = analysis_result.get('summary', '')
        masked_summary, _ = self._mask_text(summary, patient_identifiers)
        masked_result['summary'] = masked_summary

        # タイトルからもマスキング
        title = analysis_result.get('title', '')
        masked_title, _ = self._mask_text(title, patient_identifiers)
        masked_result['title'] = masked_title

        # 性別・年齢のみ保持
        case_info = analysis_result.get('case_info', {})
        masked_result['case_info'] = {
            'gender': case_info.get('gender', '不明'),
            'age': case_info.get('age', '不明'),
        }

        # マスキングログ
        masked_result['privacy_masked'] = {
            'masked_count': masked_count,
            'ai_detected_count': len(patient_identifiers),
            'pattern_detected_count': masked_count - len(patient_identifiers),
            'masked_at': datetime.now().isoformat()
        }

        if masked_count > 0:
            logging.info(f"個人情報マスキング完了: {masked_count} 箇所をマスキング")
        else:
            logging.info("個人情報マスキング完了: マスキング対象なし")

        return masked_result

    def _mask_text(self, text: str, identifiers: List[str]) -> tuple[str, int]:
        """テキストから個人情報をマスキング"""
        masked_text = text
        masked_count = 0

        # AIが検出した識別情報を削除
        for identifier in identifiers:
            if identifier and len(identifier) > 0:
                # 完全一致で置換
                if identifier in masked_text:
                    masked_text = masked_text.replace(identifier, '[個人情報削除]')
                    masked_count += 1

        # パターンマッチングで追加検出
        for pattern_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, masked_text)
                if matches:
                    for match in matches:
                        # 氏名や住所など、長さが2文字以下の場合はスキップ（誤検出防止）
                        if pattern_type in ['name', 'address'] and len(match) <= 2:
                            continue

                        masked_text = re.sub(
                            re.escape(match),
                            f'[{pattern_type}削除]',
                            masked_text,
                            count=1
                        )
                        masked_count += 1

        return masked_text, masked_count

    def preview_masking(self, original_text: str, masked_text: str) -> dict:
        """マスキング前後のプレビュー"""
        return {
            'original': original_text,
            'masked': masked_text,
            'diff': self._generate_diff(original_text, masked_text)
        }

    def _generate_diff(self, original: str, masked: str) -> List[dict]:
        """差分を生成"""
        import difflib

        diff = []
        matcher = difflib.SequenceMatcher(None, original, masked)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                diff.append({
                    'type': 'masked',
                    'original': original[i1:i2],
                    'masked': masked[j1:j2],
                    'position': i1
                })

        return diff

    def validate_masking(self, masked_text: str) -> dict:
        """マスキング結果の検証"""
        warnings = []

        # 数字の連続をチェック（患者IDなどの可能性）
        long_numbers = re.findall(r'\d{6,}', masked_text)
        if long_numbers:
            warnings.append(f"6桁以上の数字が残っています: {long_numbers}")

        # 日付パターンをチェック
        date_patterns = re.findall(r'\d{4}[年/\-]\d{1,2}[月/\-]\d{1,2}', masked_text)
        if date_patterns:
            warnings.append(f"日付パターンが残っています: {date_patterns}")

        # 電話番号パターンをチェック
        phone_patterns = re.findall(r'\d{2,4}[-\s]\d{2,4}[-\s]\d{4}', masked_text)
        if phone_patterns:
            warnings.append(f"電話番号パターンが残っています: {phone_patterns}")

        return {
            'is_safe': len(warnings) == 0,
            'warnings': warnings
        }
