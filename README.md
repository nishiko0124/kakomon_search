# kakomon_search

Simple Streamlit app to search CSVs for course/year/teacher. This repository contains:

- `app.py` - Streamlit application
- `kakodata_utils.py` - CSV loading and search utilities
- `requirements.txt` - runtime dependencies

Quick start

1. Create a Python virtual environment and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the Streamlit app locally:

```bash
streamlit run app.py
```

3. Deploy to Streamlit Community Cloud:

- Push this repository to GitHub (already done in this repo)
- On Streamlit Cloud create a new app and point it at this repository and the `main` branch. Set the entrypoint to `app.py`.

Notes

- Do not commit your local virtual environment. `.venv/` is excluded from the repository history.
- The app supports uploading CSVs via the UI; if none are uploaded it reads CSV files from a default local directory (for local testing).

