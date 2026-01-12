# 単体テスト

`process_and_validate.sh`スクリプトの単体テストです。

## テストケース一覧

### test_case_01_default_args
**正常系**: デフォルト引数（input/outputフォルダ）での実行テスト

- **入力**: `test_input.xml`
- **期待値**: `test_input_expected.xml`
- **説明**: 基本的なXML変換処理が正常に動作することを確認

### test_case_02_custom_folders
**正常系**: カスタムフォルダ指定での実行テスト

- **入力**: `custom_test.xml`
- **期待値**: `custom_test_expected.xml`
- **説明**: カスタムの入力/出力フォルダを指定した場合の動作を確認

### test_case_03_recursive
**正常系**: 再帰的検索オプション付きでの実行テスト

- **入力**: `recursive_test.xml`
- **期待値**: `recursive_test_expected.xml`
- **説明**: `--recursive`オプションを使用した場合、サブフォルダ内のXMLファイルも処理されることを確認

### test_case_04_no_input_dir
**異常系**: 入力フォルダが存在しない場合のエラーハンドリングテスト

- **説明**: 存在しない入力フォルダを指定した場合、適切なエラーメッセージが表示され、終了コード1で終了することを確認

### test_case_05_no_xml_files
**異常系**: XMLファイルが存在しない場合のエラーハンドリングテスト

- **入力**: XMLファイルなし（空のフォルダ）
- **説明**: 入力フォルダにXMLファイルが存在しない場合、適切なエラーメッセージが表示され、終了コード1で終了することを確認

### test_case_06_child_elements_missing
**問題検証**: 子要素（ArithFormula、Sub、Sup）の欠落問題を検証するテスト

- **入力**: `test_with_arithformula.xml`
- **期待値**: `test_with_arithformula_expected.xml`
- **説明**: `Sentence`要素に`ArithFormula`、`Sub`、`Sup`などの子要素が含まれている場合、変換処理で子要素のテキストが失われる問題を検証します
- **注意**: このテストケースは現在の実装では失敗します。問題を検証するためのテストケースです

## テストの実行方法

### すべてのテストケースを実行
```bash
cd unit_test
./run_unit_test.sh
```

### 特定のテストケースを実行
```bash
cd unit_test
./run_unit_test.sh test_case_01_default_args
```

### 複数のテストケースを実行
```bash
cd unit_test
./run_unit_test.sh test_case_01_default_args test_case_02_custom_folders
```

## テスト結果

テスト結果は以下の場所に保存されます：
- **ログファイル**: `unit_test/test_results/{test_case_name}_output.log`
- **出力ファイル**: `unit_test/{test_case_name}/output/`

## テストの追加方法

新しいテストケースを追加する場合：

1. `unit_test/test_case_{番号}_{説明}/` フォルダを作成
2. テストケースフォルダ直下にテスト用の入力XMLファイルを配置（例: `test_input.xml`）
3. テストケースフォルダ直下に期待値XMLファイルを配置（`_expected.xml`サフィックス付き、例: `test_input_expected.xml`）
4. 必要に応じて `README.md` にテストケースの説明を追加

テスト実行スクリプトは自動的に新しいテストケースを検出して実行します。

**ファイル命名規則:**
- 入力XML: `{ファイル名}.xml`
- 期待値XML: `{ファイル名}_expected.xml`
