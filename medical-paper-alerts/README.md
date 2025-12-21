# 医学論文自動通知システム 📚

週2回、最新の医学論文（女性泌尿器科、女性性機能、一般性機能、骨盤底機能）を自動的に取得し、和訳・解説を付けて通知するシステムです。

## ✨ 主な機能

- 📖 **PubMed自動検索**: 専門分野に特化した論文を週2回自動取得
- 🎯 **スマートフィルタリング**: 5〜10本の高関連性論文を厳選
- 🇯🇵 **AI和訳・解説**: Claude AIによる専門的な日本語訳と臨床解説
- 📧 **マルチチャンネル通知**: メール、Slack、Discordに対応
- 💾 **分野別アーカイブ**: Markdown/JSON形式で保存、文献引用に活用可能
- 📊 **BibTeX対応**: 文献管理ソフトへの簡単インポート

## 🏗️ システム構成

```
medical-paper-alerts/
├── src/
│   ├── fetch_papers.py          # PubMed API論文取得
│   ├── filter_papers.py         # 論文フィルタリング・厳選
│   ├── translate_summarize.py   # Claude API和訳・解説
│   ├── storage.py               # ストレージ管理
│   └── notifier.py              # 通知システム
├── data/
│   ├── papers/                  # 論文データ（JSON）
│   │   ├── female_urology/
│   │   ├── female_sexual_function/
│   │   ├── general_sexual_function/
│   │   └── pelvic_floor/
│   └── summaries/               # 論文まとめ（Markdown）
├── config/
│   └── config.yaml              # 設定ファイル
├── .github/workflows/
│   └── paper-alerts.yml         # GitHub Actions自動実行
├── main.py                      # メインスクリプト
├── requirements.txt             # 依存パッケージ
└── README.md                    # このファイル
```

## 🚀 セットアップ

### 1. 必要な環境

- Python 3.10以上
- GitHub アカウント（自動実行の場合）
- 各種APIキー（下記参照）

### 2. インストール

```bash
cd medical-paper-alerts
pip install -r requirements.txt
```

### 3. 設定ファイルの編集

`config/config.yaml` を開き、以下を設定してください：

#### 必須設定

```yaml
# PubMed API（必須）
pubmed:
  email: "your-email@example.com"  # PubMed APIに必須

# Claude API（和訳・解説に必須）
claude_api:
  api_key: "your-anthropic-api-key"  # または環境変数 ANTHROPIC_API_KEY

# 通知方法（最低1つは有効化）
notification:
  methods:
    email:
      enabled: true
      recipients:
        - "your-email@example.com"
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      sender: "your-email@example.com"
      smtp_user: "your-email@example.com"
      # smtp_password は環境変数 SMTP_PASSWORD で設定
```

#### オプション設定

検索クエリや通知頻度、フィルタリング条件などはデフォルト値で動作しますが、
必要に応じてカスタマイズできます。

### 4. 環境変数の設定

機密情報は環境変数で設定することを推奨します：

```bash
# Claude API
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# メール（Gmailの場合はアプリパスワード）
export SMTP_PASSWORD="your-smtp-password"

# Slack（オプション）
export SLACK_WEBHOOK_URL="your-slack-webhook-url"

# Discord（オプション）
export DISCORD_WEBHOOK_URL="your-discord-webhook-url"
```

### 5. GitHub Secrets の設定（自動実行の場合）

GitHubリポジトリの Settings > Secrets and variables > Actions で以下を設定：

- `ANTHROPIC_API_KEY`
- `SMTP_PASSWORD`
- `SLACK_WEBHOOK_URL`（オプション）
- `DISCORD_WEBHOOK_URL`（オプション）

## 📝 使い方

### ローカル実行

#### 通常実行（通知あり）

```bash
cd medical-paper-alerts
python main.py
```

#### ドライラン（通知なし）

```bash
python main.py --dry-run
```

#### テストモード（少数の論文で動作確認）

```bash
python main.py --test
```

### 自動実行（GitHub Actions）

#### 自動スケジュール

- **月曜日 9:00 JST**: 自動実行
- **木曜日 9:00 JST**: 自動実行

#### 手動実行

1. GitHubリポジトリの「Actions」タブを開く
2. 「Medical Paper Alerts」ワークフローを選択
3. 「Run workflow」をクリック
4. オプションを選択して実行

## 📊 出力形式

### Markdown形式（論文まとめ）

`data/summaries/YYYYMMDD_論文まとめ.md`

各論文について以下の情報を含みます：

- 基本情報（タイトル、著者、ジャーナル、発行日）
- リンク（PubMed、DOI）
- 抄録（日本語訳）
- 専門家による解説
- 臨床への示唆
- キーポイント
- BibTeX引用情報

### JSON形式（論文データ）

`data/papers/{category}/YYYYMMDD_HHMMSS.json`

プログラムで利用可能な構造化データとして保存されます。

### 通知（メール/Slack/Discord）

厳選された論文の概要と、臨床への示唆を含む通知が送られます。

## 🔧 カスタマイズ

### 検索クエリの変更

`config/config.yaml` の `search_queries` セクションを編集：

```yaml
search_queries:
  female_urology:
    - "female urinary incontinence"
    - "pelvic organ prolapse"
    # 独自のクエリを追加
```

### フィルタリング条件の調整

```yaml
filtering:
  min_relevance_score: 0.6  # 関連性の最小スコア（0.0〜1.0）
  days_back: 7              # 過去何日分の論文を取得するか

selection:
  max_papers_per_notification: 8  # 1回の通知で送る論文数
  prioritize_high_impact: true    # 高インパクトジャーナルを優先
```

### 通知スケジュールの変更

`.github/workflows/paper-alerts.yml` の `cron` を編集：

```yaml
schedule:
  # 月曜日 9:00 JST (0:00 UTC)
  - cron: '0 0 * * 1'
  # 水曜日 9:00 JST (0:00 UTC)
  - cron: '0 0 * * 3'
  # 金曜日 9:00 JST (0:00 UTC)
  - cron: '0 0 * * 5'
```

## 📚 取得論文の分野

1. **女性泌尿器科** (female_urology)
   - 尿失禁、骨盤臓器脱、過活動膀胱など

2. **女性性機能** (female_sexual_function)
   - 女性性機能障害、性的興奮障害、性交痛など

3. **一般性機能** (general_sexual_function)
   - 性機能障害全般、勃起障害、早漏など

4. **骨盤底機能** (pelvic_floor)
   - 骨盤底筋トレーニング、骨盤底リハビリテーションなど

## 🤝 トラブルシューティング

### PubMed APIエラー

- `email` が正しく設定されているか確認
- API制限に達していないか確認（API keyの設定を推奨）

### Claude APIエラー

- `ANTHROPIC_API_KEY` が正しく設定されているか確認
- APIクレジットが十分か確認

### メール送信エラー

- Gmailの場合、「アプリパスワード」を使用
- 2段階認証を有効にし、アプリパスワードを生成
- SMTP設定が正しいか確認

### GitHub Actions実行エラー

- Secretsが正しく設定されているか確認
- ワークフローファイルの構文エラーがないか確認

## 📄 ライセンス

このプロジェクトは個人使用を目的としています。

## 🙏 謝辞

- [PubMed](https://pubmed.ncbi.nlm.nih.gov/) - 論文データ提供
- [Anthropic Claude](https://www.anthropic.com/) - AI和訳・解説
- [Biopython](https://biopython.org/) - PubMed API クライアント

## 📧 お問い合わせ

質問や問題がある場合は、GitHubのIssuesまでお願いします。

---

**注意**: このシステムは医学論文の情報提供を目的としており、医学的助言を提供するものではありません。
臨床判断は必ず専門医の判断に基づいて行ってください。
