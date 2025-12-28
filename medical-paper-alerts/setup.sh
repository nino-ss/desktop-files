#!/bin/bash

# 医学論文自動通知システム - セットアップスクリプト

echo "=================================="
echo "医学論文自動通知システム セットアップ"
echo "=================================="
echo ""

# Pythonバージョンチェック
echo "[1/5] Pythonバージョンチェック..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✓ Python $python_version が検出されました"
else
    echo "✗ Python $required_version 以上が必要です（現在: $python_version）"
    exit 1
fi
echo ""

# 仮想環境の作成
echo "[2/5] Python仮想環境の作成..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 仮想環境を作成しました"
else
    echo "✓ 仮想環境は既に存在します"
fi
echo ""

# 仮想環境の有効化
echo "[3/5] 仮想環境の有効化..."
source venv/bin/activate
echo "✓ 仮想環境を有効化しました"
echo ""

# 依存パッケージのインストール
echo "[4/5] 依存パッケージのインストール..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ 依存パッケージをインストールしました"
echo ""

# ディレクトリ構造の作成
echo "[5/5] 必要なディレクトリの作成..."
mkdir -p logs
mkdir -p data/papers/female_urology
mkdir -p data/papers/female_sexual_function
mkdir -p data/papers/general_sexual_function
mkdir -p data/papers/pelvic_floor
mkdir -p data/summaries
echo "✓ ディレクトリを作成しました"
echo ""

echo "=================================="
echo "セットアップ完了！"
echo "=================================="
echo ""
echo "次のステップ:"
echo ""
echo "1. config/config.yaml を編集して、以下を設定してください："
echo "   - PubMed API用のメールアドレス"
echo "   - 通知先のメールアドレス"
echo ""
echo "2. 環境変数を設定してください："
echo "   export ANTHROPIC_API_KEY='your-api-key'"
echo "   export SMTP_PASSWORD='your-smtp-password'"
echo ""
echo "3. テスト実行:"
echo "   python main.py --test"
echo ""
echo "4. 通常実行:"
echo "   python main.py"
echo ""
echo "詳細はREADME.mdをご覧ください。"
