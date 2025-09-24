"""
Streamlit App: Partial match search on two columns of a CSV and a form to add rows.

Expected CSV: Has arbitrary columns, but the app automatically detects them to generate a form.
The default CSV path can be set to a user-specified path.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from kakodata_utils import load_csv, load_csvs_from_dir, search_df
import re # ハイライト表示のために正規表現ライブラリをインポート

# --- 設定 ---
# リポジトリのルートからの相対パスとして 'data' ディレクトリを参照します。
# これにより、ローカル環境でもデプロイ環境でも同様に動作します。
REPO_DATA_DIR = Path('data')

st.set_page_config(page_title="過去問検索", layout="wide")
st.title("過去問検索ツール")


# --- データ読み込みロジック ---
df = pd.DataFrame()

# 1. 'data/' ディレクトリからCSVの読み込みを試みます。
if REPO_DATA_DIR.exists() and REPO_DATA_DIR.is_dir():
    try:
        df = load_csvs_from_dir(REPO_DATA_DIR)
        if df.empty:
            st.warning(f"'{REPO_DATA_DIR}'ディレクトリは見つかりましたが、読み込み可能なCSVファイルがありません。")
    except Exception as e:
        st.error(f"'{REPO_DATA_DIR}'ディレクトリからのデータ読み込み中にエラーが発生しました: {e}")
# 2. 'data/' ディレクトリが存在しない場合は、ファイルアップローダーにフォールバックします。
else:
    st.info(
        "リポジトリに'data'ディレクトリが見つかりませんでした。"
        "検索を開始するには、CSVファイルをアップロードしてください。"
    )
    uploaded_files = st.file_uploader(
        'こちらからCSVファイルをアップロードしてください',
        type=['csv'],
        accept_multiple_files=True
    )
    if uploaded_files:
        try:
            uploaded_dfs = [pd.read_csv(uf) for uf in uploaded_files]
            if uploaded_dfs:
                df = pd.concat(uploaded_dfs, ignore_index=True)
        except Exception as e:
            st.error(f"アップロードされたファイルの読み込み中にエラーが発生しました: {e}")


# --- メインアプリケーションUI ---
if df.empty:
    st.warning("データが読み込まれていません。'data'ディレクトリを作成してCSVを配置するか、上記のフォームからファイルをアップロードしてください。")
else:
    cols = list(df.columns)

    # --- 検索フォーム ---
    st.write('検索したい項目の値を入力し、「検索」ボタンを押してください。')

    # 検索窓を縦に並べる
    year_q = st.text_input('年度')
    subject_q = st.text_input('授業名')
    teacher_q = st.text_input('教員')

    do_search = st.button('検索')

    # 検索オプション（横並びで表示）
    c1, c2, c3 = st.columns(3)
    with c1:
        st.radio('検索モード', options=['含む', '完全一致'], index=0, key='match_mode')
    with c2:
        st.radio('条件の結合', options=['AND', 'OR'], index=0, key='combine_mode')
    with c3:
        st.checkbox('検索結果をハイライト表示', value=True, key='do_highlight')


    # --- カラム名の自動検出 ---
    def find_col(name_candidates, columns):
        """候補リストから最も一致するカラム名を見つけます。"""
        for cand in name_candidates:
            # 完全一致（大文字小文字を区別しない）
            for c in columns:
                if c.lower() == cand.lower():
                    return c
        for cand in name_candidates:
            # 部分一致（大文字小文字を区別しない）
            for c in columns:
                if cand.lower() in c.lower():
                    return c
        return None

    year_col = find_col(['年度', '年', 'year'], cols)
    subject_col = find_col(['科目', '授業名', 'subject', 'class'], cols)
    teacher_col = find_col(['教員', 'teacher', '教員名', 'instructor'], cols)

    # --- 検索の実行 ---
    res = pd.DataFrame()
    filters = [] # ハイライト表示でも使うため、ifの外で定義
    if do_search:
        mode = 'contains' if st.session_state.get('match_mode') == '含む' else 'exact'

        if year_col and year_q.strip():
            query = f"^{year_q}$" if mode == 'exact' else year_q
            op = 'regex' if mode == 'exact' else 'contains'
            filters.append((year_col, query, op))
        if subject_col and subject_q.strip():
            query = f"^{subject_q}$" if mode == 'exact' else subject_q
            op = 'regex' if mode == 'exact' else 'contains'
            filters.append((subject_col, query, op))
        if teacher_col and teacher_q.strip():
            query = f"^{teacher_q}$" if mode == 'exact' else teacher_q
            op = 'regex' if mode == 'exact' else 'contains'
            filters.append((teacher_col, query, op))

        if filters:
            combine_mode = st.session_state.get('combine_mode', 'AND')
            res = search_df(df, filters, combine=combine_mode)

            # 可能であれば年度で降順ソート
            if year_col and year_col in res.columns:
                res[year_col] = pd.to_numeric(res[year_col], errors='coerce')
                res = res.sort_values(by=year_col, ascending=False).reset_index(drop=True)


    # --- 結果の表示 ---
    st.write(f"該当件数: {len(res)} 件")
    if not res.empty:
        # ダウンロードボタン
        csv_bytes = res.to_csv(index=False).encode('utf-8-sig') # Excelでの文字化けを防ぐために 'utf-8-sig' を使用
        st.download_button(
            "結果をCSVでダウンロード",
            data=csv_bytes,
            file_name='search_results.csv',
            mime='text/csv'
        )

        # --- ★★★ここを修正しました★★★ ---
        # ハイライト表示のロジックを安全な方法に変更
        def highlight_matches(val, search_filters):
            val_str = str(val)
            for col, query, mode in search_filters:
                # 'contains'モードではクエリをエスケープ
                pattern = re.escape(query) if mode == 'contains' else query
                try:
                    if re.search(pattern, val_str, flags=re.IGNORECASE):
                        return 'background-color: #FFF1A2' # ハイライト色
                except re.error:
                    continue # 無効な正規表現は無視
            return ''

        if st.session_state.do_highlight and filters:
            # DataFrameのStyler機能を使って安全にハイライトする
            st.dataframe(res.style.applymap(lambda val: highlight_matches(val, filters)))
        else:
            st.dataframe(res)

    # --- データプレビューセクション ---
    st.markdown('---')
    st.write('現在のデータプレビュー（最新200件・年度降順）')

    preview_df = df.copy()
    if year_col and year_col in preview_df.columns:
        preview_df[year_col] = pd.to_numeric(preview_df[year_col], errors='coerce')
        preview_df = preview_df.sort_values(by=year_col, ascending=False)

    st.dataframe(preview_df.head(200))
