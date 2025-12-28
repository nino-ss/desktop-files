#!/usr/bin/env python3
"""
PDF、Word、PagesファイルをMarkdownに変換するスクリプト
効率的に一括変換を行う
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import mammoth
except ImportError:
    mammoth = None


def convert_pdf_to_markdown(pdf_path: Path) -> Optional[str]:
    """PDFをMarkdownに変換"""
    try:
        if fitz is None:
            print(f"警告: PyMuPDFがインストールされていません。{pdf_path} をスキップします。")
            return None
        
        doc = fitz.open(pdf_path)
        markdown_content = []
        
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():
                markdown_content.append(f"## ページ {page_num}\n\n{text}\n")
        
        doc.close()
        return "\n".join(markdown_content)
    
    except Exception as e:
        print(f"エラー: {pdf_path} の変換中にエラーが発生しました: {e}")
        return None


def convert_docx_to_markdown(docx_path: Path) -> Optional[str]:
    """Word (.docx)をMarkdownに変換"""
    try:
        # mammothを使用（より良い変換結果）
        if mammoth is not None:
            with open(docx_path, "rb") as docx_file:
                result = mammoth.convert_to_markdown(docx_file)
                return result.value
        
        # python-docxを使用（フォールバック）
        elif Document is not None:
            doc = Document(docx_path)
            markdown_content = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    # 見出しの判定（簡単なヒューリスティック）
                    if para.style.name.startswith('Heading'):
                        level = para.style.name.replace('Heading ', '')
                        try:
                            level_int = int(level)
                            markdown_content.append('#' * level_int + ' ' + text)
                        except ValueError:
                            markdown_content.append('## ' + text)
                    else:
                        markdown_content.append(text)
                    markdown_content.append('')
            
            return '\n'.join(markdown_content)
        
        else:
            print(f"警告: mammothまたはpython-docxがインストールされていません。{docx_path} をスキップします。")
            return None
    
    except Exception as e:
        print(f"エラー: {docx_path} の変換中にエラーが発生しました: {e}")
        return None


def convert_pages_to_markdown(pages_path: Path) -> Optional[str]:
    """PagesファイルをMarkdownに変換（macOSのtextutilを使用）"""
    try:
        # macOSのtextutilコマンドを使用してPagesをテキストに変換
        result = subprocess.run(
            ['textutil', '-convert', 'txt', '-stdout', str(pages_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # テキストをMarkdownに整形
            text = result.stdout.strip()
            # 簡単な整形：空行を適切に処理
            lines = text.split('\n')
            markdown_lines = []
            prev_empty = False
            
            for line in lines:
                line_stripped = line.strip()
                if line_stripped:
                    markdown_lines.append(line_stripped)
                    prev_empty = False
                elif not prev_empty:
                    markdown_lines.append('')
                    prev_empty = True
            
            return '\n'.join(markdown_lines)
        else:
            print(f"警告: {pages_path} をテキストに変換できませんでした。")
            return None
    
    except Exception as e:
        print(f"エラー: {pages_path} の変換中にエラーが発生しました: {e}")
        return None


def convert_file(file_path: Path, output_dir: Optional[Path] = None, overwrite: bool = False) -> bool:
    """ファイルをMarkdownに変換"""
    suffix = file_path.suffix.lower()
    
    # 対応する拡張子かチェック
    if suffix not in ['.pdf', '.docx', '.pages']:
        return False
    
    # 出力ファイル名を決定
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        md_path = output_dir / f"{file_path.stem}.md"
    else:
        md_path = file_path.parent / f"{file_path.stem}.md"
    
    # 既に存在する場合はスキップ（オプション）
    if md_path.exists() and not overwrite:
        print(f"スキップ: {md_path} は既に存在します（--overwriteで上書き可能）")
        return False
    
    # 変換を実行
    print(f"変換中: {file_path} -> {md_path}")
    
    if suffix == '.pdf':
        content = convert_pdf_to_markdown(file_path)
    elif suffix == '.docx':
        content = convert_docx_to_markdown(file_path)
    elif suffix == '.pages':
        content = convert_pages_to_markdown(file_path)
    else:
        return False
    
    if content is None:
        return False
    
    # Markdownファイルに書き込み
    try:
        md_path.write_text(content, encoding='utf-8')
        print(f"✓ 完了: {md_path}")
        return True
    except Exception as e:
        print(f"エラー: {md_path} の書き込み中にエラーが発生しました: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='PDF、Word、PagesファイルをMarkdownに変換',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デスクトップ全体を再帰的に変換
  python convert_to_markdown.py /Users/ninomiya/Desktop

  # 特定のディレクトリのみ変換
  python convert_to_markdown.py /Users/ninomiya/Desktop/AI

  # 出力ディレクトリを指定
  python convert_to_markdown.py /Users/ninomiya/Desktop --output ./markdown_output

  # 既存ファイルを上書き
  python convert_to_markdown.py /Users/ninomiya/Desktop --overwrite
        """
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='変換するファイルまたはディレクトリのパス（デフォルト: カレントディレクトリ）'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='出力ディレクトリ（指定しない場合は元のファイルと同じ場所）'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='既存のMarkdownファイルを上書きする'
    )
    
    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['pdf', 'docx', 'pages'],
        help='変換するファイル拡張子（デフォルト: pdf docx pages）'
    )
    
    args = parser.parse_args()
    
    # パスを解決
    target_path = Path(args.path).expanduser().resolve()
    
    if not target_path.exists():
        print(f"エラー: パスが見つかりません: {target_path}")
        sys.exit(1)
    
    # 出力ディレクトリ
    output_dir = Path(args.output).expanduser().resolve() if args.output else None
    
    # ファイルまたはディレクトリを処理
    files_to_convert = []
    
    if target_path.is_file():
        files_to_convert = [target_path]
    else:
        # 再帰的にファイルを検索
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions]
        for ext in extensions:
            files_to_convert.extend(target_path.rglob(f'*{ext}'))
    
    if not files_to_convert:
        print("変換対象のファイルが見つかりませんでした。")
        sys.exit(0)
    
    print(f"\n{len(files_to_convert)} 個のファイルが見つかりました。\n")
    
    # 変換を実行
    success_count = 0
    for file_path in sorted(files_to_convert):
        if convert_file(file_path, output_dir, args.overwrite):
            success_count += 1
    
    print(f"\n変換完了: {success_count}/{len(files_to_convert)} ファイル")


if __name__ == '__main__':
    main()
