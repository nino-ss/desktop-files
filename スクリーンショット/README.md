# スクリーンショット文字抽出ツール

このツールは、スクリーンショット画像ファイルから文字情報を抽出（OCR）するためのPythonスクリプトです。

## 必要な環境

### 1. Pythonライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. Tesseract OCRのインストール

#### macOS
```bash
brew install tesseract tesseract-lang
```

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-jpn
```

#### Windows
1. https://github.com/UB-Mannheim/tesseract/wiki からインストーラーをダウンロード
2. インストール時に「Japanese」言語パックを選択

## 使い方

```bash
python ocr_extract.py
```

スクリプトを実行すると、同じディレクトリ内のすべてのPNG画像ファイルから文字を抽出し、以下のファイルに結果を保存します：

- `ocr_results.txt`: テキスト形式の結果
- `ocr_results.json`: JSON形式の結果

## 出力形式

各画像ファイルごとに、抽出されたテキストがファイル名とともに記録されます。
