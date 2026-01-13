#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XML Sentence Split Converter - Streamlit Webアプリケーション
"""

import streamlit as st
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import zipfile
import io

# 既存のモジュールをインポート
from xml_converter import convert_xml, process_folder
from xml_content_validator_v2 import extract_values_from_xml_structure, compare_value_lists

# XMLプレビューの最大表示行数
MAX_PREVIEW_LINES = 1000
PREVIEW_HEAD_LINES = 500  # 最初に表示する行数
PREVIEW_TAIL_LINES = 500  # 最後に表示する行数

def truncate_xml_preview(xml_content, max_lines=MAX_PREVIEW_LINES, head_lines=PREVIEW_HEAD_LINES, tail_lines=PREVIEW_TAIL_LINES):
    """XMLコンテンツをプレビュー用に切り詰める"""
    lines = xml_content.split('\n')
    total_lines = len(lines)
    
    if total_lines <= max_lines:
        # 行数が少ない場合はそのまま返す
        return xml_content, total_lines
    
    # 最初のN行と最後のM行を取得
    head_part = '\n'.join(lines[:head_lines])
    tail_part = '\n'.join(lines[-tail_lines:])
    
    truncated_content = f"{head_part}\n\n... （{total_lines - head_lines - tail_lines} 行を省略） ...\n\n{tail_part}"
    
    return truncated_content, total_lines

# ページ設定
st.set_page_config(
    page_title="XML Sentence Split Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# タイトル
st.title("📄 XML Sentence Split Converter")

# 機能説明（トグルで表示/非表示）
with st.expander("ℹ️ 機能説明", expanded=False):
    st.markdown(
        """
        XMLファイル内のSentence要素をList要素に変換するWebアプリケーションです。
        
        **機能:**
        - **条件付き変換**: ParagraphSentence内にSentence要素が10個以上の場合のみ変換を実行
        - Sentence要素内のテキストを空白で分割してColumn要素に変換
        - 冒頭10文字以内に空白がある場合のみ分割処理を実行
        - 子要素（ArithFormula、Sub、Supなど）を正しく処理
        """
    )

# タブを作成
tab1, tab2, tab3 = st.tabs(["単一ファイル処理", "複数ファイル一括処理", "使い方"])

with tab1:
    st.header("単一XMLファイルを変換します")
    
    uploaded_file = st.file_uploader(
        "XMLファイルをアップロード",
        type=["xml"],
        help="変換したいXMLファイルを選択してください"
    )
    
    process_button = st.button("変換実行", type="primary", use_container_width=True)
    
    if process_button and uploaded_file is not None:
        with st.spinner("変換処理中..."):
            try:
                # 一時ディレクトリを作成
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # アップロードされたファイルを一時ディレクトリに保存
                    input_path = temp_path / uploaded_file.name
                    with open(input_path, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    # 出力ファイル名を生成（入力ファイル名_split.xml）
                    input_file_path = Path(uploaded_file.name)
                    output_filename = f"{input_file_path.stem}_split{input_file_path.suffix}"
                    output_path = temp_path / output_filename
                    
                    # XML変換を実行
                    convert_xml(input_path, output_path)
                    
                    # 検証を自動実行
                    validation_result = ""
                    try:
                        values1 = extract_values_from_xml_structure(input_path)
                        values2 = extract_values_from_xml_structure(output_path)
                        result = compare_value_lists(values1, values2)
                        
                        if result['identical']:
                            validation_result = "✅ **検証結果: 成功**\n\nすべての値が同一です。"
                        else:
                            validation_result = "❌ **検証結果: 差異検出**\n\n"
                            if result['missing_in_2']:
                                validation_result += f"- ファイル2に欠落している値: {len(result['missing_in_2'])} 件\n"
                            if result['extra_in_2']:
                                validation_result += f"- ファイル2に追加されている値: {len(result['extra_in_2'])} 件\n"
                            if result['order_differences']:
                                validation_result += f"- 順序または内容の差異: {len(result['order_differences'])} 件\n"
                    except Exception as e:
                        validation_result = f"⚠️ 検証中にエラーが発生しました: {str(e)}"
                    
                    # 出力ファイルを読み込む
                    with open(output_path, 'rb') as f:
                        output_data = f.read()
                    
                    # XMLファイルを読み込んでプレビュー用に取得
                    with open(input_path, 'r', encoding='utf-8') as f:
                        input_xml_full = f.read()
                    with open(output_path, 'r', encoding='utf-8') as f:
                        output_xml_full = f.read()
                    
                    # XMLプレビュー用に切り詰め
                    input_xml_preview, input_total_lines = truncate_xml_preview(input_xml_full)
                    output_xml_preview, output_total_lines = truncate_xml_preview(output_xml_full)
                    
                    # 結果を表示
                    st.success(f"✅ **変換完了**\n\n- 入力ファイル: {uploaded_file.name}\n- 出力ファイル: {output_filename}")
                    
                    # 検証結果を表示
                    st.markdown(validation_result)
                    
                    # XMLプレビュー
                    col_preview1, col_preview2 = st.columns(2)
                    
                    with col_preview1:
                        preview_label = f"📄 変換前のXML（プレビュー）"
                        if input_total_lines > MAX_PREVIEW_LINES:
                            preview_label += f" - {input_total_lines:,}行中 {PREVIEW_HEAD_LINES}+{PREVIEW_TAIL_LINES}行を表示"
                        with st.expander(preview_label, expanded=False):
                            st.code(input_xml_preview, language="xml")
                    
                    with col_preview2:
                        preview_label = f"📄 変換後のXML（プレビュー）"
                        if output_total_lines > MAX_PREVIEW_LINES:
                            preview_label += f" - {output_total_lines:,}行中 {PREVIEW_HEAD_LINES}+{PREVIEW_TAIL_LINES}行を表示"
                        with st.expander(preview_label, expanded=False):
                            st.code(output_xml_preview, language="xml")
                    
                    # ダウンロードボタン
                    st.download_button(
                        label="変換結果をダウンロード",
                        data=output_data,
                        file_name=output_filename,
                        mime="application/xml",
                        type="primary",
                        use_container_width=True
                    )
                    
            except Exception as e:
                st.error(f"❌ **エラーが発生しました**\n\n{str(e)}")
                import traceback
                with st.expander("エラー詳細"):
                    st.code(traceback.format_exc())
    
    elif process_button and uploaded_file is None:
        st.warning("⚠️ ファイルをアップロードしてください。")

with tab2:
    st.header("複数のXMLファイルを一括変換します")
    
    uploaded_files = st.file_uploader(
        "XMLファイルを複数選択（Ctrl/Cmd+クリックで複数選択）",
        type=["xml"],
        accept_multiple_files=True,
        help="変換したいXMLファイルを複数選択してください"
    )
    
    recursive_option = st.checkbox("再帰的検索（サブフォルダも含む）", value=False)
    process_button_multi = st.button("一括変換実行", type="primary", use_container_width=True)
    
    if process_button_multi and uploaded_files:
        with st.spinner("一括変換処理中..."):
            try:
                # 一時ディレクトリを作成
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    input_dir = temp_path / "input"
                    output_dir = temp_path / "output"
                    input_dir.mkdir()
                    output_dir.mkdir()
                    
                    # アップロードされたファイルを一時ディレクトリにコピー
                    uploaded_file_names = []
                    for uploaded_file in uploaded_files:
                        dest_path = input_dir / uploaded_file.name
                        with open(dest_path, 'wb') as f:
                            f.write(uploaded_file.getvalue())
                        uploaded_file_names.append(uploaded_file.name)
                    
                    # 一括変換を実行
                    process_folder(input_dir, output_dir, recursive=recursive_option)
                    
                    # 検証を自動実行
                    validation_results = []
                    validation_dir = output_dir / "validation_results"
                    validation_dir.mkdir(exist_ok=True)
                    
                    for uploaded_file_name in uploaded_file_names:
                        input_file = input_dir / uploaded_file_name
                        output_file = output_dir / uploaded_file_name
                        
                        if output_file.exists():
                            try:
                                values1 = extract_values_from_xml_structure(input_file)
                                values2 = extract_values_from_xml_structure(output_file)
                                result = compare_value_lists(values1, values2)
                                
                                if result['identical']:
                                    validation_results.append(f"✅ {uploaded_file_name}: 検証成功")
                                else:
                                    validation_results.append(f"❌ {uploaded_file_name}: 差異検出 ({len(result['missing_in_2']) + len(result['extra_in_2']) + len(result['order_differences'])}件)")
                            except Exception as e:
                                validation_results.append(f"⚠️ {uploaded_file_name}: 検証エラー - {str(e)}")
                    
                    # ZIPファイルを作成（ファイル名を入力ファイル名_split.xml形式に変更）
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_path in output_dir.rglob("*.xml"):
                            # 元のファイル名から出力ファイル名を生成
                            original_filename = file_path.name
                            # 入力ファイル名と一致するものを探す
                            for uploaded_file_name in uploaded_file_names:
                                if original_filename == uploaded_file_name:
                                    # 入力ファイル名_split.xml形式に変更
                                    input_file_path = Path(uploaded_file_name)
                                    output_filename = f"{input_file_path.stem}_split{input_file_path.suffix}"
                                    zipf.write(file_path, output_filename)
                                    break
                            else:
                                # 一致しない場合はそのまま
                                zipf.write(file_path, file_path.relative_to(output_dir))
                    
                    zip_buffer.seek(0)
                    
                    # 結果を表示
                    st.success(f"✅ **一括変換完了**\n\n- 処理ファイル数: {len(uploaded_file_names)} 個\n- 出力フォルダ: output/")
                    
                    # 検証結果を表示
                    st.markdown("**検証結果:**")
                    for result in validation_results:
                        st.markdown(f"- {result}")
                    
                    # XMLプレビュー（最初のファイルのみ）
                    if uploaded_file_names:
                        first_file_name = uploaded_file_names[0]
                        first_input_file = input_dir / first_file_name
                        first_output_file = output_dir / first_file_name
                        
                        if first_output_file.exists():
                            try:
                                with open(first_input_file, 'r', encoding='utf-8') as f:
                                    first_input_xml_full = f.read()
                                with open(first_output_file, 'r', encoding='utf-8') as f:
                                    first_output_xml_full = f.read()
                                
                                # XMLプレビュー用に切り詰め
                                first_input_xml_preview, first_input_total_lines = truncate_xml_preview(first_input_xml_full)
                                first_output_xml_preview, first_output_total_lines = truncate_xml_preview(first_output_xml_full)
                                
                                st.markdown("---")
                                st.markdown(f"### 📄 XMLプレビュー（{first_file_name}）")
                                
                                col_preview1, col_preview2 = st.columns(2)
                                
                                with col_preview1:
                                    preview_label = f"📄 変換前のXML（プレビュー）"
                                    if first_input_total_lines > MAX_PREVIEW_LINES:
                                        preview_label += f" - {first_input_total_lines:,}行中 {PREVIEW_HEAD_LINES}+{PREVIEW_TAIL_LINES}行を表示"
                                    with st.expander(preview_label, expanded=False):
                                        st.code(first_input_xml_preview, language="xml")
                                
                                with col_preview2:
                                    preview_label = f"📄 変換後のXML（プレビュー）"
                                    if first_output_total_lines > MAX_PREVIEW_LINES:
                                        preview_label += f" - {first_output_total_lines:,}行中 {PREVIEW_HEAD_LINES}+{PREVIEW_TAIL_LINES}行を表示"
                                    with st.expander(preview_label, expanded=False):
                                        st.code(first_output_xml_preview, language="xml")
                            except Exception as e:
                                st.info(f"⚠️ プレビューの表示中にエラーが発生しました: {str(e)}")
                    
                    # ダウンロードボタン
                    st.download_button(
                        label="変換結果ZIPファイルをダウンロード",
                        data=zip_buffer.getvalue(),
                        file_name="converted_files.zip",
                        mime="application/zip",
                        type="primary",
                        use_container_width=True
                    )
                    
            except Exception as e:
                st.error(f"❌ **エラーが発生しました**\n\n{str(e)}")
                import traceback
                with st.expander("エラー詳細"):
                    st.code(traceback.format_exc())
    
    elif process_button_multi and not uploaded_files:
        st.warning("⚠️ ファイルをアップロードしてください。")

with tab3:
    st.markdown(
        """
        ## 使い方
        
        ### 単一ファイル処理
        1. 「単一ファイル処理」タブを開く
        2. XMLファイルをアップロード
        3. 「変換実行」ボタンをクリック
        4. 変換結果と検証結果を確認
        5. 変換結果をダウンロード
        
        ### 複数ファイル一括処理
        1. 「複数ファイル一括処理」タブを開く
        2. 複数のXMLファイルを選択（Ctrl/Cmd+クリックで複数選択）
        3. 必要に応じてオプションを設定
        4. 「一括変換実行」ボタンをクリック
        5. ZIPファイルをダウンロード
        
        ## 変換ルール
        - ParagraphSentence内にSentence要素が**10個以上**ある場合のみ変換
        - 冒頭10文字以内に空白がある場合のみ分割処理を実行
        - 子要素（ArithFormula、Sub、Supなど）も正しく処理されます
        
        ## 注意事項
        - XMLファイルはUTF-8エンコーディングである必要があります
        - 大きなファイルの処理には時間がかかる場合があります
        """
    )

# サイドバー
with st.sidebar:
    st.markdown("**バージョン:** 1.0.0")
