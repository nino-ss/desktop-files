#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スクリーンショット画像から文字情報を抽出するOCRスクリプト
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("必要なライブラリがインストールされていません。")
    print("以下のコマンドでインストールしてください：")
    print("pip install pillow pytesseract")
    sys.exit(1)

def extract_text_from_image(image_path):
    """
    画像ファイルからテキストを抽出
    
    Args:
        image_path: 画像ファイルのパス
        
    Returns:
        抽出されたテキスト（文字列）
    """
    try:
        # 画像を開く
        image = Image.open(image_path)
        
        # OCRを実行（日本語と英語の両方に対応）
        # lang='jpn+eng' で日本語と英語を認識
        text = pytesseract.image_to_string(image, lang='jpn+eng')
        
        return text.strip()
    except Exception as e:
        return f"エラー: {str(e)}"

def process_all_screenshots(directory_path):
    """
    ディレクトリ内のすべてのスクリーンショット画像を処理
    
    Args:
        directory_path: 画像ファイルが含まれるディレクトリのパス
        
    Returns:
        ファイル名と抽出テキストの辞書
    """
    results = {}
    directory = Path(directory_path)
    
    # PNGファイルを検索
    image_files = sorted(directory.glob("*.png"))
    
    if not image_files:
        print("画像ファイルが見つかりませんでした。")
        return results
    
    print(f"{len(image_files)}個の画像ファイルが見つかりました。")
    print("文字抽出を開始します...\n")
    
    for i, image_file in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] 処理中: {image_file.name}")
        text = extract_text_from_image(image_file)
        
        if text and not text.startswith("エラー"):
            results[image_file.name] = text
            print(f"  ✓ テキスト抽出完了 ({len(text)}文字)")
        else:
            results[image_file.name] = text
            print(f"  ⚠ {text}")
        print()
    
    return results

def save_results(results, output_file="ocr_results.txt", json_file="ocr_results.json"):
    """
    抽出結果をファイルに保存
    
    Args:
        results: ファイル名とテキストの辞書
        output_file: テキスト形式の出力ファイル名
        json_file: JSON形式の出力ファイル名
    """
    # テキスト形式で保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("スクリーンショット文字抽出結果\n")
        f.write(f"抽出日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for filename, text in results.items():
            f.write(f"\n{'=' * 80}\n")
            f.write(f"ファイル名: {filename}\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"{text}\n")
            f.write(f"\n")
    
    # JSON形式で保存
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果を保存しました:")
    print(f"  - {output_file} (テキスト形式)")
    print(f"  - {json_file} (JSON形式)")

def main():
    """メイン処理"""
    # 現在のディレクトリを取得
    current_dir = Path(__file__).parent
    
    print("=" * 80)
    print("スクリーンショット文字抽出ツール")
    print("=" * 80)
    print()
    
    # Tesseractがインストールされているか確認
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        print("エラー: Tesseract OCRがインストールされていません。")
        print("\nインストール方法:")
        print("  macOS: brew install tesseract tesseract-lang")
        print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-jpn")
        print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki からインストール")
        sys.exit(1)
    
    # 利用可能な言語を確認
    try:
        available_langs = pytesseract.get_languages()
        if 'jpn' not in available_langs:
            print("警告: 日本語言語パックがインストールされていない可能性があります。")
            print("利用可能な言語:", ', '.join(available_langs[:10]))
            print("\n日本語対応のため、以下をインストールしてください:")
            print("  macOS: brew install tesseract-lang")
            print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr-jpn")
    except Exception:
        pass
    
    # 画像処理を実行
    results = process_all_screenshots(current_dir)
    
    if results:
        # 結果を保存
        save_results(results)
        
        # 統計情報を表示
        total_text_length = sum(len(text) for text in results.values() if not text.startswith("エラー"))
        files_with_text = sum(1 for text in results.values() if text and not text.startswith("エラー"))
        
        print("\n" + "=" * 80)
        print("処理完了")
        print("=" * 80)
        print(f"処理したファイル数: {len(results)}")
        print(f"テキストが抽出されたファイル数: {files_with_text}")
        print(f"抽出された総文字数: {total_text_length}")
    else:
        print("処理する画像ファイルが見つかりませんでした。")

if __name__ == "__main__":
    main()
