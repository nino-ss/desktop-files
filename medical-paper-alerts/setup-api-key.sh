#!/bin/bash

# Claude APIキー環境変数設定スクリプト

echo "=========================================="
echo "Claude APIキー環境変数設定"
echo "=========================================="
echo ""

# APIキーの入力
echo "Anthropic Claude APIキーを入力してください（sk-ant-で始まる）:"
read -s api_key

if [ -z "$api_key" ]; then
    echo "エラー: APIキーが入力されていません"
    exit 1
fi

# 環境変数に設定
export ANTHROPIC_API_KEY="$api_key"

echo ""
echo "✓ 環境変数 ANTHROPIC_API_KEY を設定しました"
echo ""

# 設定確認
echo "設定確認:"
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "  → 未設定"
else
    key_length=${#ANTHROPIC_API_KEY}
    masked_key="${ANTHROPIC_API_KEY:0:10}...${ANTHROPIC_API_KEY: -4}"
    echo "  → 設定済み（${key_length}文字: ${masked_key}）"
fi

echo ""
echo "=========================================="
echo "使用方法:"
echo "=========================================="
echo ""
echo "1. この環境変数は現在のターミナルセッションでのみ有効です"
echo ""
echo "2. プログラムを実行:"
echo "   source venv/bin/activate"
echo "   python main.py --test --dry-run"
echo ""
echo "3. 永続的に設定する場合は、以下を実行:"
echo "   echo 'export ANTHROPIC_API_KEY=\"$api_key\"' >> ~/.zshrc"
echo "   source ~/.zshrc"
echo ""
