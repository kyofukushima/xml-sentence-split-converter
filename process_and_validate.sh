#!/bin/bash

# XML変換処理と検証の一連スクリプト
# 使用方法: ./process_and_validate.sh [input_dir] [output_dir] [-r|--recursive]

set -e  # エラーが発生したら停止

# 引数解析
RECURSIVE=false
INPUT_DIR=""
OUTPUT_DIR=""

for arg in "$@"; do
    case $arg in
        -r|--recursive)
            RECURSIVE=true
            shift
            ;;
        *)
            if [ -z "$INPUT_DIR" ]; then
                INPUT_DIR="$arg"
            elif [ -z "$OUTPUT_DIR" ]; then
                OUTPUT_DIR="$arg"
            fi
            ;;
    esac
done

# デフォルト値設定
INPUT_DIR="${INPUT_DIR:-input}"
OUTPUT_DIR="${OUTPUT_DIR:-output}"

echo "=== XML変換処理と検証スクリプト ==="
echo "入力フォルダ: $INPUT_DIR"
echo "出力フォルダ: $OUTPUT_DIR"
if [ "$RECURSIVE" = true ]; then
    echo "検索モード: 再帰的（サブフォルダ含む）"
else
    echo "検索モード: 直下のみ（サブフォルダ除外）"
fi
echo

# 入力フォルダの存在確認
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ エラー: 入力フォルダ '$INPUT_DIR' が存在しません。"
    exit 1
fi

# 出力フォルダの作成（存在しない場合）
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "📁 出力フォルダ '$OUTPUT_DIR' を作成します。"
    mkdir -p "$OUTPUT_DIR"
fi

# 入力フォルダ内のXMLファイル数を確認
if [ "$RECURSIVE" = true ]; then
    XML_COUNT=$(find "$INPUT_DIR" -name "*.xml" | wc -l)
else
    XML_COUNT=$(find "$INPUT_DIR" -maxdepth 1 -name "*.xml" | wc -l)
fi
if [ "$XML_COUNT" -eq 0 ]; then
    echo "❌ エラー: 入力フォルダ '$INPUT_DIR' にXMLファイルが見つかりません。"
    exit 1
fi

echo "📊 処理対象ファイル数: $XML_COUNT 個"
echo

# XML変換処理実行
echo "🔄 XML変換処理を開始します..."
if [ "$RECURSIVE" = true ]; then
    if python3 xml_converter.py "$INPUT_DIR" "$OUTPUT_DIR" --recursive; then
        echo "✅ XML変換処理が完了しました。"
    else
        echo "❌ エラー: XML変換処理に失敗しました。"
        exit 1
    fi
else
    if python3 xml_converter.py "$INPUT_DIR" "$OUTPUT_DIR"; then
        echo "✅ XML変換処理が完了しました。"
    else
        echo "❌ エラー: XML変換処理に失敗しました。"
        exit 1
    fi
fi

echo

# 検証処理
echo "🔍 変換結果の検証を開始します..."
VALIDATION_PASSED=0
VALIDATION_FAILED=0

# 検証結果保存用のフォルダ作成
VALIDATION_DIR="$OUTPUT_DIR/validation_results"
mkdir -p "$VALIDATION_DIR"

# 全体サマリーレポートファイル
SUMMARY_REPORT="$VALIDATION_DIR/validation_summary.md"

# 出力フォルダ内の各XMLファイルを検証
for output_file in "$OUTPUT_DIR"/*.xml; do
    if [ ! -f "$output_file" ]; then
        continue
    fi

    filename=$(basename "$output_file")
    basename_no_ext=$(basename "$filename" .xml)
    input_file="$INPUT_DIR/$filename"

    if [ ! -f "$input_file" ]; then
        echo "⚠️  警告: 対応する入力ファイルが見つかりません: $filename"
        continue
    fi

    echo "検証中: $filename"

    # 個別検証結果ファイル
    validation_result_file="$VALIDATION_DIR/${basename_no_ext}_validation.md"

    # xml_content_validator_v2.pyで検証し、結果をファイルに保存
    if python3 xml_content_validator_v2.py "$input_file" "$output_file" --max-diff 5 --output "$validation_result_file" > /dev/null 2>&1; then
        echo "  ✅ 検証成功: $filename"
        echo "     📄 結果: $validation_result_file"
        ((VALIDATION_PASSED++))
    else
        echo "  ❌ 検証失敗: $filename"
        echo "     📄 結果: $validation_result_file"
        echo "    詳細:"
        python3 xml_content_validator_v2.py "$input_file" "$output_file" --max-diff 3 | sed 's/^/      /'
        ((VALIDATION_FAILED++))
        echo
    fi
done

# サマリーレポート作成
echo
echo "📊 検証結果サマリーを作成します..."

# 変換エラー情報を読み込む
CONVERSION_ERROR_FILE="$OUTPUT_DIR/validation_results/conversion_errors.md"
CONVERSION_ERROR_COUNT=0
if [ -f "$CONVERSION_ERROR_FILE" ]; then
    # Markdownファイルからエラー数を取得（"### "で始まる行の数をカウント）
    CONVERSION_ERROR_COUNT=$(grep -c "^### " "$CONVERSION_ERROR_FILE" 2>/dev/null || echo "0")
fi

cat > "$SUMMARY_REPORT" << EOF
# XML変換・検証処理結果サマリー

## 処理概要
- **実行日時**: $(date '+%Y-%m-%d %H:%M:%S')
- **入力フォルダ**: $INPUT_DIR
- **出力フォルダ**: $OUTPUT_DIR
- **総処理ファイル数**: $XML_COUNT

## 変換結果
- **✅ 変換成功**: $((XML_COUNT - CONVERSION_ERROR_COUNT)) ファイル
EOF

if [ "$CONVERSION_ERROR_COUNT" -gt 0 ]; then
    cat >> "$SUMMARY_REPORT" << EOF
- **❌ 変換失敗**: $CONVERSION_ERROR_COUNT ファイル

詳細は[変換エラー詳細](conversion_errors.md)を参照してください。

EOF
fi

cat >> "$SUMMARY_REPORT" << EOF
## 検証結果
- **✅ 検証成功**: $VALIDATION_PASSED ファイル
- **❌ 検証失敗**: $VALIDATION_FAILED ファイル

## 詳細結果

EOF

# 各ファイルの結果をサマリーに追加
for output_file in "$OUTPUT_DIR"/*.xml; do
    if [ ! -f "$output_file" ]; then
        continue
    fi

    filename=$(basename "$output_file")
    basename_no_ext=$(basename "$filename" .xml)
    input_file="$INPUT_DIR/$filename"

    if [ ! -f "$input_file" ]; then
        continue
    fi

    validation_result_file="$VALIDATION_DIR/${basename_no_ext}_validation.md"

    if [ -f "$validation_result_file" ]; then
        # 検証結果ファイルが存在する場合、リンクを追加
        echo "- **$filename**: [検証結果詳細](${basename_no_ext}_validation.md)" >> "$SUMMARY_REPORT"
    fi
done

# 全体の結果メッセージを追加
if [ "$VALIDATION_FAILED" -eq 0 ] && [ "$CONVERSION_ERROR_COUNT" -eq 0 ]; then
    echo "" >> "$SUMMARY_REPORT"
    echo "## 🎉 処理結果" >> "$SUMMARY_REPORT"
    echo "すべてのファイルが正常に処理・検証されました！" >> "$SUMMARY_REPORT"
else
    echo "" >> "$SUMMARY_REPORT"
    echo "## ⚠️ 処理結果" >> "$SUMMARY_REPORT"
    if [ "$CONVERSION_ERROR_COUNT" -gt 0 ]; then
        echo "一部のファイルで変換エラーが発生しました。上記の変換エラー詳細を確認してください。" >> "$SUMMARY_REPORT"
    fi
    if [ "$VALIDATION_FAILED" -gt 0 ]; then
        echo "一部のファイルで検証エラーが発生しました。詳細な検証結果ファイルを確認してください。" >> "$SUMMARY_REPORT"
    fi
fi

# 変換エラーファイルへのリンクを追加
if [ -f "$CONVERSION_ERROR_FILE" ]; then
    echo "" >> "$SUMMARY_REPORT"
    echo "## 関連ファイル" >> "$SUMMARY_REPORT"
    echo "- [変換エラー詳細](conversion_errors.md)" >> "$SUMMARY_REPORT"
fi

echo
echo "=== 処理結果サマリー ==="
echo "総処理ファイル数: $XML_COUNT"
if [ "$CONVERSION_ERROR_COUNT" -gt 0 ]; then
    echo "変換成功: $((XML_COUNT - CONVERSION_ERROR_COUNT))"
    echo "変換失敗: $CONVERSION_ERROR_COUNT"
fi
echo "検証成功: $VALIDATION_PASSED"
echo "検証失敗: $VALIDATION_FAILED"
echo "📁 検証結果保存先: $VALIDATION_DIR"
echo "📄 サマリーレポート: $SUMMARY_REPORT"
if [ -f "$CONVERSION_ERROR_FILE" ]; then
    echo "📄 変換エラー詳細: $CONVERSION_ERROR_FILE"
fi

if [ "$VALIDATION_FAILED" -eq 0 ] && [ "$CONVERSION_ERROR_COUNT" -eq 0 ]; then
    echo "🎉 すべてのファイルが正常に処理・検証されました！"
    exit 0
else
    echo "⚠️  一部のファイルでエラーが発生しました。詳細を確認してください。"
    exit 1
fi
