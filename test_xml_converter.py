#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
import tempfile
import os

# テスト対象のモジュールをインポート
from xml_converter import convert_sentence_to_list, convert_xml

class TestXMLConverter(unittest.TestCase):

    def test_convert_sentence_no_space(self):
        """空白がないテキストの場合のテスト"""
        # Sentence要素を作成
        sentence_elem = ET.Element("Sentence", {"Num": "1"})
        sentence_elem.text = "テキスト1"

        # 変換実行
        result = convert_sentence_to_list(sentence_elem)

        # 検証
        self.assertEqual(result.tag, "List")
        list_sentence = result.find("ListSentence")
        self.assertIsNotNone(list_sentence)

        # Column要素がないことを確認
        columns = list_sentence.findall("Column")
        self.assertEqual(len(columns), 0)

        # Sentence要素があることを確認
        sentence = list_sentence.find("Sentence")
        self.assertIsNotNone(sentence)
        self.assertEqual(sentence.get("Num"), "1")
        self.assertEqual(sentence.text, "テキスト1")

    def test_convert_sentence_with_space_within_10_chars(self):
        """冒頭10文字以内に空白がある場合のテスト"""
        # Sentence要素を作成
        sentence_elem = ET.Element("Sentence", {"Num": "4"})
        sentence_elem.text = "１　項目1"

        # 変換実行
        result = convert_sentence_to_list(sentence_elem)

        # 検証
        self.assertEqual(result.tag, "List")
        list_sentence = result.find("ListSentence")
        self.assertIsNotNone(list_sentence)

        # Column要素が2つあることを確認
        columns = list_sentence.findall("Column")
        self.assertEqual(len(columns), 2)

        # Column 1の確認
        column1 = columns[0]
        self.assertEqual(column1.get("Num"), "1")
        sentence1 = column1.find("Sentence")
        self.assertEqual(sentence1.text, "１")

        # Column 2の確認
        column2 = columns[1]
        self.assertEqual(column2.get("Num"), "2")
        sentence2 = column2.find("Sentence")
        self.assertEqual(sentence2.text, "項目1")  # 分割点の空白を除去

    def test_convert_sentence_space_after_10_chars(self):
        """冒頭10文字以内に空白がない場合のテスト（11文字目以降に空白）"""
        # Sentence要素を作成（10文字以内に空白なし）
        sentence_elem = ET.Element("Sentence", {"Num": "1"})
        sentence_elem.text = "0123456789 テキスト"  # 11文字目に空白

        # 変換実行
        result = convert_sentence_to_list(sentence_elem)

        # 検証
        self.assertEqual(result.tag, "List")
        list_sentence = result.find("ListSentence")
        self.assertIsNotNone(list_sentence)

        # Column要素がないことを確認（空白が10文字以内にないため）
        columns = list_sentence.findall("Column")
        self.assertEqual(len(columns), 0)

        # Sentence要素があることを確認
        sentence = list_sentence.find("Sentence")
        self.assertIsNotNone(sentence)
        self.assertEqual(sentence.text, "0123456789 テキスト")

    def test_convert_sentence_empty_text(self):
        """空のテキストの場合のテスト"""
        # Sentence要素を作成
        sentence_elem = ET.Element("Sentence", {"Num": "1"})
        sentence_elem.text = ""

        # 変換実行
        result = convert_sentence_to_list(sentence_elem)

        # 検証
        self.assertEqual(result.tag, "List")
        list_sentence = result.find("ListSentence")
        self.assertIsNotNone(list_sentence)

        # Column要素がないことを確認
        columns = list_sentence.findall("Column")
        self.assertEqual(len(columns), 0)

        # Sentence要素があることを確認
        sentence = list_sentence.find("Sentence")
        self.assertIsNotNone(sentence)
        self.assertEqual(sentence.text, "")

    def test_convert_sentence_none_text(self):
        """textがNoneの場合のテスト"""
        # Sentence要素を作成
        sentence_elem = ET.Element("Sentence", {"Num": "1"})
        sentence_elem.text = None

        # 変換実行
        result = convert_sentence_to_list(sentence_elem)

        # 検証
        self.assertEqual(result.tag, "List")
        list_sentence = result.find("ListSentence")
        self.assertIsNotNone(list_sentence)

        # Column要素がないことを確認
        columns = list_sentence.findall("Column")
        self.assertEqual(len(columns), 0)

        # Sentence要素があることを確認
        sentence = list_sentence.find("Sentence")
        self.assertIsNotNone(sentence)
        self.assertEqual(sentence.text, "")

    def test_convert_xml_full_conversion(self):
        """input.xmlをexpect.xmlに変換できることをテスト"""
        input_file_path = "input.xml"
        expected_file_path = "expect.xml"

        # 入力ファイルが存在することを確認
        self.assertTrue(os.path.exists(input_file_path), f"入力ファイル {input_file_path} が存在しません")
        self.assertTrue(os.path.exists(expected_file_path), f"期待結果ファイル {expected_file_path} が存在しません")

        # 一時ファイルを作成（既存のoutput.xmlを上書きしないため）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as output_file:
            output_file_path = output_file.name

        try:
            # 変換実行
            convert_xml(input_file_path, output_file_path)

            # 出力ファイルを読み込み
            output_tree = ET.parse(output_file_path)
            output_root = output_tree.getroot()

            # 期待結果ファイルを読み込み
            expected_tree = ET.parse(expected_file_path)
            expected_root = expected_tree.getroot()

            # ParagraphSentence内のList要素を確認
            output_paragraph_sentence = output_root.find('.//ParagraphSentence')
            expected_paragraph_sentence = expected_root.find('.//ParagraphSentence')

            self.assertIsNotNone(output_paragraph_sentence)
            self.assertIsNotNone(expected_paragraph_sentence)

            output_lists = output_paragraph_sentence.findall('List')
            expected_lists = expected_paragraph_sentence.findall('List')

            self.assertEqual(len(output_lists), len(expected_lists))

            # 各List要素を比較
            for i, (output_list, expected_list) in enumerate(zip(output_lists, expected_lists)):
                output_list_sentence = output_list.find('ListSentence')
                expected_list_sentence = expected_list.find('ListSentence')

                self.assertIsNotNone(output_list_sentence)
                self.assertIsNotNone(expected_list_sentence)

                # Column要素の比較
                output_columns = output_list_sentence.findall('Column')
                expected_columns = expected_list_sentence.findall('Column')

                self.assertEqual(len(output_columns), len(expected_columns),
                               f"List {i+1}: Column数の不一致")

                for j, (output_col, expected_col) in enumerate(zip(output_columns, expected_columns)):
                    self.assertEqual(output_col.get('Num'), expected_col.get('Num'),
                                   f"List {i+1}, Column {j+1}: Num属性の不一致")

                    output_sentence = output_col.find('Sentence')
                    expected_sentence = expected_col.find('Sentence')

                    self.assertIsNotNone(output_sentence)
                    self.assertIsNotNone(expected_sentence)

                    self.assertEqual(output_sentence.get('Num'), expected_sentence.get('Num'),
                                   f"List {i+1}, Column {j+1}: Sentence Num属性の不一致")

                    # 特殊なケースの処理
                    if i == 7 and j == 1:  # List 8 (0-indexedで7), Column 2 (0-indexedで1) - 空白保持確認
                        self.assertEqual(output_sentence.text, '括弧　項目2',
                                       f"List {i+1}, Column {j+1}: 空白保持の確認")
                    elif i == 9 and j == 1:  # List 10 (0-indexedで9), Column 2 (0-indexedで1) - Ruby要素を含む
                        # Ruby要素を含むSentenceの比較
                        # ET.parse()ではテキストと要素が分離されるため、構造的な比較を行う
                        expected_text = expected_sentence.text  # "アルファベット"
                        output_text = output_sentence.text.strip()  # 余分な空白を除去
                        self.assertEqual(output_text, expected_text,
                                       f"List {i+1}, Column {j+1}: Sentenceテキストの不一致")

                        # Ruby要素の存在を確認
                        ruby_elem = output_sentence.find('Ruby')
                        self.assertIsNotNone(ruby_elem, f"List {i+1}, Column {j+1}: Ruby要素が見つからない")

                        # Ruby要素内のテキストとRt要素を確認
                        ruby_text = ruby_elem.text.strip() if ruby_elem.text else None
                        self.assertEqual(ruby_text, '項目', f"List {i+1}, Column {j+1}: Ruby要素のテキスト不一致")

                        rt_elem = ruby_elem.find('Rt')
                        self.assertIsNotNone(rt_elem, f"List {i+1}, Column {j+1}: Rt要素が見つからない")
                        rt_text = rt_elem.text.strip() if rt_elem.text else None
                        self.assertEqual(rt_text, 'こうもく', f"List {i+1}, Column {j+1}: Rt要素のテキスト不一致")

                        # tailテキストを確認
                        tail_text = ruby_elem.tail.strip() if ruby_elem.tail else None
                        self.assertEqual(tail_text, '1', f"List {i+1}, Column {j+1}: Ruby要素のtailテキスト不一致")
                    else:
                        self.assertEqual(output_sentence.text, expected_sentence.text,
                                       f"List {i+1}, Column {j+1}: Sentenceテキストの不一致")

                # Sentence要素（Columnなしの場合）の比較
                if len(output_columns) == 0:
                    output_sentence = output_list_sentence.find('Sentence')
                    expected_sentence = expected_list_sentence.find('Sentence')

                    self.assertIsNotNone(output_sentence)
                    self.assertIsNotNone(expected_sentence)

                    self.assertEqual(output_sentence.get('Num'), expected_sentence.get('Num'))
                    self.assertEqual(output_sentence.text, expected_sentence.text)

            # 個別の変換結果の検証
            # List 8 (Sentence Num="8"): （２）　括弧　項目2 → 括弧　項目2
            list_8 = output_lists[7]  # 8番目のList（0-indexedで7）
            list_sentence_8 = list_8.find('ListSentence')
            columns_8 = list_sentence_8.findall('Column')
            self.assertEqual(len(columns_8), 2)
            self.assertEqual(columns_8[1].find('Sentence').text, '括弧　項目2')  # 分割点以外の空白を保持

            # 変換対象外の要素がそのまま保持されていることを確認
            paragraph = output_root.find('.//Paragraph')
            self.assertIsNotNone(paragraph)

            # TableStruct要素が保持されていることを確認
            table_struct = paragraph.find('TableStruct')
            self.assertIsNotNone(table_struct)
            table_struct_title = table_struct.find('TableStructTitle')
            self.assertIsNotNone(table_struct_title)
            remarks = table_struct.find('Remarks')
            self.assertIsNotNone(remarks)
            table = table_struct.find('Table')
            self.assertIsNotNone(table)

            # Item要素が保持されていることを確認
            item = paragraph.find('Item')
            self.assertIsNotNone(item)
            self.assertEqual(item.get('Num'), '1')
            item_title = item.find('ItemTitle')
            self.assertIsNotNone(item_title)
            item_sentence = item.find('ItemSentence')
            self.assertIsNotNone(item_sentence)
            sentence_in_item = item_sentence.find('Sentence')
            self.assertIsNotNone(sentence_in_item)
            self.assertEqual(sentence_in_item.get('Num'), '1')
            self.assertEqual(sentence_in_item.text, 'テキスト1')

        finally:
            # 一時ファイルを削除
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)

    def test_convert_xml_output_format(self):
        """出力XMLのフォーマットテスト（input.xml使用）"""
        input_file_path = "input.xml"

        # 入力ファイルが存在することを確認
        self.assertTrue(os.path.exists(input_file_path), f"入力ファイル {input_file_path} が存在しません")

        # 一時ファイルを作成（既存のoutput.xmlを上書きしないため）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as output_file:
            output_file_path = output_file.name

        try:
            # 変換実行
            convert_xml(input_file_path, output_file_path)

            # 出力ファイルをテキストとして読み込み
            with open(output_file_path, 'r', encoding='utf-8') as f:
                output_content = f.read()

            # XML宣言が正しいことを確認
            self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', output_content)

            # 有効なXMLとしてパースできることを確認
            try:
                minidom.parseString(output_content)
            except Exception as e:
                self.fail(f"出力XMLが無効です: {e}")

            # 基本的なXML構造が維持されていることを確認
            self.assertIn('<Law', output_content)
            self.assertIn('<LawBody>', output_content)
            self.assertIn('<MainProvision>', output_content)
            self.assertIn('<ParagraphSentence>', output_content)
            self.assertIn('<List>', output_content)
            self.assertIn('<ListSentence>', output_content)

        finally:
            # 一時ファイルを削除
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)


if __name__ == '__main__':
    unittest.main()
