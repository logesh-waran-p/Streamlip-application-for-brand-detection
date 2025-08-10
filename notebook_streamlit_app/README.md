# Notebook → Streamlit App

This project converts and **runs your Jupyter Notebook as a Streamlit app**.

## Files

- `streamlit_app.py` — the Streamlit app that executes your notebook's code cells.
- `nbl.ipynb` — your original notebook (already included here).
- `requirements.txt` — Python dependencies.
- `.gitignore` — ignore common Python/Streamlit clutter.

---

## Run Locally

1. **Create a virtual environment (recommended)**

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the app**

   ```bash
   streamlit run streamlit_app.py
   ```

4. Your browser will open automatically. If not, visit the URL shown in the terminal (usually http://localhost:8501).

---

## Upload to GitHub (Web UI — no command line)

1. Go to https://github.com and **sign in**.
2. Click the **+** (top-right) → **New repository**.
3. Name it (e.g., `notebook-streamlit-app`) and click **Create repository**.
4. On the repo page, click **Add file → Upload files**.
5. On your computer, **unzip** the folder you downloaded from ChatGPT.
6. **Drag and drop all files** (`streamlit_app.py`, `nbl.ipynb`, `requirements.txt`, `.gitignore`) into GitHub’s upload area.
7. Scroll down and click **Commit changes**.

That’s it — your code is now on GitHub!

---

## (Optional) Deploy to Streamlit Community Cloud

1. Visit https://share.streamlit.io (or https://streamlit.io/cloud) and **sign in with GitHub**.
2. Click **New app**.
3. Choose your repository and branch.
4. Set **Main file path** to `streamlit_app.py`.
5. Click **Deploy**.

Your app will build and then go live. Share the URL with others!

---

## Common Tips

- If your notebook relies on local data files, add them to the repository too.
- If you see `ModuleNotFoundError`, add the missing package name to `requirements.txt`, commit, and redeploy.
- For large/long-running computations, consider caching with `@st.cache_data` or `@st.cache_resource` inside `streamlit_app.py`.
