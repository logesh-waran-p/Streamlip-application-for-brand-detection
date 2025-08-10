# Brand Matcher — Streamlit App

This Streamlit app matches product **descriptions** to a list of **brands** using RapidFuzz.

## Features
- Upload **two Excel files** (one with descriptions, one with brands)
- Choose which columns to use
- Tune **similarity threshold** and **Top N**
- Download **Excel results**

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Then open the browser (usually http://localhost:8501).

## Upload to GitHub (no command line)
1. Create a new repo on GitHub.
2. Click **Add file → Upload files**.
3. Drag & drop `app.py`, `requirements.txt`, and `README.md`.
4. Commit changes.

## Deploy to Streamlit Community Cloud
1. Sign in with GitHub at https://share.streamlit.io (or https://streamlit.io/cloud).
2. **New app** → select your repo.
3. **Main file path:** `app.py`
4. Deploy.

