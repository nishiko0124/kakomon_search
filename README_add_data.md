手順: ローカルの CSV をリポジトリの `data/` に追加して push する

方法1 (推奨・簡単): スクリプトを使う
1. ターミナルでリポジトリルートに移動:

```bash
cd /Users/nishikawakotone/Documents/kotone_app/kakomon_search_app
```

2. スクリプトに実行権限を与えて実行:

```bash
chmod +x scripts/copy_kakodata_to_repo.sh
./scripts/copy_kakodata_to_repo.sh
```

このスクリプトは `SRC_DIR` (デフォルト: `/Users/nishikawakotone/Documents/kotone_app/kakomondata`) から `data/` に CSV をコピーし、`git add` -> `git commit` -> `git push` を自動で行います。

方法2 (手動):
1. コピー先ディレクトリを作成

```bash
mkdir -p data
cp /Users/nishikawakotone/Documents/kotone_app/kakomondata/*.csv data/
```

2. Git に追加してコミット

```bash
git add data
git commit -m "Add kakodata CSV files to repo data/"
git push
```

注意:
- Streamlit Community Cloud にデプロイする場合、リポジトリに `data/` が含まれていればデプロイ環境から `data/` にある CSV にアクセスできます。
- CSV が大きい場合はリポジトリにコミットすると push が遅くなります。その場合は外部ホスティング（S3等）を検討してください。