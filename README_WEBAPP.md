# XML Sentence Split Converter - Webアプリケーション

Streamlitを使用したWebアプリケーション版です。

## ローカルでの実行方法

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. アプリケーションの起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` に自動的にアクセスします。

## Streamlit Cloudへのデプロイ

### 1. GitHubリポジトリの準備

以下のファイルが必要です：

```
your-repo/
├── app.py                    # Streamlitアプリ本体
├── requirements.txt           # 依存パッケージ
├── xml_converter.py          # XML変換スクリプト
├── xml_content_validator_v2.py # XML検証スクリプト
└── README.md                 # このファイル
```

### 2. GitHubにプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/your-repo-name.git
git push -u origin main
```

### 3. Streamlit Cloudでデプロイ

1. [Streamlit Cloud](https://streamlit.io/cloud)にアクセス
2. GitHubアカウントでログイン
3. 「New app」をクリック
4. リポジトリを選択
5. メインファイルパスに `app.py` を指定
6. 「Deploy」をクリック

数分でデプロイが完了し、公開URLが生成されます。

## Hugging Face Spacesへのデプロイ（オプション）

StreamlitアプリはHugging Face Spacesでも動作します。

### 1. Hugging Faceアカウントの作成

1. [Hugging Face](https://huggingface.co/)でアカウントを作成
2. 新しいSpaceを作成（SDK: Streamlit、CPU無料プランでOK）

### 2. リポジトリの準備

以下のファイルが必要です：

```
your-repo/
├── app.py                    # Streamlitアプリ本体
├── requirements.txt           # 依存パッケージ
├── xml_converter.py          # XML変換スクリプト
├── xml_content_validator_v2.py # XML検証スクリプト
└── README.md                 # このファイル
```

### 3. GitHubリポジトリにプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://huggingface.co/spaces/your-username/your-space-name
git push -u origin main
```

### 4. 自動デプロイ

Hugging Face Spacesが自動的にデプロイを開始します。数分で完了します。

## 機能

### 単一ファイル処理
- XMLファイルを1つずつ変換
- 変換後の検証オプション
- 変換結果をダウンロード

### 複数ファイル一括処理
- 複数のXMLファイルを同時に処理
- ZIPファイルとしてダウンロード
- 再帰的検索オプション（サブフォルダも含む）

## 使い方

1. **単一ファイル処理**タブまたは**複数ファイル一括処理**タブを選択
2. XMLファイルをアップロード
3. 必要に応じてオプションを設定
4. 「変換実行」または「一括変換実行」ボタンをクリック
5. 変換結果をダウンロード

## 注意事項

- XMLファイルはUTF-8エンコーディングである必要があります
- 大きなファイルの処理には時間がかかる場合があります
- Streamlit Cloudの無料プランでは、リソースに制限があります
