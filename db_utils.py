"""
SQLiteベースのユーティリティ: CSVのインポート、検索（部分一致AND）、行追加
"""
import sqlite3
from pathlib import Path
import pandas as pd
import shutil
import time


def init_db(db_path: str, table_name: str = 'kakodata') -> None:
    p = Path(db_path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.close()


def import_csv_to_db(csv_path: str, db_path: str, table_name: str = 'kakodata', if_exists: str = 'replace') -> None:
    """CSVを読み込んでSQLiteのテーブルに保存する。"""
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(csv_path)
    df = pd.read_csv(p)
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    finally:
        conn.close()


def get_table_columns(db_path: str, table_name: str = 'kakodata') -> list:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info('{table_name}')")
        rows = cur.fetchall()
        return [r[1] for r in rows]
    finally:
        conn.close()


def search_db(db_path: str, filters: list, table_name: str = 'kakodata', combine: str = 'AND') -> pd.DataFrame:
    """filters: list of (column_name, query_string, mode)
    mode: 'contains' | 'startswith' | 'regex'
    SQLiteで可能な検索はSQLで実行し、regexモードが含まれる場合は一旦絞ってからpandasで正規表現フィルタをかける。
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        sql_parts = []
        params = []
        post_regex_filters = []

        for item in filters:
            if len(item) == 3:
                col, q, mode = item
            else:
                col, q = item
                mode = 'contains'
            if not q or str(q).strip() == "":
                continue
            if mode == 'regex':
                post_regex_filters.append((col, q))
            elif mode == 'startswith':
                sql_parts.append((f"lower({col}) LIKE ?", f"{q.lower()}%"))
            else:
                sql_parts.append((f"lower({col}) LIKE ?", f"%{q.lower()}%"))

        # Build SQL
        if not sql_parts:
            base_where = "1"
            base_params = []
        else:
            clauses = [p[0] for p in sql_parts]
            vals = [p[1] for p in sql_parts]
            joiner = f" {combine} " if combine in ('AND','OR') else ' AND '
            base_where = joiner.join(clauses)
            base_params = vals

        sql = f"SELECT * FROM {table_name} WHERE {base_where}"
        df = pd.read_sql_query(sql, conn, params=base_params)

        # If there are regex filters, apply them with pandas. For combine='OR', we need to union results:
        if post_regex_filters:
            if combine == 'AND':
                for col, q in post_regex_filters:
                    if col not in df.columns:
                        return df.iloc[0:0]
                    df = df[df[col].astype(str).str.contains(q, case=False, regex=True)]
            else:
                # OR: need to run separate queries for regex filters and union with existing df
                frames = [df]
                for col, q in post_regex_filters:
                    # select all rows then filter
                    all_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                    if col in all_df.columns:
                        m = all_df[all_df[col].astype(str).str.contains(q, case=False, regex=True)]
                        frames.append(m)
                if frames:
                    df = pd.concat(frames, ignore_index=True).drop_duplicates().reset_index(drop=True)

        return df
    finally:
        conn.close()


def append_row_db(db_path: str, row: dict, table_name: str = 'kakodata', backup: bool = True) -> None:
    """テーブルに行を追加する。バックアップとしてテーブルをCSVにダンプするオプションあり。"""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        new_df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        if backup:
            ts = int(time.time())
            backup_csv = Path(db_path).with_name(f"{Path(db_path).stem}.backup_{ts}.csv")
            new_df.to_csv(backup_csv, index=False)
        # replace table
        new_df.to_sql(table_name, conn, if_exists='replace', index=False)
    finally:
        conn.close()

if __name__ == '__main__':
    print('db_utils loaded')
