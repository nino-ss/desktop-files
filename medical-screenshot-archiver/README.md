# 医療スクリーンショット自動整理システム (MedScreenArchiver)

医療スライド・論文作成のためのスクリーンショットを自動的に解析し、テキストデータとして整理・検索可能な形で保存するシステムです。

## 主な機能

- **スクリーンショットの自動検知と解析**: ファイル監視で新規画像を自動検出
- **AIによる内容の自動分類**: Claude APIによる画像解析とカテゴリ自動判定
- **患者個人情報の自動マスキング**: 氏名・生年月日・ID等を自動検出して削除（性別・年齢のみ保持）
- **フルテキスト検索**: 内容全体から高速検索
- **類似資料の通知**: 同一キーワードの古い資料を自動検出
- **出典情報の自動抽出**: 学会名、論文タイトル、著者、発表年などを抽出

## セットアップ

### 1. 環境構築

```bash
# プロジェクトディレクトリに移動
cd ~/Desktop/medical-screenshot-archiver

# 仮想環境作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt
```

### 2. API キー設定

Claude APIキーを環境変数に設定します。

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

永続化する場合は、`~/.zshrc` または `~/.bashrc` に追加してください。

```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. 設定ファイル編集

`config/config.yaml` を必要に応じて編集します。

```yaml
monitor:
  watch_folder: "~/Desktop/Screenshots"  # 監視するフォルダ

storage:
  base_folder: "~/Desktop/医療スライド・論文作成資料"  # 保存先フォルダ
```

### 4. データベース初期化

```bash
python src/main.py init
```

## 使い方

### 監視の開始

```bash
python src/main.py start
```

監視が開始されると、指定したフォルダにスクリーンショットを保存するだけで自動的に処理されます。

**処理フロー:**
1. スクリーンショットを取得
2. 5秒待機（複数枚の連続撮影に対応）
3. 自動で画像解析・個人情報マスキング・分類・保存
4. macOS通知で完了を通知
5. 画像は一時フォルダに保存され、手動で保存/削除を判断

### 検索

#### 全文検索

```bash
python src/main.py search "GSM エストロゲン"
```

#### カテゴリ絞り込み

```bash
python src/main.py search "骨盤底筋" --category "婦人科/GSM関連"
```

#### 日付範囲指定

```bash
python src/main.py search --from-date 2025-01-01 --to-date 2025-12-31
```

#### 要確認情報のみ

```bash
python src/main.py search --needs-review
```

### 画像管理

#### 一時フォルダの画像一覧

```bash
python src/main.py list-temp
```

#### 画像を保存

```bash
python src/main.py save-image <record_id>
```

#### 画像を削除

```bash
python src/main.py delete-image <record_id>
```

## ディレクトリ構成

```
medical-screenshot-archiver/
├── src/
│   ├── main.py              # エントリーポイント
│   ├── monitor.py           # ファイル監視
│   ├── analyzer.py          # 画像解析（Claude API）
│   ├── privacy.py           # 個人情報マスキング
│   ├── classifier.py        # 自動分類
│   ├── database.py          # DB操作
│   ├── similar_detector.py  # 類似資料検出
│   ├── image_manager.py     # 画像管理
│   └── utils.py             # ユーティリティ
├── config/
│   └── config.yaml          # 設定ファイル
├── data/
│   └── medical_terms.json   # 医学用語辞書
├── logs/                    # ログファイル
├── requirements.txt
└── README.md
```

## 保存データの構成

### Markdownファイル

```
~/Desktop/医療スライド・論文作成資料/
├── 婦人科/
│   ├── GSM関連/
│   │   ├── 20251228_GSM治療ガイドライン.md
│   │   └── 20251225_エストロゲン療法.md
│   ├── 骨盤臓器脱/
│   └── 更年期障害/
├── 産科/
├── 泌尿器科/
├── 一般/
├── _archives/
│   └── images/              # 保存した画像
└── screenshots.db           # 検索用データベース
```

### Markdownファイルの構造

```markdown
# GSM治療ガイドライン - 20251228

**取得日時**: 2025-12-28 14:30:00
**カテゴリ**: 婦人科/GSM関連
**出典**: 第XX回日本婦人科学会 (2024)
**症例情報**: 女性、65歳
**キーワード**: #GSM #エストロゲン #骨盤底筋
**画像保存**: なし

---
📚 **同じトピックの過去資料があります**

- [エストロゲン療法.md](20251225_エストロゲン療法.md) (2023年12月)
- 最新の知見と比較することをお勧めします
---

## 要約

閉経後のGSM（閉経後性器尿路症候群）に対するエストロゲン療法の有効性について...

---

## 内容

[AIが抽出した全文テキスト（個人情報マスキング済み）]

---

## 視覚要素

BMIと骨密度の相関を示す散布図。BMI 18-25の範囲で骨密度が最も高い傾向。

---

## メモ

<!-- ここに手動でメモを追記できます -->
```

## セキュリティとプライバシー

### 個人情報保護

- **自動マスキング**: AIとパターンマッチングで患者情報を自動検出・削除
- **保持データ**: 性別と年齢のみ保持
- **削除対象**: 氏名、生年月日、患者ID、住所、電話番号など

### API利用

- ローカル処理を基本とし、画像解析時のみClaude APIを使用
- APIキーは環境変数で管理（設定ファイルには記載しない）

## トラブルシューティング

### 監視が開始されない

- 監視フォルダのパスを確認してください
- 権限エラーの場合は、フォルダの読み取り権限を確認

### API エラー

```
ValueError: ANTHROPIC_API_KEY環境変数が設定されていません
```

→ 環境変数が正しく設定されているか確認してください

```bash
echo $ANTHROPIC_API_KEY
```

### 画像解析エラー

- 画像ファイルが破損していないか確認
- API利用上限に達していないか確認
- ログファイル（`logs/`）を確認

## 開発情報

### 依存パッケージ

- anthropic: Claude API クライアント
- watchdog: ファイルシステム監視
- click: CLI インターフェース
- PyYAML: 設定ファイル読み込み
- Pillow: 画像処理
- tenacity: リトライロジック

### ログ

ログファイルは `logs/` ディレクトリに日付別で保存されます。

```
logs/medscreen_20251228.log
```

### API使用量の目安

- 1画像あたり: 約1500トークン（入力） + 1000トークン（出力）
- 1日10枚の場合: 月間約$15-30（Claude 3.5 Sonnet使用時）

## バックグラウンド実行（オプション）

launchdを使ってmacOSで自動起動する場合:

`~/Library/LaunchAgents/com.medscreen.archiver.plist` を作成:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.medscreen.archiver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/src/main.py</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_API_KEY</key>
        <string>your-api-key</string>
    </dict>
</dict>
</plist>
```

起動:

```bash
launchctl load ~/Library/LaunchAgents/com.medscreen.archiver.plist
```

停止:

```bash
launchctl unload ~/Library/LaunchAgents/com.medscreen.archiver.plist
```

## ライセンス

このプロジェクトは個人利用を目的としています。

## 作成者

Dr. Ninomiya

## サポート

問題が発生した場合は、ログファイルを確認するか、設定を見直してください。
