"""
CSV読み込み・検索・追記のユーティリティ
"""
from pathlib import Path
import pandas as pd
import shutil
import time


def load_csv(path: str) -> pd.DataFrame:
    """CSVを読み込み、DataFrameを返す。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(p)


def load_csvs_from_dir(dir_path: str) -> pd.DataFrame:
    """指定ディレクトリ内の全てのCSVを読み込み、結合して返す。
    ファイルがない場合は空のDataFrameを返す。
    """
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    csv_files = sorted(p.glob('*.csv'))
    if not csv_files:
        return pd.DataFrame()
    dfs = []
    for f in csv_files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception:
            # skip unreadable files
            continue
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def get_columns(path: str) -> list:
    """CSVのカラム名リストを返す。"""
    df = load_csv(path)
    return list(df.columns)


def search_df(df: pd.DataFrame, filters: list, combine: str = 'AND') -> pd.DataFrame:
    """検索を行う。

    filters: list of (column_name, query_string, mode)
      mode: 'contains' | 'startswith' | 'regex'
    query が空文字または空白のみの場合はそのフィルタは無視される。
    大文字小文字は無視して検索（case-insensitive）、ただし'regex'はユーザ指定に従う。
    複数フィルタはANDで結合。
    """
    if df is None or df.empty:
        return df

    if combine not in ('AND', 'OR'):
        combine = 'AND'

    masks = []
    for item in filters:
        # item can be (col, q) or (col, q, mode)
        if len(item) == 3:
            col, q, mode = item
        else:
            col, q = item
            mode = 'contains'
        if not q or str(q).strip() == "":
            continue
        if col not in df.columns:
            # 存在しない列は常にFalseにする
            m = pd.Series(False, index=df.index)
            masks.append(m)
            continue
        s = df[col].astype(str)
        if mode == 'contains':
            m = s.str.contains(str(q), case=False, na=False)
        elif mode == 'startswith':
            m = s.str.lower().str.startswith(str(q).lower(), na=False)
        elif mode == 'regex':
            m = s.str.contains(str(q), case=False, na=False, regex=True)
        else:
            m = s.str.contains(str(q), case=False, na=False)
        masks.append(m)

    # combine masks
    if not masks:
        return df
    if combine == 'AND':
        final_mask = masks[0]
        for m in masks[1:]:
            final_mask &= m
    else:
        final_mask = masks[0]
        for m in masks[1:]:
            final_mask |= m

    return df[final_mask]


def append_row(path: str, row: dict, backup: bool = True) -> None:
    """CSVに行を追記する。既存ファイルがあればバックアップをとって上書き保存する方式。

    - path: CSVのパス
    - row: カラム名をキーとする辞書
    """
    p = Path(path)
    if not p.exists():
        # 新規ファイル作成
        df = pd.DataFrame([row])
        df.to_csv(p, index=False)
        return

    # 既存ファイル読み込み
    df = pd.read_csv(p)

    # 新しい行をDFに追加
    new_df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    # バックアップ
    if backup:
        ts = int(time.time())
        backup_path = p.parent / f"{p.stem}.backup_{ts}{p.suffix}"
        shutil.copy(p, backup_path)

    # 上書き保存
    new_df.to_csv(p, index=False)


if __name__ == "__main__":
    # テスト用の簡単な動作確認
    print("kakodata_utils loaded")
