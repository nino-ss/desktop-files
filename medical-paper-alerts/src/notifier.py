#!/usr/bin/env python3
"""
論文通知モジュール
メール、Slack、Discordで論文情報を通知します
"""

import os
import yaml
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from pathlib import Path
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class PaperNotifier:
    """論文情報を通知するクラス"""

    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self.notification_config = self.config.get('notification', {})

    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def send_email(
        self,
        papers_by_category: Dict[str, List[Dict]],
        markdown_path: Path = None
    ) -> bool:
        """
        メールで論文情報を送信

        Args:
            papers_by_category: カテゴリごとの論文リスト
            markdown_path: Markdownファイルのパス（添付用）

        Returns:
            送信成功の場合True
        """
        email_config = self.notification_config.get('methods', {}).get('email', {})

        if not email_config.get('enabled', False):
            logger.info("メール通知は無効です")
            return False

        try:
            # メール内容を生成
            subject = f"医学論文まとめ - {datetime.now().strftime('%Y年%m月%d日')}"
            body = self._generate_email_body(papers_by_category)

            # MIMEメッセージ作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config.get('sender', '')
            msg['To'] = ', '.join(email_config.get('recipients', []))

            # テキスト部分
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)

            # HTML部分
            html_body = self._generate_email_html(papers_by_category)
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)

            # SMTP送信
            smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = email_config.get('smtp_port', 587)
            smtp_user = email_config.get('smtp_user', email_config.get('sender', ''))
            smtp_password = os.getenv('SMTP_PASSWORD', email_config.get('smtp_password', ''))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                if smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"メール送信成功: {email_config.get('recipients')}")
            return True

        except Exception as e:
            logger.error(f"メール送信エラー: {e}")
            return False

    def _generate_email_body(self, papers_by_category: Dict[str, List[Dict]]) -> str:
        """
        メール本文（テキスト）を生成

        Args:
            papers_by_category: カテゴリごとの論文リスト

        Returns:
            メール本文
        """
        category_names_ja = {
            'female_urology': '女性泌尿器科',
            'female_sexual_function': '女性性機能',
            'general_sexual_function': '一般性機能',
            'pelvic_floor': '骨盤底機能'
        }

        body = f"医学論文まとめ - {datetime.now().strftime('%Y年%m月%d日')}\n\n"
        body += "=" * 60 + "\n\n"

        total_papers = sum(len(papers) for papers in papers_by_category.values())
        body += f"今週の新着論文: {total_papers}件\n\n"

        for category, papers in papers_by_category.items():
            if not papers:
                continue

            category_ja = category_names_ja.get(category, category)
            body += f"\n【{category_ja}】({len(papers)}件)\n"
            body += "-" * 60 + "\n\n"

            for i, paper in enumerate(papers, 1):
                body += f"{i}. {paper.get('japanese_title', paper.get('title', ''))}\n"
                body += f"   著者: {', '.join(paper.get('authors', [])[:3])}\n"
                body += f"   ジャーナル: {paper.get('journal', 'N/A')}\n"
                body += f"   PubMed: {paper.get('url', 'N/A')}\n"

                if paper.get('clinical_significance'):
                    body += f"   臨床への示唆: {paper['clinical_significance']}\n"

                body += "\n"

        body += "\n" + "=" * 60 + "\n"
        body += "詳細は添付のMarkdownファイルをご覧ください。\n"

        return body

    def _generate_email_html(self, papers_by_category: Dict[str, List[Dict]]) -> str:
        """
        メール本文（HTML）を生成

        Args:
            papers_by_category: カテゴリごとの論文リスト

        Returns:
            HTML形式のメール本文
        """
        category_names_ja = {
            'female_urology': '女性泌尿器科',
            'female_sexual_function': '女性性機能',
            'general_sexual_function': '一般性機能',
            'pelvic_floor': '骨盤底機能'
        }

        html = """
        <html>
        <head>
            <style>
                body { font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
                .category { margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #667eea; }
                .paper { margin: 15px 0; padding: 15px; background: white; border: 1px solid #e0e0e0; border-radius: 5px; }
                .paper-title { font-size: 16px; font-weight: bold; color: #667eea; margin-bottom: 10px; }
                .paper-meta { font-size: 13px; color: #666; margin: 5px 0; }
                .clinical-sig { background: #e8f5e9; padding: 10px; margin: 10px 0; border-radius: 3px; }
                a { color: #667eea; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
        """

        html += f"""
        <div class="header">
            <h1>📚 医学論文まとめ</h1>
            <p>{datetime.now().strftime('%Y年%m月%d日')}</p>
        </div>
        """

        total_papers = sum(len(papers) for papers in papers_by_category.values())
        html += f"<p style='text-align: center; font-size: 18px; margin: 20px;'>今週の新着論文: <strong>{total_papers}件</strong></p>"

        for category, papers in papers_by_category.items():
            if not papers:
                continue

            category_ja = category_names_ja.get(category, category)
            html += f"""
            <div class="category">
                <h2>{category_ja} ({len(papers)}件)</h2>
            """

            for i, paper in enumerate(papers, 1):
                html += f"""
                <div class="paper">
                    <div class="paper-title">{i}. {paper.get('japanese_title', paper.get('title', ''))}</div>
                    <div class="paper-meta">📝 著者: {', '.join(paper.get('authors', [])[:3])}</div>
                    <div class="paper-meta">📖 ジャーナル: {paper.get('journal', 'N/A')}</div>
                    <div class="paper-meta">🔗 <a href="{paper.get('url', '#')}">PubMed</a>
                """

                if paper.get('doi_url'):
                    html += f""" | <a href="{paper['doi_url']}">DOI</a>"""

                html += "</div>"

                if paper.get('clinical_significance'):
                    html += f"""
                    <div class="clinical-sig">
                        <strong>💡 臨床への示唆:</strong> {paper['clinical_significance']}
                    </div>
                    """

                html += "</div>"

            html += "</div>"

        html += """
        </body>
        </html>
        """

        return html

    def send_slack(
        self,
        papers_by_category: Dict[str, List[Dict]]
    ) -> bool:
        """
        Slackで論文情報を送信

        Args:
            papers_by_category: カテゴリごとの論文リスト

        Returns:
            送信成功の場合True
        """
        slack_config = self.notification_config.get('methods', {}).get('slack', {})

        if not slack_config.get('enabled', False):
            logger.info("Slack通知は無効です")
            return False

        webhook_url = slack_config.get('webhook_url') or os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.error("Slack webhook URLが設定されていません")
            return False

        try:
            # Slackメッセージを生成
            message = self._generate_slack_message(papers_by_category)

            # Webhook送信
            response = requests.post(
                webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                logger.info("Slack送信成功")
                return True
            else:
                logger.error(f"Slack送信エラー: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Slack送信エラー: {e}")
            return False

    def _generate_slack_message(self, papers_by_category: Dict[str, List[Dict]]) -> dict:
        """
        Slackメッセージを生成

        Args:
            papers_by_category: カテゴリごとの論文リスト

        Returns:
            Slackメッセージ（JSON）
        """
        category_names_ja = {
            'female_urology': '女性泌尿器科',
            'female_sexual_function': '女性性機能',
            'general_sexual_function': '一般性機能',
            'pelvic_floor': '骨盤底機能'
        }

        total_papers = sum(len(papers) for papers in papers_by_category.values())

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📚 医学論文まとめ - {datetime.now().strftime('%Y年%m月%d日')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*今週の新着論文: {total_papers}件*"
                }
            },
            {"type": "divider"}
        ]

        for category, papers in papers_by_category.items():
            if not papers:
                continue

            category_ja = category_names_ja.get(category, category)

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{category_ja}* ({len(papers)}件)"
                }
            })

            for i, paper in enumerate(papers[:3], 1):  # 最初の3件のみ
                paper_text = f"*{i}. {paper.get('japanese_title', paper.get('title', ''))}*\n"
                paper_text += f"📝 {', '.join(paper.get('authors', [])[:2])}\n"
                paper_text += f"📖 {paper.get('journal', 'N/A')}\n"
                paper_text += f"🔗 <{paper.get('url', '#')}|PubMed>"

                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": paper_text
                    }
                })

            if len(papers) > 3:
                blocks.append({
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": f"他 {len(papers) - 3}件の論文があります"
                    }]
                })

            blocks.append({"type": "divider"})

        return {"blocks": blocks}

    def send_discord(
        self,
        papers_by_category: Dict[str, List[Dict]]
    ) -> bool:
        """
        Discordで論文情報を送信

        Args:
            papers_by_category: カテゴリごとの論文リスト

        Returns:
            送信成功の場合True
        """
        discord_config = self.notification_config.get('methods', {}).get('discord', {})

        if not discord_config.get('enabled', False):
            logger.info("Discord通知は無効です")
            return False

        webhook_url = discord_config.get('webhook_url') or os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            logger.error("Discord webhook URLが設定されていません")
            return False

        try:
            # Discordメッセージを生成
            message = self._generate_discord_message(papers_by_category)

            # Webhook送信
            response = requests.post(
                webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 204:
                logger.info("Discord送信成功")
                return True
            else:
                logger.error(f"Discord送信エラー: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Discord送信エラー: {e}")
            return False

    def _generate_discord_message(self, papers_by_category: Dict[str, List[Dict]]) -> dict:
        """
        Discordメッセージを生成

        Args:
            papers_by_category: カテゴリごとの論文リスト

        Returns:
            Discordメッセージ（JSON）
        """
        category_names_ja = {
            'female_urology': '女性泌尿器科',
            'female_sexual_function': '女性性機能',
            'general_sexual_function': '一般性機能',
            'pelvic_floor': '骨盤底機能'
        }

        total_papers = sum(len(papers) for papers in papers_by_category.values())

        embeds = []

        # ヘッダー
        embeds.append({
            "title": f"📚 医学論文まとめ - {datetime.now().strftime('%Y年%m月%d日')}",
            "description": f"今週の新着論文: **{total_papers}件**",
            "color": 6733034  # 紫色
        })

        for category, papers in papers_by_category.items():
            if not papers:
                continue

            category_ja = category_names_ja.get(category, category)

            for i, paper in enumerate(papers[:3], 1):  # 最初の3件のみ
                fields = [
                    {
                        "name": "著者",
                        "value": ", ".join(paper.get('authors', [])[:3]),
                        "inline": True
                    },
                    {
                        "name": "ジャーナル",
                        "value": paper.get('journal', 'N/A'),
                        "inline": True
                    }
                ]

                if paper.get('clinical_significance'):
                    fields.append({
                        "name": "💡 臨床への示唆",
                        "value": paper['clinical_significance'][:200],
                        "inline": False
                    })

                embeds.append({
                    "title": f"{category_ja} - {i}. {paper.get('japanese_title', paper.get('title', ''))[:100]}",
                    "url": paper.get('url', ''),
                    "fields": fields,
                    "color": 3447003  # 青色
                })

        return {"embeds": embeds[:10]}  # Discordは最大10個のembedまで

    def notify_all(
        self,
        papers_by_category: Dict[str, List[Dict]],
        markdown_path: Path = None
    ) -> Dict[str, bool]:
        """
        全ての有効な通知方法で送信

        Args:
            papers_by_category: カテゴリごとの論文リスト
            markdown_path: Markdownファイルのパス

        Returns:
            通知方法ごとの成功/失敗
        """
        results = {}

        # メール
        results['email'] = self.send_email(papers_by_category, markdown_path)

        # Slack
        results['slack'] = self.send_slack(papers_by_category)

        # Discord
        results['discord'] = self.send_discord(papers_by_category)

        return results


def main():
    """メイン関数"""
    from pathlib import Path

    # 設定ファイルのパス
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    # 通知者初期化
    notifier = PaperNotifier(str(config_path))

    # サンプルデータ
    sample_papers = {
        'female_urology': [
            {
                'pmid': '12345678',
                'title': 'Novel treatments for urinary incontinence',
                'japanese_title': '尿失禁の新しい治療法',
                'authors': ['Smith J', 'Johnson A'],
                'journal': 'International Urogynecology Journal',
                'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/',
                'clinical_significance': '日常診療において患者選択の際に有用な情報を提供します'
            }
        ]
    }

    # 通知送信
    results = notifier.notify_all(sample_papers)

    print("=== 通知結果 ===")
    for method, success in results.items():
        status = "✓ 成功" if success else "✗ 失敗"
        print(f"{method}: {status}")


if __name__ == "__main__":
    main()
