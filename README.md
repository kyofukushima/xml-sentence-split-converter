# XML Sentence Split Converter

XMLファイル内のSentence要素をList要素に変換するスクリプトです。

## 機能

- **条件付き変換**: ParagraphSentence内にSentence要素が2つ以上の場合のみ変換を実行
- Sentence要素内のテキストを空白で分割してColumn要素に変換
- 冒頭10文字以内に空白がある場合のみ分割処理を実行
- 最初の分割点以外の空白は保持
- フォルダ内の複数ファイルを一括処理可能

## 使用方法

### 単一ファイル処理
```bash
python3 xml_converter.py input.xml output.xml
```

### フォルダ一括処理
```bash
# デフォルトでは直下のXMLファイルのみ処理（サブフォルダは除外）
python3 xml_converter.py input_folder output_folder

# サブフォルダも再帰的に検索（オプション）
python3 xml_converter.py input_folder output_folder --recursive
# または
python3 xml_converter.py input_folder output_folder -r
```

### デフォルト動作
```bash
python3 xml_converter.py  # input.xml → output.xml
```

### 一括処理 + 検証スクリプト
```bash
# デフォルトフォルダを使用（input/ → output/）
# デフォルトでは直下のXMLファイルのみ処理（サブフォルダは除外）
./process_and_validate.sh

# カスタムフォルダを指定
./process_and_validate.sh input output

# サブフォルダも再帰的に検索（オプション）
./process_and_validate.sh input output --recursive
# または
./process_and_validate.sh input output -r

# 現在のディレクトリを処理
./process_and_validate.sh . ./results
```

**検証結果の保存:** 各ファイルの検証結果がMarkdown形式で`output/validation_results/`に保存されます。

**実行例:**
```
=== XML変換処理と検証スクリプト ===
入力フォルダ: input
出力フォルダ: output

📊 処理対象ファイル数: 5 個

🔄 XML変換処理を開始します...
✅ XML変換処理が完了しました。

🔍 変換結果の検証を開始します...
検証中: file1.xml
  ✅ 検証成功: file1.xml
検証中: file2.xml
  ✅ 検証成功: file2.xml

=== 処理結果サマリー ===
総処理ファイル数: 5
検証成功: 5
検証失敗: 0
🎉 すべてのファイルが正常に処理・検証されました！
```

### パイプライン処理
findコマンドと組み合わせた処理例：

```bash
# 特定のディレクトリ内の全XMLファイルを処理
find /path/to/xml/files -name "*.xml" -exec python3 xml_converter.py {} output_dir/ \;

# xargsを使った並列処理
find input_dir -name "*.xml" | xargs -I {} python3 xml_converter.py {} output_dir/

# 処理結果の検証を追加
find input_dir -name "*.xml" | xargs -I {} sh -c 'python3 xml_converter.py "$1" output_dir/ && python3 xml_content_validator_v2.py "$1" "output_dir/$(basename $1)"' -- {}
```

## 検証機能

`xml_content_validator_v2.py`を使用して変換前後の値を比較できます：

```bash
# 標準出力に結果を表示
python3 xml_content_validator_v2.py input.xml output.xml

# 結果をファイルに出力
python3 xml_content_validator_v2.py input.xml output.xml --output validation_result.txt
```

**オプション:**
- `--output, -o`: 出力ファイルパスを指定（拡張子なしの場合は自動的に.mdが付与されます）
- `--max-diff`: 表示する差異の最大数（デフォルト: 10）

**出力形式:**
- **標準出力**: コンソールに結果を表示
- **ファイル出力**: Markdown形式(.md)で保存され、見出し・リスト・コードブロックを使用した読みやすい形式

**注意**: 変換により値が分割されるため、検証では構造変化が検知されますが、これは正常な動作です。

## Webアプリケーション版

Streamlitを使用したWebアプリケーション版も利用可能です。

### ローカルでの実行

```bash
pip install -r requirements.txt
streamlit run app.py
```

ブラウザで `http://localhost:8501` に自動的にアクセスします。

### Streamlit Cloud / Hugging Face Spacesへのデプロイ

詳細は `README_WEBAPP.md` を参照してください。

## 変換例

**変換前:**
```xml
<Sentence Num="4">１　項目1</Sentence>
```

**変換後:**
```xml
<List>
  <ListSentence>
    <Column Num="1">
      <Sentence Num="1">１</Sentence>
    </Column>
    <Column Num="2">
      <Sentence Num="1">項目1</Sentence>
    </Column>
  </ListSentence>
</List>
```
