"""
画像解析モジュール
Claude APIを使った画像解析、OCR、内容理解、出典情報抽出を提供
"""

import os
import base64
import json
import re
import logging
from io import BytesIO
from pathlib import Path
from datetime import datetime
from typing import Dict

import anthropic
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential


class ImageAnalyzer:
    """画像解析クラス"""

    def __init__(self, config: dict):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY環境変数が設定されていません")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = config['ai']['model']
        self.max_tokens = config['ai']['max_tokens']

    def _optimize_image(self, image_path: str, max_size: int = 1568) -> bytes:
        """画像を最適化（API送信用）"""
        try:
            img = Image.open(image_path)

            # RGBA → RGB変換（PNGの透過対応）
            if img.mode == 'RGBA':
                # 白背景で合成
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # アルファチャンネル
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # サイズ調整
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # JPEG形式でバイト列に変換（サイズ削減）
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)

            return buffer.getvalue()

        except Exception as e:
            logging.error(f"画像最適化エラー: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def analyze(self, image_path: str) -> dict:
        """画像を解析"""
        logging.info(f"解析開始: {image_path}")

        # 画像を最適化
        image_data = self._optimize_image(image_path)
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # プロンプト構築
        prompt = self._build_analysis_prompt()

        # Claude APIで解析
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # レスポンスをパース
            response_text = message.content[0].text
            result = self._parse_response(response_text)

            # 元のファイルパスを追加
            result['original_image_path'] = image_path
            result['analyzed_at'] = datetime.now().isoformat()

            logging.info(f"解析完了: {result.get('title', '無題')}")

            return result

        except Exception as e:
            logging.error(f"Claude API エラー: {e}")
            raise

    def _build_analysis_prompt(self) -> str:
        """解析用プロンプトを構築"""
        return """
この医療関連のスクリーンショット画像を解析してください。

以下の情報を抽出し、JSON形式で返してください：

{
  "title": "画像の主題・タイトル（50文字以内）",
  "summary": "内容の要約（200文字以内）",
  "full_text": "画像内の全文字情報（OCR結果）。個人情報は含めないでください",
  "keywords": ["キーワード1", "キーワード2", ...],
  "medical_terms": {
    "diseases": ["疾患名1", "疾患名2", ...],
    "treatments": ["治療法1", "治療法2", ...],
    "drugs": ["薬剤名1", "薬剤名2", ...]
  },
  "source": {
    "type": "学会 or 論文 or 教科書 or その他 or null",
    "conference_name": "学会名（該当する場合）",
    "paper_title": "論文タイトル（該当する場合）",
    "authors": ["著者1", "著者2", ...],
    "year": "発表年・出版年（YYYY形式）",
    "source_text": "出典情報の元テキスト"
  },
  "case_info": {
    "has_case": true/false,
    "gender": "男性 or 女性 or 不明",
    "age": "年齢（数値または範囲、例: 65 or 60-70 or 不明）",
    "patient_identifiers": ["検出された個人識別情報のリスト（氏名、生年月日、患者IDなど）"]
  },
  "visual_elements": {
    "has_chart": true/false,
    "has_graph": true/false,
    "has_image": true/false,
    "has_diagram": true/false,
    "description": "図表・画像の説明（テキストのみでは不十分な場合）。何も特筆すべきものがなければ空文字"
  },
  "category_suggestion": "最も適切なカテゴリの推定（婦人科/GSM関連、婦人科/骨盤臓器脱、婦人科/更年期障害、産科、泌尿器科、一般、のいずれか）"
}

重要な注意事項：
1. 患者個人情報（氏名、生年月日、ID番号）を検出した場合は、case_info.patient_identifiers に正確に記録してください
2. full_text には個人情報を含めないでください（性別・年齢は除く）
3. 性別と年齢のみを case_info に保持します
4. 医学用語は正確に抽出してください
5. 出典情報がない場合は source 全体を null にしてください
6. visual_elements.description は、図表やグラフの内容をテキストで説明してください（例：「BMIと骨密度の相関を示す散布図。BMI 18-25の範囲で骨密度が最も高い傾向」）

必ずJSON形式のみで返してください。説明文は不要です。
"""

    def _parse_response(self, response_text: str) -> dict:
        """Claude APIのレスポンスをパース"""
        # JSONブロックを抽出
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # マークダウンなしの場合
            json_str = response_text.strip()

        try:
            result = json.loads(json_str)

            # デフォルト値設定
            result.setdefault('title', '無題')
            result.setdefault('summary', '')
            result.setdefault('full_text', '')
            result.setdefault('keywords', [])
            result.setdefault('medical_terms', {'diseases': [], 'treatments': [], 'drugs': []})
            result.setdefault('source', None)
            result.setdefault('case_info', {'has_case': False, 'gender': '不明', 'age': '不明', 'patient_identifiers': []})
            result.setdefault('visual_elements', {'has_chart': False, 'has_graph': False, 'has_image': False, 'has_diagram': False, 'description': ''})
            result.setdefault('category_suggestion', '一般')

            return result

        except json.JSONDecodeError as e:
            logging.error(f"JSONパースエラー: {e}")
            logging.error(f"レスポンス: {response_text}")

            # フォールバック: 最低限の構造を返す
            return {
                "title": "解析エラー",
                "summary": response_text[:200] if len(response_text) > 200 else response_text,
                "full_text": response_text,
                "keywords": [],
                "medical_terms": {'diseases': [], 'treatments': [], 'drugs': []},
                "source": None,
                "case_info": {'has_case': False, 'gender': '不明', 'age': '不明', 'patient_identifiers': []},
                "visual_elements": {'has_chart': False, 'has_graph': False, 'has_image': False, 'has_diagram': False, 'description': ''},
                "category_suggestion": '一般',
                "error": str(e)
            }
