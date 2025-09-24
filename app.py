"""
Streamlit アプリ: CSVの部分一致2列検索と行追加フォーム

期待するCSV: 任意のカラムを持つが、アプリはカラムを自動検出してフォームを生成する。
デフォルトのCSVパスはユーザ指定のパスに設定できる。
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from kakodata_utils import load_csv, load_csvs_from_dir, search_df

DEFAULT_DIR = "/Users/nishikawakotone/Documents/kotone_app/kakomondata"
REPO_DATA_DIR = Path('data')

st.set_page_config(page_title="過去問検索", layout="wide")
st.title("過去問検索ツール")

# prefer repository `data/` if present (so deployed app or repo includes bundled CSVs)
csv_path = DEFAULT_DIR
if REPO_DATA_DIR.exists() and REPO_DATA_DIR.is_dir():
    # use relative repo data dir when present
    csv_path = str(REPO_DATA_DIR)

# Note: this app now always uses repository `data/` when present.
st.info('このアプリはリポジトリ内の `data/` を常に使用します。アップロードしたCSVは無視されます。')

# Allow user to upload one or more CSV files in the deployed app (uploads are ignored if data/ exists)
uploaded_files = st.file_uploader('CSVファイルをアップロード（data/ が無ければ代替として使用できます）', type=['csv'], accept_multiple_files=True)

# Option kept for legacy behavior if you want explicit local fallback, but default is to use data/
force_local = st.checkbox('リポジトリ内の data/ がない場合、ユーザ指定のローカル DEFAULT_DIR を使う', value=False)

force_local = st.checkbox('リポジトリ内の data/ がない場合、ユーザ指定のローカル DEFAULT_DIR を使う', value=False)

# Prepare uploaded dfs (uploads are fallback only when data/ is missing)
df = pd.DataFrame()
uploaded_dfs = []
if uploaded_files:
    for uf in uploaded_files:
        try:
            uploaded_dfs.append(pd.read_csv(uf))
        except Exception:
            continue

# Decide source: prefer repo data/ if present
repo_data_exists = REPO_DATA_DIR.exists() and REPO_DATA_DIR.is_dir()
if repo_data_exists:
    try:
        df = load_csvs_from_dir(str(REPO_DATA_DIR))
    except Exception as e:
        st.error(f"リポジトリ内 data/ の読み込みに失敗しました: {e}")
        df = pd.DataFrame()
else:
    # No repo data/: use uploads if provided, otherwise (optionally) use DEFAULT_DIR
    if uploaded_dfs:
        df = pd.concat(uploaded_dfs, ignore_index=True)
    elif force_local:
        try:
            df = load_csvs_from_dir(DEFAULT_DIR)
        except Exception as e:
            st.error(f"ローカルCSVの読み込みに失敗しました: {e}")
            df = pd.DataFrame()
    else:
        st.info("リポジトリ内に data/ が存在しません。`data/` を作成して CSV を置くか、アップロードしてください。")
        df = pd.DataFrame()

# DB機能はオプション化しました。CSVを直接操作します。

#st.header("検索（年度・授業名・教員）")

cols = list(df.columns) if not df.empty else []

# Improve layout: three columns for inputs
st.write('検索したいフィールドに値を入力し、「検索」ボタンを押してください。')
year_q = st.text_input('年度')
subject_q = st.text_input('授業名')
teacher_q = st.text_input('教員')
do_search = st.button('検索')

st.radio('検索モード', options=['含む', '完全一致'], index=0, key='match_mode')
st.radio('条件の結合', options=['AND', 'OR'], index=0, key='combine_mode')
do_highlight = st.checkbox('ハイライト表示', value=True)

# カラム自動検出（ユーザが手動で上書き可能）


# （旧）重複していた検索設定はUI上部に統合済み

def find_col(name_candidates):
    # flexible matching: exact first, then substring match
    for cand in name_candidates:
        for c in cols:
            if c.lower() == cand.lower():
                return c
    for cand in name_candidates:
        for c in cols:
            if cand.lower() in c.lower() or c.lower() in cand.lower():
                return c
    return None


# サイドバーは使用しません（UIをシンプルに保つため）


def build_filters_from_three():
    filters = []

    # カラムマッピングUIを廃止したため、自動検出のみを使う
    year_col = find_col(['年度', '年', 'year'])
    subject_col = find_col(['科目', '授業名', 'subject'])
    teacher_col = find_col(['教員', 'teacher', '教員名'])

    mode = 'contains' if st.session_state.get('match_mode', '含む') == '含む' else 'exact'

    if year_col and year_q and year_q.strip():
        if mode == 'contains':
            filters.append((year_col, year_q, 'contains'))
        else:
            filters.append((year_col, f"^{year_q}$", 'regex'))
    if subject_col and subject_q and subject_q.strip():
        if mode == 'contains':
            filters.append((subject_col, subject_q, 'contains'))
        else:
            filters.append((subject_col, f"^{subject_q}$", 'regex'))
    if teacher_col and teacher_q and teacher_q.strip():
        if mode == 'contains':
            filters.append((teacher_col, teacher_q, 'contains'))
        else:
            filters.append((teacher_col, f"^{teacher_q}$", 'regex'))
    return filters

filters = []
res = pd.DataFrame()
if do_search:
    filters = build_filters_from_three()
    if filters:
        # CSVベースで検索
        combine = st.session_state.get('combine_mode', 'AND')
        res = search_df(df, filters, combine=combine)

    # 年度で降順ソート（存在する場合、数値としてソートを試みる）
    year_col = find_col(['年度', '年', 'year'])
    if year_col and year_col in res.columns:
        try:
            res[year_col] = pd.to_numeric(res[year_col], errors='coerce')
            res = res.sort_values(by=year_col, ascending=False)
        except Exception:
            # fallback: lexicographical sort desc
            res = res.sort_values(by=year_col, ascending=False)

st.write(f"該当件数: {len(res)} 件")
if not res.empty:
    csv_bytes = res.to_csv(index=False).encode('utf-8')
    st.download_button("結果をCSVでダウンロード", data=csv_bytes, file_name='search_results.csv', mime='text/csv')

    # ハイライト表示: キーワードにマッチする部分を黄色でハイライト
    def highlight_html(df, filters):
        try:
            import re
            html = '<table border="1" cellpadding="4" cellspacing="0">'
            html += '<tr>' + ''.join([f'<th>{c}</th>' for c in df.columns]) + '</tr>'
            for _, row in df.iterrows():
                html += '<tr>'
                for c in df.columns:
                    cell = str(row[c])
                    cell_html = cell
                    for (fc, fq, fm) in filters:
                        if fc == c and fq and str(fq).strip():
                            try:
                                if fm == 'contains':
                                    pattern = re.escape(str(fq))
                                    cell_html = re.sub(pattern, lambda m: f"<strong style='background:rgba(255,230,128,0.45)'>{m.group(0)}</strong>", cell, flags=re.IGNORECASE)
                                elif fm == 'regex':
                                    cell_html = re.sub(fq, lambda m: f"<strong style='background:rgba(255,230,128,0.45)'>{m.group(0)}</strong>", cell, flags=re.IGNORECASE)
                                elif fm == 'startswith':
                                    if cell.lower().startswith(str(fq).lower()):
                                        match = cell[:len(fq)]
                                        after = cell[len(fq):]
                                        cell_html = f"<strong style='background:rgba(255,230,128,0.45)'>{match}</strong>{after}"
                            except Exception:
                                pass
                    html += f'<td>{cell_html}</td>'
                html += '</tr>'
            html += '</table>'
            return html
        except Exception:
            return None

    display_filters = [(f[0], f[1], f[2]) for f in filters]
    html = highlight_html(res, display_filters)
    if html:
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.dataframe(res)

# no max rows input; simplify preview header
st.markdown('---')
st.write('現在のデータプレビュー（年度降順）')
# CSVから直接プレビュー（年度があれば降順）
preview_df = df.copy()
year_col = find_col(['年度', '年', 'year'])
if year_col and year_col in preview_df.columns:
    try:
        preview_df[year_col] = pd.to_numeric(preview_df[year_col], errors='coerce')
        preview_df = preview_df.sort_values(by=year_col, ascending=False)
    except Exception:
        preview_df = preview_df.sort_values(by=year_col, ascending=False)

def _format_year_column_for_display(df, year_col_name):
    df = df.copy()
    try:
        if year_col_name in df.columns:
            nums = pd.to_numeric(df[year_col_name], errors='coerce')
            df[year_col_name] = nums.where(nums.notna()).apply(lambda v: str(int(v)) if pd.notna(v) else '')
    except Exception:
        pass
    return df

disp_preview = _format_year_column_for_display(preview_df, year_col) if not preview_df.empty else preview_df

st.dataframe(disp_preview.head(200) if not disp_preview.empty else pd.DataFrame())
