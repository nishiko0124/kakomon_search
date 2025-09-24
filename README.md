# Kakomon CSV 検索アプリ

簡単なStreamlitアプリケーションです。CSVを読み込み、任意の2列に対して部分一致検索（AND）を行えます。また、UIから行を追加できます。

## 使い方

1. Python環境を用意し、依存パッケージをインストールします:

```bash
pip install -r requirements.txt
```

2. デフォルトCSVパスは `/Users/nishikawakotone/Documents/kotone_app/kakomondata/kakodata.csv` です。別のCSVをサイドバーからアップロードして使うこともできます。

3. アプリを起動します:

```bash
streamlit run app.py
```

## 注意点
- 行追加時に既存ファイルがあるとバックアップ（同ディレクトリに `kakodata.backup_<timestamp>.csv`）が作成されます。
- 大文字小文字を区別せず部分一致で検索します。
