#!/bin/bash

# 単体テスト実行スクリプト
# 使用方法: ./run_unit_test.sh [test_case_name]
# 引数なしの場合、すべてのテストケースを実行

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# テスト結果を保存するディレクトリ
TEST_RESULTS_DIR="$SCRIPT_DIR/test_results"
mkdir -p "$TEST_RESULTS_DIR"

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# テスト結果のカウンター
PASSED=0
FAILED=0
TOTAL=0

# XMLファイルを比較する関数
compare_xml_files() {
    local expected_file="$1"
    local actual_file="$2"
    
    if [ ! -f "$expected_file" ]; then
        echo "  ❌ 期待値ファイルが見つかりません: $expected_file"
        return 1
    fi
    
    if [ ! -f "$actual_file" ]; then
        echo "  ❌ 実際の出力ファイルが見つかりません: $actual_file"
        return 1
    fi
    
    # XMLファイルを正規化して比較（空白や改行の違いを無視）
    # xmllintを使用して正規化（存在する場合）
    if command -v xmllint &> /dev/null; then
        expected_normalized=$(xmllint --format "$expected_file" 2>/dev/null || cat "$expected_file")
        actual_normalized=$(xmllint --format "$actual_file" 2>/dev/null || cat "$actual_file")
        
        # 正規化されたXMLを一時ファイルに保存
        expected_tmp=$(mktemp)
        actual_tmp=$(mktemp)
        echo "$expected_normalized" > "$expected_tmp"
        echo "$actual_normalized" > "$actual_tmp"
        
        # diffで比較
        if diff -q "$expected_tmp" "$actual_tmp" > /dev/null 2>&1; then
            rm -f "$expected_tmp" "$actual_tmp"
            return 0
        else
            echo "  ⚠️  XMLファイルに差異があります:"
            diff -u "$expected_tmp" "$actual_tmp" | head -20 | sed 's/^/    /'
            rm -f "$expected_tmp" "$actual_tmp"
            return 1
        fi
    else
        # xmllintが存在しない場合は、単純なdiffで比較
        if diff -q "$expected_file" "$actual_file" > /dev/null 2>&1; then
            return 0
        else
            echo "  ⚠️  XMLファイルに差異があります:"
            diff -u "$expected_file" "$actual_file" | head -20 | sed 's/^/    /'
            return 1
        fi
    fi
}

# 単一のテストケースを実行
run_test_case() {
    local test_case="$1"
    local test_case_dir="$SCRIPT_DIR/$test_case"
    
    if [ ! -d "$test_case_dir" ]; then
        echo -e "${RED}❌ テストケースが見つかりません: $test_case${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${YELLOW}=== テストケース: $test_case ===${NC}"
    
    local output_dir="$test_case_dir/output"
    local temp_input_dir="$test_case_dir/temp_input"
    
    # 出力ディレクトリをクリーンアップ
    rm -rf "$output_dir" "$temp_input_dir"
    mkdir -p "$output_dir"
    
    # テストケースの種類を判定
    if [ "$test_case" = "test_case_04_no_input_dir" ]; then
        # 入力フォルダ不存在エラーのテスト
        echo "  テスト: 存在しない入力フォルダでのエラーハンドリング"
        cd "$PROJECT_ROOT"
        if ./process_and_validate.sh nonexistent_folder output 2>&1 | grep -q "入力フォルダ.*が存在しません"; then
            echo -e "  ${GREEN}✅ テスト成功: 適切なエラーメッセージが表示されました${NC}"
            return 0
        else
            echo -e "  ${RED}❌ テスト失敗: 期待されるエラーメッセージが表示されませんでした${NC}"
            return 1
        fi
    
    elif [ "$test_case" = "test_case_05_no_xml_files" ]; then
        # XMLファイル不存在エラーのテスト
        echo "  テスト: XMLファイルが存在しない場合のエラーハンドリング"
        cd "$PROJECT_ROOT"
        mkdir -p "$temp_input_dir"
        if ./process_and_validate.sh "$temp_input_dir" "$output_dir" 2>&1 | grep -q "XMLファイルが見つかりません"; then
            rm -rf "$temp_input_dir"
            echo -e "  ${GREEN}✅ テスト成功: 適切なエラーメッセージが表示されました${NC}"
            return 0
        else
            rm -rf "$temp_input_dir"
            echo -e "  ${RED}❌ テスト失敗: 期待されるエラーメッセージが表示されませんでした${NC}"
            return 1
        fi
    
    else
        # 正常系のテストケース
        # テストケースフォルダ内の入力XMLファイルを検索（_expectedが付いていないもの）
        local input_files=()
        while IFS= read -r -d '' file; do
            # _expected.xmlで終わるファイルは除外
            if [[ ! "$file" =~ _expected\.xml$ ]]; then
                input_files+=("$file")
            fi
        done < <(find "$test_case_dir" -maxdepth 1 -name "*.xml" -type f -print0)
        
        if [ ${#input_files[@]} -eq 0 ]; then
            echo -e "  ${RED}❌ 入力XMLファイルが見つかりません${NC}"
            return 1
        fi
        
        # 期待値XMLファイルを検索（_expected.xmlで終わるもの）
        local expected_files=()
        while IFS= read -r -d '' file; do
            if [[ "$file" =~ _expected\.xml$ ]]; then
                expected_files+=("$file")
            fi
        done < <(find "$test_case_dir" -maxdepth 1 -name "*_expected.xml" -type f -print0)
        
        if [ ${#expected_files[@]} -eq 0 ]; then
            echo -e "  ${RED}❌ 期待値XMLファイルが見つかりません${NC}"
            return 1
        fi
        
        # 一時的な入力フォルダを作成し、入力XMLファイルをコピー
        mkdir -p "$temp_input_dir"
        for input_file in "${input_files[@]}"; do
            cp "$input_file" "$temp_input_dir/$(basename "$input_file")"
        done
        
        # プロジェクトルートに移動
        cd "$PROJECT_ROOT"
        
        # テストケースに応じたスクリプト実行
        if [ "$test_case" = "test_case_03_recursive" ]; then
            echo "  テスト: 再帰的検索オプション付きでの実行"
            if ./process_and_validate.sh "$temp_input_dir" "$output_dir" --recursive > "$TEST_RESULTS_DIR/${test_case}_output.log" 2>&1; then
                echo "  ✓ スクリプト実行成功"
            else
                echo -e "  ${RED}❌ スクリプト実行失敗${NC}"
                cat "$TEST_RESULTS_DIR/${test_case}_output.log" | sed 's/^/    /'
                rm -rf "$temp_input_dir"
                return 1
            fi
        else
            echo "  テスト: 通常実行"
            if ./process_and_validate.sh "$temp_input_dir" "$output_dir" > "$TEST_RESULTS_DIR/${test_case}_output.log" 2>&1; then
                echo "  ✓ スクリプト実行成功"
            else
                echo -e "  ${RED}❌ スクリプト実行失敗${NC}"
                cat "$TEST_RESULTS_DIR/${test_case}_output.log" | sed 's/^/    /'
                rm -rf "$temp_input_dir"
                return 1
            fi
        fi
        
        # 期待値と実際の出力を比較
        local comparison_failed=0
        
        for expected_file in "${expected_files[@]}"; do
            # 期待値ファイル名から_expected.xmlを削除して入力ファイル名を取得
            expected_basename=$(basename "$expected_file")
            input_basename="${expected_basename/_expected.xml/.xml}"
            actual_file="$output_dir/$input_basename"
            
            echo "  比較中: $input_basename"
            if compare_xml_files "$expected_file" "$actual_file"; then
                echo -e "    ${GREEN}✅ 一致${NC}"
            else
                echo -e "    ${RED}❌ 不一致${NC}"
                comparison_failed=1
            fi
        done
        
        # 一時的な入力フォルダを削除
        rm -rf "$temp_input_dir"
        
        if [ $comparison_failed -eq 1 ]; then
            return 1
        else
            return 0
        fi
    fi
}

# メイン処理
cd "$PROJECT_ROOT"

# 引数が指定されている場合はそのテストケースのみ実行
if [ $# -gt 0 ]; then
    TEST_CASES=("$@")
else
    # すべてのテストケースを検出
    TEST_CASES=()
    for dir in "$SCRIPT_DIR"/test_case_*; do
        if [ -d "$dir" ]; then
            TEST_CASES+=("$(basename "$dir")")
        fi
    done
fi

echo "=========================================="
echo "  単体テスト実行"
echo "=========================================="
echo "テストケース数: ${#TEST_CASES[@]}"
echo ""

# 各テストケースを実行
for test_case in "${TEST_CASES[@]}"; do
    TOTAL=$((TOTAL + 1))
    if run_test_case "$test_case"; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
done

# 結果サマリー
echo ""
echo "=========================================="
echo "  テスト結果サマリー"
echo "=========================================="
echo -e "総テスト数: $TOTAL"
echo -e "${GREEN}成功: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}失敗: $FAILED${NC}"
else
    echo -e "失敗: $FAILED"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 すべてのテストが成功しました！${NC}"
    exit 0
else
    echo -e "${RED}⚠️  一部のテストが失敗しました。詳細を確認してください。${NC}"
    exit 1
fi
