# クイックスタートガイド 🚀

このガイドに従って、5分で医学論文自動通知システムを始めましょう！

## ⚡ 最速セットアップ（5分）

### ステップ1: セットアップスクリプト実行

```bash
cd medical-paper-alerts
./setup.sh
```

これで以下が自動的に行われます：
- Python仮想環境の作成
- 必要なパッケージのインストール
- ディレクトリ構造の作成

### ステップ2: APIキーの取得

#### Claude API キー（必須）

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. APIキーを作成
3. キーをコピー

#### Gmail アプリパスワード（メール通知の場合）

1. Googleアカウントの2段階認証を有効化
2. [アプリパスワード](https://myaccount.google.com/apppasswords)にアクセス
3. 「メール」用のアプリパスワードを生成
4. 16桁のパスワードをコピー

### ステップ3: 設定ファイル編集

`config/config.yaml` を開き、以下を編集：

```yaml
# 1. メールアドレス設定（必須）
pubmed:
  email: "your-email@example.com"  # ← あなたのメールアドレス

# 2. 通知設定（必須）
notification:
  methods:
    email:
      enabled: true
      recipients:
        - "your-email@example.com"  # ← 通知先メールアドレス
      sender: "your-email@example.com"  # ← 送信元メールアドレス
      smtp_user: "your-email@example.com"  # ← Gmailアドレス
```

### ステップ4: 環境変数設定

```bash
# Claude API キー
export ANTHROPIC_API_KEY='sk-ant-xxxxx'

# Gmail アプリパスワード
export SMTP_PASSWORD='xxxx xxxx xxxx xxxx'
```

または、`.env` ファイルを作成：

```bash
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-xxxxx
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EOF
```

そして以下を実行：

```bash
source .env
```

### ステップ5: テスト実行

```bash
# 仮想環境を有効化
source venv/bin/activate

# テストモードで実行（少数の論文のみ、通知なし）
python main.py --test --dry-run
```

成功すれば、`data/summaries/` に Markdown ファイルが生成されます！

### ステップ6: 通常実行

```bash
# 通知ありで実行
python main.py
```

これで最新の論文まとめがメールで届きます！🎉

## 📅 自動実行の設定（GitHub Actions）

### 1. GitHubリポジトリにプッシュ

```bash
cd medical-paper-alerts
git init
git add .
git commit -m "Initial commit: Medical paper alerts system"
git remote add origin https://github.com/yourusername/medical-paper-alerts.git
git push -u origin main
```

### 2. GitHub Secrets 設定

1. GitHubリポジトリページを開く
2. Settings > Secrets and variables > Actions
3. 「New repository secret」をクリック
4. 以下のSecretを追加：

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | Claude APIキー |
| `SMTP_PASSWORD` | Gmailアプリパスワード |

### 3. GitHub Actions 有効化

1. リポジトリの「Actions」タブを開く
2. 「I understand my workflows, go ahead and enable them」をクリック

### 4. 自動実行の確認

- **月曜日 9:00 JST**: 自動実行
- **木曜日 9:00 JST**: 自動実行

手動実行も可能：
1. 「Actions」タブ > 「Medical Paper Alerts」
2. 「Run workflow」をクリック

## 🎯 カスタマイズ例

### 週3回に変更

`.github/workflows/paper-alerts.yml` を編集：

```yaml
schedule:
  - cron: '0 0 * * 1'  # 月曜日
  - cron: '0 0 * * 3'  # 水曜日
  - cron: '0 0 * * 5'  # 金曜日
```

### 論文数を10件に変更

`config/config.yaml` を編集：

```yaml
selection:
  max_papers_per_notification: 10
```

### 検索期間を14日に変更

```yaml
filtering:
  days_back: 14
```

## 💡 よくある質問

### Q: 論文が1件も取得できません

A: 以下を確認してください：
- PubMedのメールアドレスが設定されているか
- インターネット接続が正常か
- `days_back` の設定（過去7日で論文がない場合は14日に変更）

### Q: Claude APIエラーが出ます

A: 以下を確認してください：
- `ANTHROPIC_API_KEY` が正しく設定されているか
- APIクレジットが十分にあるか
- モデル名が正しいか（`claude-sonnet-4-5-20250929`）

### Q: メールが送信されません

A: 以下を確認してください：
- Gmailの2段階認証が有効か
- アプリパスワードを使用しているか（通常のパスワードではNG）
- `SMTP_PASSWORD` が正しく設定されているか

### Q: GitHub Actions が失敗します

A: 以下を確認してください：
- Secrets が正しく設定されているか（スペースなど注意）
- ワークフローファイルの構文が正しいか
- Actionsタブでエラーログを確認

## 🔄 定期的なメンテナンス

### 依存パッケージの更新（月1回推奨）

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### ログの確認

```bash
# 最新のログを確認
tail -n 100 logs/$(ls -t logs/ | head -n1)
```

### 古いデータの整理

```bash
# 90日以前のJSONを削除
find data/papers -name "*.json" -mtime +90 -delete

# 180日以前のMarkdownを削除
find data/summaries -name "*.md" -mtime +180 -delete
```

## 📞 サポート

問題が解決しない場合は、GitHubのIssuesで質問してください。

---

**おめでとうございます！🎉**

これで医学論文自動通知システムが稼働しています。
週2回、最新の論文情報が自動的に届くようになりました！
