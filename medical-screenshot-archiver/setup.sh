#!/bin/bash

# 医療スクリーンショット自動整理システム セットアップスクリプト

echo "=========================================="
echo "医療スクリーンショット自動整理システム"
echo "セットアップを開始します"
echo "=========================================="
echo ""

# 1. Python バージョンチェック
echo "1. Python バージョン確認..."
python3 --version

if [ $? -ne 0 ]; then
    echo "エラー: Python 3 がインストールされていません"
    exit 1
fi

# 2. 仮想環境作成
echo ""
echo "2. 仮想環境を作成中..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "エラー: 仮想環境の作成に失敗しました"
    exit 1
fi

# 3. 仮想環境を有効化
echo ""
echo "3. 仮想環境を有効化..."
source venv/bin/activate

# 4. 依存パッケージインストール
echo ""
echo "4. 依存パッケージをインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "エラー: パッケージのインストールに失敗しました"
    exit 1
fi

# 5. APIキー設定確認
echo ""
echo "5. APIキー設定確認..."

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "警告: ANTHROPIC_API_KEY 環境変数が設定されていません"
    echo ""
    echo "以下のコマンドでAPIキーを設定してください:"
    echo "  export ANTHROPIC_API_KEY=\"your-api-key-here\""
    echo ""
    echo "永続化する場合は ~/.zshrc または ~/.bashrc に追加してください:"
    echo "  echo 'export ANTHROPIC_API_KEY=\"your-api-key-here\"' >> ~/.zshrc"
    echo "  source ~/.zshrc"
else
    echo "APIキーが設定されています: ${ANTHROPIC_API_KEY:0:10}..."
fi

# 6. データベース初期化
echo ""
echo "6. データベースを初期化中..."
python src/main.py init

if [ $? -ne 0 ]; then
    echo "エラー: データベースの初期化に失敗しました"
    exit 1
fi

# 7. 必要なフォルダを作成
echo ""
echo "7. 必要なフォルダを作成中..."
mkdir -p ~/Desktop/Screenshots
mkdir -p ~/Desktop/医療スライド・論文作成資料

echo ""
echo "=========================================="
echo "セットアップ完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. APIキーを設定（まだの場合）"
echo "   export ANTHROPIC_API_KEY=\"your-api-key\""
echo ""
echo "2. 監視を開始"
echo "   python src/main.py start"
echo ""
echo "3. 使い方を確認"
echo "   README.md を参照してください"
echo ""
