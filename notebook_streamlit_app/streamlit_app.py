import json, ast, io, contextlib, os
import streamlit as st

# Optional but commonly needed
try:
    import pandas as pd  # for nicer display of DataFrames if present
except Exception:
    pd = None

try:
    import matplotlib.pyplot as plt
except Exception as e:
    st.warning("matplotlib is not available. Plots may not render.")
    plt = None

st.set_page_config(page_title="Notebook → Streamlit", layout="wide")
st.title("📓➡️ Streamlit: Run a Jupyter Notebook as an App")

st.markdown(
    "This app runs code cells from your Jupyter notebook and renders outputs in Streamlit. "
    "Upload an `.ipynb` file below or keep `nbl.ipynb` in the same folder."
)

uploaded = st.file_uploader("Upload your .ipynb (optional)", type=["ipynb"])

def read_notebook_bytes(b):
    try:
        nb = json.loads(b.decode("utf-8"))
        return nb
    except Exception as e:
        st.error(f"Could not parse notebook JSON: {e}")
        return None

def read_notebook_path(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Could not read notebook at '{path}': {e}")
        return None

if uploaded:
    nb = read_notebook_bytes(uploaded.read())
else:
    nb = read_notebook_path("nbl.ipynb")

if not nb:
    st.stop()

# Extract code cells
cells = []
for cell in nb.get("cells", []):
    if cell.get("cell_type") == "code":
        src = "".join(cell.get("source", ""))
        if src.strip():
            cells.append(src)

if not cells:
    st.warning("No code cells were found in the notebook.")
    st.stop()

st.sidebar.header("Controls")
run_all = st.sidebar.button("▶️ Run all cells")
reset_state = st.sidebar.button("🔄 Reset runtime")
selected_idx = st.sidebar.multiselect(
    "Run selected cells (by index)",
    options=list(range(1, len(cells) + 1)),
    default=[]
)

if reset_state or "exec_env" not in st.session_state:
    st.session_state.exec_env = {"__name__": "__main__", "st": st}
    # Make a display() helper available to notebook-style code
    st.session_state.exec_env["display"] = st.write
    if plt:
        # Monkeypatch plt.show() to render into Streamlit
        def _st_show(*args, **kwargs):
            st.pyplot(plt.gcf())
            plt.clf()
        plt.show = _st_show
        st.session_state.exec_env["plt"] = plt
    if pd:
        st.session_state.exec_env["pd"] = pd

def run_cell(cell_code: str):
    # Display code
    with st.expander("Show code", expanded=False):
        st.code(cell_code, language="python")

    # Prepare execution env
    env = st.session_state.exec_env

    # Capture stdout
    buf = io.StringIO()
    try:
        tree = ast.parse(cell_code, mode="exec")
        last_is_expr = len(tree.body) > 0 and isinstance(tree.body[-1], ast.Expr)
        if last_is_expr:
            # Separate last expression for eval to show its value like in notebooks
            last_expr = ast.Expression(body=tree.body[-1].value)
            tree.body = tree.body[:-1]
            code_without_last = compile(tree, "<cell>", "exec")
            last_code = compile(last_expr, "<cell-expr>", "eval")
            with contextlib.redirect_stdout(buf):
                exec(code_without_last, env)
            stdout = buf.getvalue()
            if stdout:
                st.text(stdout)
            result = eval(last_code, env)
            # Display nicely
            try:
                if pd is not None and (isinstance(result, pd.DataFrame) or isinstance(result, pd.Series)):
                    st.dataframe(result)
                else:
                    st.write(result)
            except Exception:
                st.write(result)
        else:
            code_obj = compile(tree, "<cell>", "exec")
            with contextlib.redirect_stdout(buf):
                exec(code_obj, env)
            stdout = buf.getvalue()
            if stdout:
                st.text(stdout)
    except Exception as e:
        st.exception(e)

# UI: choose to run all or selected
if run_all:
    for i, src in enumerate(cells, start=1):
        st.subheader(f"Cell {i}")
        run_cell(src)
elif selected_idx:
    for i in selected_idx:
        idx = int(i) - 1
        if 0 <= idx < len(cells):
            st.subheader(f"Cell {i}")
            run_cell(cells[idx])
else:
    st.info("Use **Run all cells** or pick specific cells from the sidebar to execute.")

st.caption("Tip: If your notebook expects local files, place them next to this app in the same folder or upload them within your code.")
