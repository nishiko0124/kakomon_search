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
from html import escape # HTMLエスケープのためにインポート

# --- 設定 ---
# リポジトリのルートからの相対パスとして 'data' ディレクトリを参照します。
# これにより、ローカル環境でもデプロイ環境でも同様に動作します。
REPO_DATA_DIR = Path('data')

st.set_page_config(page_title="過去問検索", layout="wide")
st.title("過去問検索ツール")

# --- カスタムCSS ---
# 生成するHTMLテーブルとハイライト用のスタイルを定義
st.markdown("""
<style>
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th, td {
        border: 1px solid #e0e0e0;
        padding: 8px;
        text-align: left;
        vertical-align: top;
    }
    th {
        background-color: #f2f2f2;
    }
    mark {
        background-color: #FFF1A2;
        padding: 0.1em 0.2em;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)


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
        # ハイライト表示のロジックを、該当単語のみマークする方法に変更
        def generate_highlighted_html(df, filters):
            """検索語にマッチした部分を<mark>タグで囲んだHTMLテーブルを生成する"""
            # ヘッダーを生成
            table_html = "<table><thead><tr>"
            for column in df.columns:
                table_html += f"<th>{escape(str(column))}</th>"
            table_html += "</tr></thead><tbody>"

            # 各行を生成
            for _, row in df.iterrows():
                table_html += "<tr>"
                for column in df.columns:
                    cell_value = str(row[column])
                    # まずはセル全体を安全にエスケープする
                    highlighted_cell = escape(cell_value)

                    # この列に関連するフィルターを適用してハイライトする
                    for f_col, f_query, f_mode in filters:
                        if f_col == column:
                            pattern = re.escape(f_query) if f_mode == 'contains' else f_query
                            try:
                                # マッチした部分を<mark>タグで囲む
                                highlighted_cell = re.sub(
                                    f'({pattern})',
                                    r'<mark>\1</mark>',
                                    highlighted_cell,
                                    flags=re.IGNORECASE
                                )
                            except re.error:
                                continue # 不正な正規表現はスキップ

                    table_html += f"<td>{highlighted_cell}</td>"
                table_html += "</tr>"

            table_html += "</tbody></table>"
            return table_html

        if st.session_state.do_highlight and filters:
            # カスタムHTMLを生成して表示
            html_output = generate_highlighted_html(res, filters)
            st.markdown(html_output, unsafe_allow_html=True)
        else:
            # ハイライトしない場合は通常のデータフレーム表示
            st.dataframe(res)

    # --- データプレビューセクション ---
    st.markdown('---')
    st.write('現在のデータプレビュー（最新200件・年度降順）')

    preview_df = df.copy()
    if year_col and year_col in preview_df.columns:
        preview_df[year_col] = pd.to_numeric(preview_df[year_col], errors='coerce')
        preview_df = preview_df.sort_values(by=year_col, ascending=False)

    st.dataframe(preview_df.head(200))
