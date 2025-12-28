#!/bin/bash

# 外出先のClaudeブランチをideaブランチに同期するスクリプト
# 使用方法: ./sync-claude-to-idea.sh [claudeブランチ名]
# 例: ./sync-claude-to-idea.sh claude/create-dated-file-aXJQT

set -e  # エラーが発生したらスクリプトを終了

# 色付きメッセージ用の関数
print_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[0;33m[WARNING]\033[0m $1"
}

# リモートのClaudeブランチをリスト表示する関数
list_claude_branches() {
    print_info "利用可能なClaudeブランチ:"
    git branch -r | grep "origin/claude/" | sed 's|origin/||' | sed 's/^/  - /'
    echo ""
    print_info "使用方法: ./sync-claude-to-idea.sh <ブランチ名>"
    print_info "例: ./sync-claude-to-idea.sh claude/create-dated-file-aXJQT"
}

# ブランチ名が指定されていない場合、利用可能なブランチを表示
if [ -z "$1" ]; then
    print_warning "ブランチ名が指定されていません。"
    echo ""
    list_claude_branches
    exit 0
fi

CLAUDE_BRANCH="$1"
REMOTE_BRANCH="origin/${CLAUDE_BRANCH}"

print_info "Claudeブランチ '${CLAUDE_BRANCH}' をideaブランチに同期します..."

# 1. リモートの最新情報を取得
print_info "リモートの最新情報を取得しています..."
git fetch origin

# 2. リモートブランチが存在するか確認
if ! git show-ref --verify --quiet refs/remotes/${REMOTE_BRANCH}; then
    print_error "リモートブランチ '${REMOTE_BRANCH}' が見つかりません。"
    echo ""
    list_claude_branches
    exit 1
fi

# 3. 現在のブランチを保存
CURRENT_BRANCH=$(git branch --show-current)

# 4. ideaブランチに切り替え（既にideaブランチにいる場合はスキップ）
if [ "${CURRENT_BRANCH}" != "idea" ]; then
    print_info "ideaブランチに切り替えています..."
    git checkout idea
else
    print_info "既にideaブランチにいます。"
fi

# 5. ideaブランチを最新の状態に更新
print_info "ideaブランチを最新の状態に更新しています..."
git pull origin idea 2>/dev/null || print_warning "リモートのideaブランチがないか、pullできませんでした。"

# 6. Claudeブランチをideaブランチにマージ
print_info "Claudeブランチ '${REMOTE_BRANCH}' をideaブランチにマージしています..."
if git merge "${REMOTE_BRANCH}" --no-edit; then
    print_info "マージが正常に完了しました！"
    
    # 7. リモートにpushするか確認
    echo ""
    read -p "リモートのideaブランチにpushしますか？ (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "リモートのideaブランチにpushしています..."
        git push origin idea
        print_info "pushが完了しました！"
    else
        print_info "pushをスキップしました。後で手動でpushできます。"
    fi
else
    print_error "マージ中にコンフリクトが発生しました。"
    print_info "コンフリクトを解決してから、以下のコマンドで続行してください:"
    echo "  git add ."
    echo "  git commit"
    echo "  git push origin idea"
    exit 1
fi

print_info "同期が完了しました！"
