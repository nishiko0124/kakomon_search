import tempfile
import os
import pandas as pd
from db_utils import init_db, import_csv_to_db, search_db, append_row_db, get_table_columns


def test_import_and_search_and_append(tmp_path):
    # 一時CSVを作成
    csv_path = tmp_path / 'test.csv'
    df = pd.DataFrame({
        'subject': ['民法', '刑法', '民法'],
        'teacher': ['森田', '田中', '佐藤']
    })
    df.to_csv(csv_path, index=False)

    db_path = tmp_path / 'test.db'
    init_db(str(db_path))
    import_csv_to_db(str(csv_path), str(db_path), if_exists='replace')

    # 検索
    res = search_db(str(db_path), [('subject', '民法'), ('teacher', '森田')])
    assert len(res) == 1
    assert res.iloc[0]['teacher'] == '森田'

    # 追加
    append_row_db(str(db_path), {'subject': '民法', 'teacher': '新村'}, backup=True)
    res2 = search_db(str(db_path), [('teacher', '新村')])
    assert len(res2) == 1


def test_search_modes_db(tmp_path):
    csv_path = tmp_path / 'test2.csv'
    df = pd.DataFrame({
        'subject': ['民法I', '民法II', '刑法'],
        'notes': ['abc123', 'xyz', '123abc']
    })
    df.to_csv(csv_path, index=False)
    db_path = tmp_path / 'test2.db'
    init_db(str(db_path))
    import_csv_to_db(str(csv_path), str(db_path), if_exists='replace')

    r1 = search_db(str(db_path), [('subject', '民法', 'startswith')])
    assert len(r1) == 2
    r2 = search_db(str(db_path), [('notes', '^abc', 'regex')])
    assert len(r2) == 1
