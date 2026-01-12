#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

def extract_sentence_text(sentence_elem):
    """Sentence要素からテキストを抽出（子要素も含む）"""
    text_parts = []
    
    # 要素のテキスト
    if sentence_elem.text:
        text_parts.append(sentence_elem.text)
    
    # 子要素を処理
    for child in sentence_elem:
        if child.tag == 'Ruby':
            # Ruby要素の処理
            if child.text:
                text_parts.append(child.text)
            for ruby_child in child:
                if ruby_child.tag == 'Rt':
                    if ruby_child.text:
                        text_parts.append(ruby_child.text)
        elif child.tag in ['Sup', 'Sub', 'Line', 'ArithFormula']:
            # これらの要素はテキストと子要素を再帰的に処理
            child_text = extract_element_text_recursive(child)
            if child_text:
                text_parts.append(child_text)
        else:
            # その他の子要素も再帰的に処理
            child_text = extract_element_text_recursive(child)
            if child_text:
                text_parts.append(child_text)
    
    return ''.join(text_parts).strip()

def extract_element_text_recursive(elem):
    """要素から再帰的にテキストを抽出"""
    text_parts = []
    
    if elem.text:
        text_parts.append(elem.text)
    
    for child in elem:
        child_text = extract_element_text_recursive(child)
        if child_text:
            text_parts.append(child_text)
    
    if elem.tail:
        text_parts.append(elem.tail)
    
    return ''.join(text_parts)

def extract_list_text(list_elem):
    """List構造からColumnのSentenceを結合して元のテキストを再構築"""
    text_parts = []
    
    # List要素の直接の子要素であるListSentenceを取得
    for list_sentence in list_elem:
        if list_sentence.tag != 'ListSentence':
            continue
            
        # ListSentenceの直接の子要素であるColumnを取得
        columns = [child for child in list_sentence if child.tag == 'Column']
        
        if len(columns) >= 2:
            # Columnが2つ以上ある場合、結合（最初の空白で分割されたもの）
            column_texts = []
            for column in columns:
                # Columnの直接の子要素であるSentenceを取得
                sentences = [child for child in column if child.tag == 'Sentence']
                column_text = ' '.join([extract_sentence_text(s) for s in sentences if extract_sentence_text(s)])
                if column_text:
                    column_texts.append(column_text)
            
            # 最初の空白で分割された場合、全角スペースで結合
            if len(column_texts) >= 2:
                combined = column_texts[0] + '\u3000' + column_texts[1]
                text_parts.append(combined)
            elif len(column_texts) == 1:
                text_parts.append(column_texts[0])
        else:
            # Columnがない場合、直接Sentenceを取得
            sentences = [child for child in list_sentence if child.tag == 'Sentence']
            for sentence in sentences:
                sentence_text = extract_sentence_text(sentence)
                if sentence_text:
                    text_parts.append(sentence_text)
    
    return text_parts

def extract_values_from_xml_structure(file_path):
    """XML構造を理解してテキストを抽出（構造変換を考慮）"""
    values = []
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # ParagraphSentence要素を探す
        for paragraph_sentence in root.iter('ParagraphSentence'):
            for child in paragraph_sentence:
                if child.tag == 'Sentence':
                    # Sentence要素のテキストを抽出
                    text = extract_sentence_text(child)
                    if text:
                        values.append(text)
                elif child.tag == 'List':
                    # List構造からテキストを再構築
                    list_texts = extract_list_text(child)
                    values.extend(list_texts)
                else:
                    # その他の要素は従来通り処理
                    if child.text and child.text.strip():
                        values.append(child.text.strip())
        
        # ParagraphSentence以外の要素も処理（簡易的にテキストノードを抽出）
        # 注意: これは補完的な処理で、主要な処理はParagraphSentence内で行われる
    
    except ET.ParseError:
        # XMLパースエラーの場合、従来の方法にフォールバック
        return extract_values_from_lines(file_path)
    
    return values

def extract_values_from_lines(file_path):
    """Extract values from XML file by removing tags from each line, ignoring XML structure."""
    values = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Remove XML tags using regex
            # This removes anything between < and > including the brackets
            line_without_tags = re.sub(r'<[^>]+>', '', line)
            # Remove extra whitespace and strip
            cleaned_line = line_without_tags.strip()
            # Only add non-empty lines
            if cleaned_line:
                values.append(cleaned_line)

    return values

def compare_value_lists(values1, values2):
    """Compare two lists of values and report differences."""
    # Find missing values in list2
    missing_in_2 = []
    for value in values1:
        if values1.count(value) > values2.count(value):
            missing_in_2.extend([value] * (values1.count(value) - values2.count(value)))

    # Find extra values in list2
    extra_in_2 = []
    for value in values2:
        if values2.count(value) > values1.count(value):
            extra_in_2.extend([value] * (values2.count(value) - values1.count(value)))

    # Check order differences
    order_differences = []
    min_len = min(len(values1), len(values2))
    for i in range(min_len):
        if values1[i] != values2[i]:
            order_differences.append({
                'position': i,
                'file1': values1[i],
                'file2': values2[i]
            })

    # Check for values that appear in both but at different positions
    if len(values1) != len(values2):
        if len(values1) > len(values2):
            order_differences.extend([{
                'position': i,
                'file1': values1[i],
                'file2': '<MISSING>'
            } for i in range(len(values2), len(values1))])
        else:
            order_differences.extend([{
                'position': i,
                'file1': '<MISSING>',
                'file2': values2[i]
            } for i in range(len(values1), len(values2))])

    return {
        'missing_in_2': missing_in_2,
        'extra_in_2': extra_in_2,
        'order_differences': order_differences,
        'total_values_1': len(values1),
        'total_values_2': len(values2),
        'identical': values1 == values2
    }

def main():
    parser = argparse.ArgumentParser(description='XML値比較: 構造を無視して値の差分と順序差分のみを検証')
    parser.add_argument('file1', help='比較元XMLファイル')
    parser.add_argument('file2', help='比較先XMLファイル')
    parser.add_argument('--max-diff', type=int, default=10, help='表示する差異の最大数')
    parser.add_argument('--output', '-o', help='出力ファイルパス（.md拡張子推奨、指定しない場合は標準出力）')

    args = parser.parse_args()

    # 出力ファイルパスの処理
    if args.output:
        output_path = Path(args.output)
        # 拡張子が指定されていない場合は.mdを付ける
        if not output_path.suffix:
            output_path = output_path.with_suffix('.md')
        args.output = str(output_path)

    path1 = Path(args.file1)
    path2 = Path(args.file2)

    if not path1.exists():
        print(f"❌ エラー: ファイルが見つかりません: {args.file1}", file=sys.stderr)
        return 1
    if not path2.exists():
        print(f"❌ エラー: ファイルが見つかりません: {args.file2}", file=sys.stderr)
        return 1

    # 構造変換を考慮した抽出を試行
    try:
        values1 = extract_values_from_xml_structure(path1)
        values2 = extract_values_from_xml_structure(path2)
    except Exception as e:
        # エラーが発生した場合は従来の方法にフォールバック
        print(f"⚠️  警告: XML構造解析でエラーが発生しました。従来の方法を使用します: {e}", file=sys.stderr)
        values1 = extract_values_from_lines(path1)
        values2 = extract_values_from_lines(path2)

    # 出力先の設定
    if args.output:
        output_file = open(args.output, 'w', encoding='utf-8')
        print_func = lambda msg: print(msg, file=output_file)
    else:
        output_file = None
        print_func = print

    # Markdown形式で出力
    print_func("# XML値比較レポート (構造無視)")
    print_func("")
    print_func(f"- **ファイル1**: `{path1.name}` - {len(values1)} 個の値")
    print_func(f"- **ファイル2**: `{path2.name}` - {len(values2)} 個の値")
    print_func(f"- **比較日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_func("")

    result = compare_value_lists(values1, values2)

    if result['identical']:
        print_func("## ✅ 検証結果: 成功")
        print_func("")
        print_func("すべての値が同一です。")
        if output_file:
            output_file.close()
        return 0
    else:
        print_func("## ❌ 検証結果: 差異検出")
        print_func("")
        print_func("以下の差異が見つかりました:")
        print_func("")

        if result['missing_in_2']:
            print_func(f"### 📝 ファイル2に欠落している値 ({len(result['missing_in_2'])} 件)")
            print_func("")
            for i, value in enumerate(result['missing_in_2'][:args.max_diff]):
                print_func(f"{i+1}. `{repr(value[:100])}`")
            if len(result['missing_in_2']) > args.max_diff:
                print_func(f"**... 他 {len(result['missing_in_2']) - args.max_diff} 件**")
            print_func("")

        if result['extra_in_2']:
            print_func(f"### 📝 ファイル2に追加されている値 ({len(result['extra_in_2'])} 件)")
            print_func("")
            for i, value in enumerate(result['extra_in_2'][:args.max_diff]):
                print_func(f"{i+1}. `{repr(value[:100])}`")
            if len(result['extra_in_2']) > args.max_diff:
                print_func(f"**... 他 {len(result['extra_in_2']) - args.max_diff} 件**")
            print_func("")

        if result['order_differences']:
            print_func(f"### 🔄 順序または内容の差異 ({len(result['order_differences'])} 件)")
            print_func("")
            for diff in result['order_differences'][:args.max_diff]:
                print_func(f"**位置 {diff['position']}:**")
                print_func(f"- ファイル1: `{repr(diff['file1'][:100])}`")
                print_func(f"- ファイル2: `{repr(diff['file2'][:100])}`")
                print_func("")
            if len(result['order_differences']) > args.max_diff:
                print_func(f"**... 他 {len(result['order_differences']) - args.max_diff} 件**")
                print_func("")

        print_func("## 📋 検証完了")
        print_func("")
        print_func(f"- 総差異数: {len(result['missing_in_2']) + len(result['extra_in_2']) + len(result['order_differences'])} 件")
        print_func(f"- 表示制限: 最大 {args.max_diff} 件まで表示")
        if output_file:
            output_file.close()
        return 1

if __name__ == '__main__':
    sys.exit(main())
