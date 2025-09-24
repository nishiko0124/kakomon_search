#!/usr/bin/env bash
# コピー先: repo の ./data フォルダにローカルの kakomondata 内の CSV をコピーして git add/commit/push まで行います。
# 使い方: リポジトリルートで実行: ./scripts/copy_kakodata_to_repo.sh
set -euo pipefail

# 変更が必要な場合はここを編集
SRC_DIR="/Users/nishikawakotone/Documents/kotone_app/kakomondata"
DEST_DIR="data"
COMMIT_MSG="Add kakodata CSV files to repo data/ (automated)"

echo "確認: コピー元 = ${SRC_DIR}"
if [ ! -d "${SRC_DIR}" ]; then
  echo "エラー: コピー元ディレクトリが存在しません: ${SRC_DIR}"
  exit 1
fi

mkdir -p "${DEST_DIR}"

# Copy CSV files (overwrite if exist)
shopt -s nullglob
CSV_FILES=("${SRC_DIR}"/*.csv)
if [ ${#CSV_FILES[@]} -eq 0 ]; then
  echo "エラー: コピー元に CSV ファイルが見つかりません: ${SRC_DIR}"
  exit 1
fi

for f in "${CSV_FILES[@]}"; do
  echo "コピー: ${f} -> ${DEST_DIR}/$(basename "$f")"
  cp -f "$f" "${DEST_DIR}/"
done

# Git add/commit/push
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git add "${DEST_DIR}"
  git commit -m "${COMMIT_MSG}" || echo "コミットなし（変更なし）"
  echo "リモートへ push します。"
  git push
  echo "完了: CSV を ${DEST_DIR} にコピーしてコミット・push しました。"
else
  echo "このスクリプトは git リポジトリのルートで実行してください。"
  exit 1
fi
