\
import io
import re
import pandas as pd
import streamlit as st
from rapidfuzz import process, fuzz

st.set_page_config(page_title="Brand Matcher", layout="wide")
st.title("🧠🔎 Brand Matcher — Descriptions ↔ Brands")

st.markdown("""
Upload **two Excel files**:
1) one with product **descriptions** (plus an optional ID column) and  
2) one with **brands**.

Adjust options, run the matcher, and **download the results as Excel**.
""")

# --- Controls
with st.sidebar:
    st.header("Settings")
    similarity_threshold = st.slider("Similarity threshold", min_value=0, max_value=100, value=75, step=1)
    top_n = st.number_input("Top N candidates", min_value=1, max_value=20, value=5, step=1)
    st.caption("Higher threshold = stricter matches.")

# --- Uploaders
c1, c2 = st.columns(2)
with c1:
    desc_file = st.file_uploader("Upload product descriptions Excel", type=["xlsx", "xls"], key="desc")
with c2:
    brand_file = st.file_uploader("Upload brands Excel", type=["xlsx", "xls"], key="brand")

def clean_text(text: str) -> str:
    text = str(text)
    text = text.lower()
    text = re.sub(r'\([^)]*\)', '', text)          # remove (...) segments
    text = re.sub(r"[’'‘`]", '', text)             # remove apostrophes
    text = re.sub(r'\b(inc|incorporated|ltd|llc|corp|co|company)\b', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)           # punctuation -> space
    text = re.sub(r'\s+', ' ', text)               # collapse spaces
    return text.strip()

@st.cache_data(show_spinner=False)
def read_excel(buf):
    return pd.read_excel(buf)

desc_df = None
brand_df = None

if desc_file is not None:
    try:
        desc_df = read_excel(desc_file)
        st.success(f"Descriptions file loaded — {desc_df.shape[0]} rows, {desc_df.shape[1]} columns")
        with st.expander("Preview: Descriptions", expanded=False):
            st.dataframe(desc_df.head(20), use_container_width=True)
    except Exception as e:
        st.error(f"Failed to read descriptions Excel: {e}")

if brand_file is not None:
    try:
        brand_df = read_excel(brand_file)
        st.success(f"Brands file loaded — {brand_df.shape[0]} rows, {brand_df.shape[1]} columns")
        with st.expander("Preview: Brands", expanded=False):
            st.dataframe(brand_df.head(20), use_container_width=True)
    except Exception as e:
        st.error(f"Failed to read brands Excel: {e}")

# --- Column mapping
desc_text_col = None
desc_id_col = None
brand_text_col = None

if desc_df is not None:
    st.subheader("Map Description Columns")
    cols = list(desc_df.columns)
    # Try to guess sensible defaults
    guess_desc = None
    for c in cols:
        if str(c).strip().lower() in ("description", "descriptions", "product_description", "text"):
            guess_desc = c
            break
    desc_text_col = st.selectbox("Descriptions: text column", options=cols, index=(cols.index(guess_desc) if guess_desc in cols else 0), key="desc_text_col")
    desc_id_col = st.selectbox("Descriptions: optional ID/key column", options=["(none)"] + cols, index=0, key="desc_id_col")

if brand_df is not None:
    st.subheader("Map Brand Columns")
    bcols = list(brand_df.columns)
    guess_brand = None
    for c in bcols:
        if str(c).strip().lower() in ("brand", "brands", "name", "manufacturer"):
            guess_brand = c
            break
    brand_text_col = st.selectbox("Brands: brand/name column", options=bcols, index=(bcols.index(guess_brand) if guess_brand in bcols else 0), key="brand_text_col")

# --- Run
run = st.button("▶️ Run Matching", type="primary", disabled=not (desc_df is not None and brand_df is not None))

if run:
    if desc_text_col is None or brand_text_col is None:
        st.error("Please choose the description text column and brand column.")
        st.stop()

    # Prepare brands (drop NaNs)
    work_brands = brand_df.dropna(subset=[brand_text_col]).copy()
    cleaned_brands = [clean_text(b) for b in work_brands[brand_text_col].astype(str)]
    cleaned_to_original = dict(zip(cleaned_brands, work_brands[brand_text_col].astype(str)))

    matched_brands_per_description = []
    scores_per_description = []

    st.write("Starting matching process…")
    prog = st.progress(0)
    total = len(desc_df)

    for i, desc in enumerate(desc_df[desc_text_col].astype(str)):
        desc_lower = desc.lower()

        # try " by " heuristic first
        candidates_source = None
        if " by " in desc_lower:
            after_by = desc_lower.split(" by ", 1)[1]
            query = clean_text(after_by)
            candidates_source = "after ' by '"
        else:
            query = clean_text(desc)
            candidates_source = "full description"

        results = process.extract(
            query=query,
            choices=cleaned_brands,
            scorer=fuzz.token_set_ratio,
            limit=int(top_n),
        )

        # filter by threshold
        filtered = [(cleaned_to_original[m[0]], m[1]) for m in results if m[1] >= int(similarity_threshold)]

        # fallback: if none after-by, use full desc
        if len(filtered) == 0 and " by " in desc_lower:
            query2 = clean_text(desc)
            results2 = process.extract(
                query=query2,
                choices=cleaned_brands,
                scorer=fuzz.token_set_ratio,
                limit=int(top_n),
            )
            filtered = [(cleaned_to_original[m[0]], m[1]) for m in results2 if m[1] >= int(similarity_threshold)]

        matched_brands_per_description.append(", ".join([f"{name} ({score})" for name, score in filtered]))
        scores_per_description.append([score for _, score in filtered])

        if (i + 1) % max(1, total // 100) == 0:
            prog.progress(min(1.0, (i + 1) / total))

    # Build output
    out_df = pd.DataFrame({
        "Description": desc_df[desc_text_col].astype(str),
        "Matched_Brands": matched_brands_per_description,
    })

    # put ID first if provided
    if desc_id_col and desc_id_col != "(none)":
        out_df.insert(0, "data_key", desc_df[desc_id_col])
    else:
        # still add placeholder to match your old format if needed
        pass

    st.success("Matching complete!")
    st.subheader("Results (first 200 rows)")
    st.dataframe(out_df.head(200), use_container_width=True)

    # Download as Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        out_df.to_excel(writer, index=False, sheet_name="matches")
        # Optional: include inputs for traceability
        desc_df.head(1000).to_excel(writer, index=False, sheet_name="descriptions_sample")
        brand_df.head(1000).to_excel(writer, index=False, sheet_name="brands_sample")
    output.seek(0)

    st.download_button(
        label="⬇️ Download Excel results",
        data=output,
        file_name="brand_match_results_topN.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.caption("Tip: If you see missing matches, lower the threshold or increase Top N.")