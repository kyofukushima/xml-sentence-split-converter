# テストケース6: 子要素（ArithFormula、Sub、Sup）の欠落検証

このテストケースは、`Sentence`要素に子要素（`ArithFormula`、`Sub`、`Sup`など）が含まれている場合に、変換処理で子要素のテキストが失われる問題を検証します。

## 問題の詳細

検証結果ファイル（`02_H13null[2490]1347_R06null[2490]1000_R070401_2_validation_v2.md`）で確認された問題：

1. **ArithFormula要素の欠落**
   - 入力: `<Sentence>（式）　<ArithFormula>Ｌｗ＝...</ArithFormula></Sentence>`
   - 現在の出力: Column 2が空になる（ArithFormulaの内容が失われる）
   - 期待される出力: Column 2にArithFormula要素が含まれる

2. **Sup/Sub要素の欠落**
   - 入力: `<Sentence>Ｌｗ　単位面積あたりの必要壁量（単位　１ｍ<Sup>２</Sup>につきｃｍ）</Sentence>`
   - 現在の出力: `<Sup>２</Sup>`の部分が失われる
   - 期待される出力: Sup要素が保持される

3. **全角スペースの削除**
   - 入力: `<Sentence>Ｃ<Sub>０</Sub>　０．２...</Sentence>`
   - 現在の出力: 全角スペースが削除される
   - 期待される出力: 全角スペースで正しく分割される

## テスト内容

- **入力**: `test_with_arithformula.xml`
  - Sentence要素にArithFormula、Sub、Sup要素を含む
  - 冒頭10文字以内に全角スペースがある場合の分割処理をテスト

- **期待値**: `test_with_arithformula_expected.xml`
  - 子要素が正しく保持される
  - 全角スペースで正しく分割される

## 期待される動作

変換処理で以下の点が確認される必要があります：

1. `ArithFormula`要素がColumn 2に正しく配置される
2. `Sub`、`Sup`要素が正しく保持される
3. 全角スペースで分割される場合、子要素も適切に処理される

## 現在の問題

`xml_converter.py`の`convert_sentence_to_list`関数では、`sentence_elem.text`のみを処理しており、子要素のテキストが失われています。

## テスト結果

**注意**: このテストケースは現在の実装では失敗します。これは問題を検証するためのテストケースです。

現在の実装では以下の問題が確認されます：
1. `ArithFormula`要素の内容が失われる
2. `Sup`要素の内容が失われる
3. 全角スペースで分割する際に子要素が適切に処理されない

このテストケースは、これらの問題を検証し、修正後の動作確認に使用します。
