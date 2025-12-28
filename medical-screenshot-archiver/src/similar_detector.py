"""
類似資料検出モジュール
同一キーワードの古い資料を検出し、関連資料のリンクを生成
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


class SimilarDetector:
    """類似資料検出クラス"""

    def __init__(self, database, config: dict):
        self.database = database
        self.threshold_months = config['similar_detection']['old_resource_months']
        self.enabled = config['similar_detection']['enabled']

    def find_similar(self, keywords: List[str], category: str) -> List[dict]:
        """類似資料を検索"""
        if not self.enabled or not keywords:
            return []

        conn = sqlite3.connect(self.database.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # しきい値日付を計算
            threshold_date = datetime.now() - timedelta(days=self.threshold_months * 30)

            similar_resources = []

            # 各キーワードで検索
            for keyword in keywords:
                cursor.execute('''
                    SELECT id, md_path, category, keywords, summary, created_at
                    FROM screenshots
                    WHERE category = ?
                      AND created_at < ?
                      AND keywords LIKE ?
                ''', (category, threshold_date.isoformat(), f'%{keyword}%'))

                results = cursor.fetchall()

                for row in results:
                    # 重複チェック
                    if not any(r['id'] == row['id'] for r in similar_resources):
                        similar_resources.append({
                            'id': row['id'],
                            'md_path': row['md_path'],
                            'title': self._extract_title_from_md(row['md_path']),
                            'created_at': row['created_at'],
                            'matched_keyword': keyword
                        })

            # 日付でソート（古い順）
            similar_resources.sort(key=lambda x: x['created_at'])

            if similar_resources:
                logging.info(f"類似資料検出: {len(similar_resources)} 件")

            return similar_resources

        except Exception as e:
            logging.error(f"類似資料検出エラー: {e}")
            return []

        finally:
            conn.close()

    def _extract_title_from_md(self, md_path: str) -> str:
        """Markdownファイルからタイトルを抽出"""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('# '):
                    return first_line[2:]
        except Exception as e:
            logging.warning(f"タイトル抽出エラー: {md_path}, {e}")

        return Path(md_path).stem

    def update_old_resources_with_new(self, similar_resources: List[dict], new_md_path: str, new_title: str):
        """古い資料のMarkdownファイルに新しい資料へのリンクを追加"""
        if not similar_resources:
            return

        new_date = datetime.now().strftime('%Y年%m月')

        for res in similar_resources:
            try:
                with open(res['md_path'], 'r', encoding='utf-8') as f:
                    content = f.read()

                # 既に類似資料セクションがあるかチェック
                if '📚 **同じトピックの過去資料があります**' in content:
                    # 既存のセクションに追加
                    new_link = f"- [{new_title}]({Path(new_md_path).name}) ({new_date}) 【新着】\\n"

                    # セクションの終わり（---）の前に挿入
                    content = content.replace(
                        '- 最新の知見と比較することをお勧めします\n---',
                        f'{new_link}- 最新の知見と比較することをお勧めします\n---'
                    )
                else:
                    # 新規セクションを追加
                    new_section = f"""
---
📚 **同じトピックの新しい資料があります**

- [{new_title}]({Path(new_md_path).name}) ({new_date})
---

"""
                    # タイトルの後に挿入
                    lines = content.split('\n')
                    # 最初の空行を探して挿入
                    for i, line in enumerate(lines):
                        if line.strip() == '' and i > 0:
                            lines.insert(i + 1, new_section)
                            break

                    content = '\n'.join(lines)

                with open(res['md_path'], 'w', encoding='utf-8') as f:
                    f.write(content)

                logging.info(f"類似資料更新: {res['md_path']}")

            except Exception as e:
                logging.error(f"類似資料更新エラー: {res['md_path']}, {e}")
