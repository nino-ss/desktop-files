# ファイル変換スクリプト

PDF、Word（.docx）、PagesファイルをMarkdownに一括変換するスクリプトです。

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements-convert.txt
```

または個別にインストール：

```bash
pip install PyMuPDF mammoth python-docx
```

### 2. スクリプトに実行権限を付与（オプション）

```bash
chmod +x convert_to_markdown.py
```

## 使用方法

### 基本的な使い方

```bash
# デスクトップ全体を再帰的に変換
python convert_to_markdown.py /Users/ninomiya/Desktop

# カレントディレクトリを変換
python convert_to_markdown.py

# 特定のディレクトリのみ変換
python convert_to_markdown.py /Users/ninomiya/Desktop/AI
```

### オプション

```bash
# 出力ディレクトリを指定（すべてのMarkdownファイルを1箇所に集約）
python convert_to_markdown.py /Users/ninomiya/Desktop --output ./markdown_output

# 既存のMarkdownファイルを上書き
python convert_to_markdown.py /Users/ninomiya/Desktop --overwrite

# 特定のファイルタイプのみ変換
python convert_to_markdown.py /Users/ninomiya/Desktop --extensions pdf docx
```

## 変換の仕組み

- **PDF**: PyMuPDFを使用してテキストを抽出し、Markdownに変換
- **Word (.docx)**: mammothライブラリを使用（フォールバックとしてpython-docxも使用可能）
- **Pages**: macOSの`textutil`コマンドを使用してテキストに変換

## 注意事項

1. **Pagesファイル**: macOSの`textutil`コマンドを使用するため、macOSでのみ動作します
2. **既存ファイル**: デフォルトでは既存のMarkdownファイルはスキップされます。`--overwrite`オプションで上書き可能
3. **出力場所**: `--output`オプションを指定しない場合、元のファイルと同じディレクトリに`.md`ファイルが作成されます
4. **大量のファイル**: 変換には時間がかかる場合があります。特にPDFは処理が重いです

## 効率的な変換手順の推奨

1. **まず小規模でテスト**：
   ```bash
   python convert_to_markdown.py /Users/ninomiya/Desktop/AI
   ```

2. **問題がなければ全体を変換**：
   ```bash
   python convert_to_markdown.py /Users/ninomiya/Desktop
   ```

3. **出力を別ディレクトリに集約したい場合**：
   ```bash
   python convert_to_markdown.py /Users/ninomiya/Desktop --output ~/Desktop/markdown_files
   ```

## トラブルシューティング

### ライブラリがインストールできない場合

```bash
# pipをアップグレード
pip install --upgrade pip

# 個別にインストールを試す
pip install PyMuPDF
pip install mammoth
pip install python-docx
```

### Pagesファイルが変換できない場合

- PagesファイルはmacOSでのみ変換可能です
- 手動でPagesをWordやPDFにエクスポートしてから変換することも可能です

### メモリエラーが発生する場合

- 大きなPDFファイルはメモリを多く使用します
- 特定のディレクトリに分けて変換することをお勧めします
