#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import re
import copy
from pathlib import Path

def get_full_text(sentence_elem):
    """Sentence要素のテキスト全体を取得（子要素のテキストも含む）"""
    full_text = sentence_elem.text or ""
    for child in sentence_elem:
        # 子要素のテキストを再帰的に取得
        def get_child_text(elem):
            text = elem.text or ""
            for subchild in elem:
                text += get_child_text(subchild)
                if subchild.tail:
                    text += subchild.tail
            return text
        full_text += get_child_text(child)
        if child.tail:
            full_text += child.tail
    return full_text

def convert_sentence_to_list(sentence_elem):
    """Sentence要素をList要素に変換する"""
    # 子要素を含めたテキスト全体を取得
    full_text = get_full_text(sentence_elem)
    
    # 冒頭10文字以内に空白があるかチェック
    first_10_chars = full_text[:10]
    space_match = re.search(r'\s', first_10_chars)

    # List要素を作成
    list_elem = ET.Element("List")

    # ListSentence要素を作成
    list_sentence_elem = ET.SubElement(list_elem, "ListSentence")

    if space_match:
        # 最初の空白位置を取得
        space_pos = space_match.start()

        # Column Num="1" を作成
        column1 = ET.SubElement(list_sentence_elem, "Column", {"Num": "1"})
        sentence1 = ET.SubElement(column1, "Sentence", {"Num": "1"})
        
        # Column Num="2" を作成
        column2 = ET.SubElement(list_sentence_elem, "Column", {"Num": "2"})
        sentence2 = ET.SubElement(column2, "Sentence", {"Num": "1"})
        
        # 元のSentence要素の構造を順番に処理
        current_pos = 0
        
        # 最初のテキスト部分を処理
        if sentence_elem.text:
            text_len = len(sentence_elem.text)
            if text_len > space_pos:
                # テキストが分割点をまたいでいる
                text_before_space = sentence_elem.text[:space_pos]
                text_after_space = sentence_elem.text[space_pos + 1:]
                sentence1.text = text_before_space
                # Column 2の最初のテキストとして設定（後で子要素が追加される場合は調整）
                if text_after_space:
                    sentence2.text = text_after_space
                current_pos = text_len
            else:
                # テキストが分割点の前にある
                sentence1.text = sentence_elem.text
                current_pos = text_len
        
        # 子要素を処理
        def get_child_text_length(elem):
            """子要素のテキスト長を計算（再帰的に）"""
            length = len(elem.text or "")
            for subchild in elem:
                length += get_child_text_length(subchild)
                if subchild.tail:
                    length += len(subchild.tail)
            return length
        
        for child in sentence_elem:
            child_text_len = get_child_text_length(child)
            child_start_pos = current_pos
            child_end_pos = current_pos + child_text_len
            
            # 子要素が分割点の前にあるか後にあるかを判定
            if child_end_pos <= space_pos:
                # Column 1に配置
                child_copy = copy.deepcopy(child)
                sentence1.append(child_copy)
                if child.tail:
                    tail_start_pos = child_end_pos
                    tail_end_pos = tail_start_pos + len(child.tail)
                    if tail_end_pos <= space_pos:
                        # tail全体がColumn 1に来る
                        child_copy.tail = child.tail
                    elif tail_start_pos <= space_pos:
                        # tailが分割点をまたぐ（tail_start_pos == space_posの場合も含む）
                        tail_offset = space_pos - tail_start_pos
                        tail_before = child.tail[:tail_offset]
                        tail_after = child.tail[tail_offset + 1:]  # 分割点の空白を除去
                        child_copy.tail = tail_before
                        # Column 2のテキストを更新
                        if sentence2.text:
                            sentence2.text = tail_after + sentence2.text
                        else:
                            sentence2.text = tail_after
                    else:
                        # tail全体がColumn 2に来る
                        if sentence2.text:
                            sentence2.text = child.tail + sentence2.text
                        else:
                            sentence2.text = child.tail
            elif child_start_pos >= space_pos + 1:
                # Column 2に配置
                child_copy = copy.deepcopy(child)
                # tailを子要素のコピーに設定
                if child.tail:
                    child_copy.tail = child.tail
                sentence2.append(child_copy)
            else:
                # 子要素が分割点をまたいでいる場合
                # 基本的にColumn 2に配置（ArithFormulaなどは通常Column 2に来る）
                child_copy = copy.deepcopy(child)
                # tailを子要素のコピーに設定
                if child.tail:
                    child_copy.tail = child.tail
                sentence2.append(child_copy)
            
            # 位置を更新
            current_pos = child_end_pos
            if child.tail:
                current_pos += len(child.tail)
        
        # Column 2のテキストを整理（子要素の前にテキストがある場合）
        if sentence2.text and len(sentence2) > 0:
            # 最初の子要素の前にテキストがある場合、そのまま保持
            pass
        
    else:
        # 空白がない場合はColumnなしでSentenceをそのまま
        sentence = ET.SubElement(list_sentence_elem, "Sentence", {"Num": "1"})
        sentence.text = sentence_elem.text
        # 子要素をすべてコピー
        for child in sentence_elem:
            child_copy = copy.deepcopy(child)
            sentence.append(child_copy)
            if child.tail:
                child_copy.tail = child.tail

    return list_elem

def convert_xml(input_file, output_file):
    """XMLファイルを変換する"""
    # XMLファイルをパース
    tree = ET.parse(input_file)
    root = tree.getroot()

    # ParagraphSentence要素を探す
    for paragraph_sentence in root.iter('ParagraphSentence'):
        # 既存のSentence要素を削除し、List要素に変換
        sentences = list(paragraph_sentence)  # 子要素のコピーを作成

        # Sentence要素が10個以上の場合のみ変換を行う
        sentence_count = sum(1 for elem in sentences if elem.tag == 'Sentence')
        if sentence_count >= 10:
            # すべての子要素をクリア
            paragraph_sentence.clear()

            # 各SentenceをListに変換して追加
            for sentence in sentences:
                if sentence.tag == 'Sentence':
                    list_elem = convert_sentence_to_list(sentence)
                    paragraph_sentence.append(list_elem)
                else:
                    # Sentence以外の要素はそのまま追加
                    paragraph_sentence.append(sentence)

    # expect.xmlに近いフォーマットで出力
    def format_xml_element(element, level=0):
        """expect.xmlに近いフォーマットでXML要素を整形"""
        # expect.xmlのインデントに合わせる（レベル0: 0スペース, レベル1: 2スペース, レベル2: 4スペース, etc.）
        indent = "  " * level

        # 開始タグ
        attrs = []
        for key, value in element.attrib.items():
            if '{' in key and '}' in key:
                # xmlns属性の場合、名前空間形式を正しい形式に変換
                ns_end = key.find('}')
                ns_uri = key[1:ns_end]
                attr_name = key[ns_end + 1:]
                if attr_name.startswith('xmlns:'):
                    attrs.append(f'{attr_name}="{ns_uri}"')
                elif attr_name == 'noNamespaceSchemaLocation':
                    attrs.insert(0, f'xmlns:xsi="{ns_uri}"')  # xmlns:xsiを先頭に
                    attrs.append(f'xsi:{attr_name}="{value}"')
            else:
                attrs.append(f'{key}="{value}"')

        # Law要素の場合、属性の順序をexpect.xmlに合わせる
        if element.tag == 'Law':
            ordered_attrs = []
            # 通常属性
            for attr in attrs:
                if not attr.startswith('xmlns:') and not attr.startswith('xsi:'):
                    ordered_attrs.append(attr)
            # xmlns属性
            for attr in attrs:
                if attr.startswith('xmlns:'):
                    ordered_attrs.append(attr)
            # xsi属性
            for attr in attrs:
                if attr.startswith('xsi:'):
                    ordered_attrs.append(attr)
            attrs = ordered_attrs

        attr_str = ' ' + ' '.join(attrs) if attrs else ''

        # Law要素の特別処理
        if element.tag == 'Law':
            attr_str += ' '

        # Ruby要素の特別処理
        if element.tag == 'Ruby':
            # Ruby要素は子要素を同じ行にまとめる
            result = f"<{element.tag}{attr_str}>"
            if element.text and element.text.strip():
                result += element.text.strip()

            # 子要素を同じ行に
            for child in element:
                child_result = format_xml_element(child, 0)  # Rubyの子要素はインデントなし
                result += child_result
                if child.tail and child.tail.strip():
                    result += child.tail.strip()

            result += f"</{element.tag}>"
            return result

        # Sentence要素の特別処理
        if element.tag == 'Sentence':
            # Sentence要素はテキストと子要素をすべて同じ行にまとめる
            result = f"{indent}<{element.tag}{attr_str}>"
            if element.text and element.text.strip():
                result += element.text.strip()

            # 子要素を同じ行に
            for child in element:
                child_result = format_xml_element(child, 0)  # Sentenceの子要素はインデントなし
                result += child_result
                if child.tail and child.tail.strip():
                    result += child.tail.strip()

            result += f"</{element.tag}>"
            return result

        # ArithFormula要素の特別処理
        if element.tag == 'ArithFormula':
            # ArithFormula要素はテキストと子要素をすべて同じ行にまとめる
            result = f"<{element.tag}{attr_str}>"
            if element.text and element.text.strip():
                result += element.text.strip()

            # 子要素を同じ行に
            for child in element:
                child_result = format_xml_element(child, 0)  # ArithFormulaの子要素はインデントなし
                result += child_result
                if child.tail and child.tail.strip():
                    result += child.tail.strip()

            result += f"</{element.tag}>"
            return result

        # 空要素の場合
        if len(element) == 0 and (element.text is None or element.text.strip() == ''):
            if element.tag in ['ArticleTitle', 'ParagraphNum', 'TableStructTitle', 'Remarks', 'ItemTitle']:
                # expect.xmlではこれらの要素は <tag></tag> 形式
                result = f"{indent}<{element.tag}{attr_str}></{element.tag}>"
            else:
                # 他の空要素は <tag/> 形式
                result = f"{indent}<{element.tag}{attr_str}/>"
        else:
            result = f"{indent}<{element.tag}{attr_str}>"

            # テキストコンテンツ
            if element.text and element.text.strip():
                if element.tag == 'Sentence':
                    # Sentence要素はテキストを1行で出力
                    text_content = element.text.strip()
                    result += text_content
                elif element.tag == 'LawNum':
                    # LawNum要素はテキストをそのまま（改行なし）
                    result += element.text.strip()
                else:
                    result += element.text.strip()

            # 子要素
            if len(element) > 0:
                result += "\n"
                for child in element:
                    result += format_xml_element(child, level + 1)
                    # tailテキストがある場合は追加
                    if child.tail and child.tail.strip():
                        result += child.tail.strip()
                    result += "\n"
                result += indent
            elif element.tag == 'Sentence' and element.text and element.text.strip():
                # Sentence要素の場合は閉じタグを同じ行に
                pass
            elif element.tag == 'LawNum' and element.text and element.text.strip():
                # LawNum要素の場合は閉じタグを同じ行に
                pass
            else:
                pass

            result += f"</{element.tag}>"

        return result

    # XML宣言 + ルート要素の整形
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += format_xml_element(root)
    xml_content += '\n'  # ファイル末尾に改行を追加

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)

def process_folder(input_dir, output_dir, recursive=False):
    """フォルダ内のXMLファイルを一括変換
    
    Args:
        input_dir: 入力フォルダのパス
        output_dir: 出力フォルダのパス
        recursive: Trueの場合、サブフォルダも再帰的に検索（デフォルト: False）
    """
    from datetime import datetime
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 入力フォルダが存在することを確認
    if not input_path.exists():
        print(f"入力フォルダ {input_path} が存在しません。")
        return

    # 出力フォルダが存在しない場合は作成
    output_path.mkdir(parents=True, exist_ok=True)

    # 入力フォルダ内のXMLファイルを検索
    if recursive:
        xml_files = list(input_path.glob("**/*.xml"))
    else:
        xml_files = list(input_path.glob("*.xml"))
    
    if not xml_files:
        search_mode = "（サブフォルダ含む）" if recursive else "（直下のみ）"
        print(f"入力フォルダ {input_path} にXMLファイルが見つかりません{search_mode}。")
        return

    print(f"{len(xml_files)} 個のXMLファイルを処理します...")

    # エラー情報を記録
    errors = []
    success_count = 0
    error_count = 0

    for input_file in xml_files:
        # 出力ファイルのパスを生成
        if recursive:
            # サブフォルダ構造を保持
            relative_path = input_file.relative_to(input_path)
            output_file = output_path / relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            display_name = str(relative_path)
        else:
            output_file = output_path / input_file.name
            display_name = input_file.name

        print(f"処理中: {display_name}")
        try:
            convert_xml(input_file, output_file)
            print(f"  ✓ 完了: {display_name}")
            success_count += 1
        except ET.ParseError as e:
            error_msg = f"XML構文エラー: {str(e)}"
            if hasattr(e, 'position'):
                error_msg += f" (行 {e.position[0]}, 列 {e.position[1]})"
            print(f"  ✗ エラー: {display_name} - {error_msg}")
            errors.append({
                "file": display_name,
                "error_type": "XML構文エラー",
                "error_message": str(e),
                "line": e.position[0] if hasattr(e, 'position') else None,
                "column": e.position[1] if hasattr(e, 'position') else None
            })
            error_count += 1
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"  ✗ エラー: {display_name} - {error_type}: {error_msg}")
            errors.append({
                "file": display_name,
                "error_type": error_type,
                "error_message": error_msg
            })
            error_count += 1

    print(f"\n全ファイルの処理が完了しました。")
    print(f"  成功: {success_count} 個")
    if error_count > 0:
        print(f"  エラー: {error_count} 個")

    # エラー情報をMarkdownファイルに出力
    if errors:
        error_report_path = output_path / "validation_results" / "conversion_errors.md"
        error_report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(error_report_path, 'w', encoding='utf-8') as f:
            f.write("# XML変換エラー詳細\n\n")
            f.write(f"## 処理概要\n\n")
            f.write(f"- **実行日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **入力フォルダ**: {input_path}\n")
            f.write(f"- **出力フォルダ**: {output_path}\n")
            f.write(f"- **総処理ファイル数**: {len(xml_files)}\n")
            f.write(f"- **✅ 変換成功**: {success_count} ファイル\n")
            f.write(f"- **❌ 変換失敗**: {error_count} ファイル\n\n")
            
            f.write("## エラー詳細\n\n")
            for i, error in enumerate(errors, 1):
                f.write(f"### {i}. {error['file']}\n\n")
                f.write(f"- **エラータイプ**: {error['error_type']}\n")
                f.write(f"- **エラーメッセージ**: {error['error_message']}\n")
                if error.get('line') is not None:
                    f.write(f"- **エラー位置**: 行 {error['line']}, 列 {error.get('column', 'N/A')}\n")
                f.write("\n")
        
        print(f"  📄 エラー詳細: {error_report_path}")

def main():
    import sys

    # 引数解析
    recursive = False
    args = []
    for arg in sys.argv[1:]:
        if arg in ['--recursive', '-r']:
            recursive = True
        else:
            args.append(arg)

    if len(args) == 0:
        # 引数なしの場合、デフォルトの動作（単一ファイル）
        input_file = Path("input.xml")
        output_file = Path("output.xml")

        if not input_file.exists():
            print(f"入力ファイル {input_file} が存在しません。")
            print("使い方: python xml_converter.py [input.xml output.xml]")
            print("フォルダ処理: python xml_converter.py input_dir output_dir [--recursive]")
            return

        print(f"{input_file} を {output_file} に変換します...")
        convert_xml(input_file, output_file)
        print("変換が完了しました。")

    elif len(args) == 2:
        input_arg = args[0]
        output_arg = args[1]

        input_path = Path(input_arg)
        output_path = Path(output_arg)

        # フォルダかどうかを判定
        if input_path.is_dir():
            process_folder(input_arg, output_arg, recursive=recursive)
        else:
            # 単一ファイル処理
            if not input_path.exists():
                print(f"入力ファイル {input_path} が存在しません。")
                return

            print(f"{input_path} を {output_path} に変換します...")
            convert_xml(input_path, output_path)
            print("変換が完了しました。")

    else:
        print("使い方:")
        print("  単一ファイル: python xml_converter.py input.xml output.xml")
        print("  フォルダ処理: python xml_converter.py input_dir output_dir [--recursive]")
        print("  デフォルト: python xml_converter.py (input.xml -> output.xml)")
        print("")
        print("オプション:")
        print("  --recursive, -r: サブフォルダも再帰的に検索（デフォルト: 直下のみ）")

if __name__ == "__main__":
    main()
