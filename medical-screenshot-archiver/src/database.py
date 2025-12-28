"""
データベース管理モジュール
SQLiteデータベースの管理、Markdownファイルの生成、検索機能を提供
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    """データベース管理クラス"""

    def __init__(self, config: dict):
        self.config = config
        self.base_folder = Path(config['storage']['base_folder']).expanduser()
        self.db_path = self.base_folder / 'screenshots.db'

    def initialize(self):
        """データベース初期化"""
        self.base_folder.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # メインテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                md_path TEXT NOT NULL,
                image_path TEXT,
                created_at DATETIME NOT NULL,
                category TEXT,
                keywords TEXT,
                source_info TEXT,
                case_info TEXT,
                summary TEXT,
                needs_review BOOLEAN DEFAULT 0,
                has_similar_old BOOLEAN DEFAULT 0,
                last_updated DATETIME
            )
        ''')

        # 全文検索テーブル
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS screenshots_fts
            USING fts5(
                content,
                tokenize = 'unicode61'
            )
        ''')

        # インデックス作成
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category
            ON screenshots(category)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON screenshots(created_at)
        ''')

        conn.commit()
        conn.close()

        logging.info(f"データベース初期化完了: {self.db_path}")

    def save(self, analysis_result: dict, category: str,
             similar_resources: List[dict], classifier) -> int:
        """解析結果を保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Markdownファイル生成
            md_path = classifier.get_save_path(
                category,
                analysis_result['title'],
                datetime.now()
            )

            md_content = self._generate_markdown(
                analysis_result,
                category,
                similar_resources
            )

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # データベースに保存
            cursor.execute('''
                INSERT INTO screenshots (
                    file_path, md_path, image_path, created_at, category,
                    keywords, source_info, case_info, summary,
                    has_similar_old, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_result['original_image_path'],
                str(md_path),
                None,  # 画像は後で手動で保存
                datetime.now().isoformat(),
                category,
                json.dumps(analysis_result.get('keywords', []), ensure_ascii=False),
                json.dumps(analysis_result.get('source', {}), ensure_ascii=False),
                json.dumps(analysis_result.get('case_info', {}), ensure_ascii=False),
                analysis_result.get('summary', ''),
                len(similar_resources) > 0,
                datetime.now().isoformat()
            ))

            record_id = cursor.lastrowid

            # 全文検索テーブルに追加
            cursor.execute('''
                INSERT INTO screenshots_fts (rowid, content)
                VALUES (?, ?)
            ''', (
                record_id,
                analysis_result.get('full_text', '')
            ))

            conn.commit()
            logging.info(f"保存完了: {md_path} (ID: {record_id})")

            return record_id

        except Exception as e:
            conn.rollback()
            logging.error(f"保存エラー: {e}")
            raise

        finally:
            conn.close()

    def _generate_markdown(self, analysis_result: dict, category: str,
                          similar_resources: List[dict]) -> str:
        """Markdownファイルを生成"""
        # 類似資料セクション
        similar_section = ""
        if similar_resources:
            similar_section = "\n---\n📚 **同じトピックの過去資料があります**\n\n"
            for res in similar_resources:
                res_date = datetime.fromisoformat(res['created_at']).strftime('%Y年%m月')
                # 相対パスを計算
                res_md_path = Path(res['md_path'])
                rel_path = res_md_path.name  # 同じカテゴリ内なら相対パス不要
                similar_section += f"- [{res['title']}]({rel_path}) ({res_date})\n"
            similar_section += "- 最新の知見と比較することをお勧めします\n---\n"

        # ソース情報
        source = analysis_result.get('source', {})
        source_text = "不明"
        if source and source.get('type'):
            if source['type'] == '学会':
                source_text = f"{source.get('conference_name', '')} ({source.get('year', '')})"
            elif source['type'] == '論文':
                source_text = f"{source.get('paper_title', '')} ({source.get('year', '')})"
            else:
                source_text = source.get('source_text', '不明')

        # 症例情報
        case_info = analysis_result.get('case_info', {})
        case_text = f"{case_info.get('gender', '不明')}、{case_info.get('age', '不明')}歳"

        # キーワード
        keywords_text = ' '.join(['#' + kw for kw in analysis_result.get('keywords', [])])

        # Markdown構築
        md_content = f"""# {analysis_result.get('title', '無題')}

**取得日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**カテゴリ**: {category}
**出典**: {source_text}
**症例情報**: {case_text}
**キーワード**: {keywords_text}
**画像保存**: なし

{similar_section}

## 要約

{analysis_result.get('summary', '')}

---

## 内容

{analysis_result.get('full_text', '')}

---

## 視覚要素

{analysis_result.get('visual_elements', {}).get('description', '特になし')}

---

## メモ

<!-- ここに手動でメモを追記できます -->

"""

        return md_content

    def search(self, query: str = "", filters: dict = None) -> List[dict]:
        """検索"""
        if filters is None:
            filters = {}

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # ベースクエリ
            if query:
                sql = """
                    SELECT s.*, fts.content
                    FROM screenshots s
                    INNER JOIN screenshots_fts fts ON s.id = fts.rowid
                    WHERE fts.content MATCH ?
                """
                params = [query]
            else:
                sql = """
                    SELECT *
                    FROM screenshots
                    WHERE 1=1
                """
                params = []

            # カテゴリフィルタ
            if filters.get('category'):
                sql += " AND category = ?"
                params.append(filters['category'])

            # 日付範囲フィルタ
            if filters.get('from_date'):
                sql += " AND created_at >= ?"
                params.append(filters['from_date'])

            if filters.get('to_date'):
                sql += " AND created_at <= ?"
                params.append(filters['to_date'])

            # 要確認フラグ
            if filters.get('needs_review'):
                sql += " AND needs_review = 1"

            # 並び順
            sql += " ORDER BY created_at DESC"

            # 制限
            if filters.get('limit'):
                sql += f" LIMIT {int(filters['limit'])}"

            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]

            return results

        finally:
            conn.close()

    def update_image_path(self, record_id: int, image_path: str):
        """画像パスを更新"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE screenshots
                SET image_path = ?, last_updated = ?
                WHERE id = ?
            ''', (image_path, datetime.now().isoformat(), record_id))

            # Markdownファイルも更新
            cursor.execute('SELECT md_path FROM screenshots WHERE id = ?', (record_id,))
            result = cursor.fetchone()

            if result:
                md_path = result[0]

                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 画像保存ステータス更新
                content = content.replace('**画像保存**: なし', '**画像保存**: あり')

                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            conn.commit()
            logging.info(f"画像パス更新完了: ID={record_id}")

        except Exception as e:
            conn.rollback()
            logging.error(f"画像パス更新エラー: {e}")
            raise

        finally:
            conn.close()

    def get_record_by_id(self, record_id: int) -> Optional[dict]:
        """IDでレコードを取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM screenshots WHERE id = ?', (record_id,))
            result = cursor.fetchone()

            if result:
                return dict(result)
            return None

        finally:
            conn.close()
