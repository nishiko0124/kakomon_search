import pandas as pd
from kakodata_utils import search_df


def test_search_single_column():
    df = pd.DataFrame({
        'subject': ['民法', '刑法', '民事訴訟法'],
        'teacher': ['森田太郎', '田中花子', '森田次郎']
    })
    res = search_df(df, [('subject', '民法', 'contains')])
    assert len(res) == 1
    assert res.iloc[0]['teacher'] == '森田太郎'


def test_search_two_columns_and():
    df = pd.DataFrame({
        'subject': ['民法', '民法', '刑法'],
        'teacher': ['森田', '佐藤', '森田']
    })
    res = search_df(df, [('subject', '民法', 'contains'), ('teacher', '森田', 'contains')])
    assert len(res) == 1
    assert res.iloc[0]['teacher'] == '森田'


def test_search_startswith_and_regex():
    df = pd.DataFrame({
        'subject': ['民法I', '民法II', '刑法'],
        'notes': ['abc123', 'xyz', '123abc']
    })
    res1 = search_df(df, [('subject', '民法', 'startswith')])
    assert len(res1) == 2
    res2 = search_df(df, [('notes', '^abc', 'regex')])
    assert len(res2) == 1
