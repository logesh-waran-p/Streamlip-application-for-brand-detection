import io
import re
import pandas as pd
import streamlit as st
from rapidfuzz import process, fuzz

st.set_page_config(page_title="Brand Matcher (Updated)", layout="wide")
st.title("🧠🔎 Brand Matcher — Updated Version")

st.markdown("""
Upload **two Excel files**:
1) Product descriptions file (with `Description` + optional `data_key`)  
2) Brands file (with `Brand` column)

Run the matcher → filter → **download results as Excel**.
""")

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    similarity_threshold = st.slider("Similarity threshold", 0, 100, 75, 1)
    top_n = st.number_input("Top N candidates", 1, 20, 5, 1)
    st.caption("Higher threshold = stricter matches.")

# File uploaders
c1, c2 = st.columns(2)
with c1:
    desc_file = st.file_uploader("Upload product descriptions Excel", type=["xlsx", "xls"])
with c2:
    brand_file = st.file_uploader("Upload brands Excel", type=["xlsx", "xls"])

def clean_text(text: str) -> str:
    text = str(text)
    text = text.lower()
    text = re.sub(r'\([^)]*\)', '', text)  # remove (...)
    text = re.sub(r"[’'‘`]", '', text)    # remove apostrophes
    text = re.sub(r'\b(inc|incorporated|ltd|llc|corp|co|company)\b', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)   # punctuation → space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_brand_name(brand):
    brand = re.sub(r'\([^)]*\)', '', str(brand))
    return clean_text(brand).strip()

def brand_in_description(brand, description):
    desc_clean = clean_text(description)
    brand_clean = clean_text(brand)
    return brand_clean in desc_clean  # phrase match

def split_brands(s):
    pattern = r',\s*(?![^()]*\))'
    return re.split(pattern, str(s))

def filter_matched_brands(description, matched_brands_str):
    if pd.isna(matched_brands_str) or str(matched_brands_str).strip() == '':
        return "no brand found"

    matched_brands_raw = split_brands(matched_brands_str)
    multi_word_brands = []
    single_word_flag = False

    for raw_brand in matched_brands_raw:
        brand = clean_brand_name(raw_brand)
        brand_tokens = brand.split()

        if len(brand_tokens) == 1:
            single_word_flag = True
            continue

        if brand_in_description(brand, description):
            multi_word_brands.append(raw_brand.strip())

    if multi_word_brands:
        return ', '.join(multi_word_brands)

    if single_word_flag:
        return "this is a single word brand"

    return "no brand found"

# Run button
run = st.button("▶️ Run Matching", type="primary", disabled=not (desc_file and brand_file))

if run:
    try:
        desc_df = pd.read_excel(desc_file)
        brand_df = pd.read_excel(brand_file)
    except Exception as e:
        st.error(f"Failed to read Excel files: {e}")
        st.stop()

    # Ensure correct columns
    if "Description" not in desc_df.columns:
        st.error("Descriptions file must have a column named 'Description'.")
        st.stop()
    if "Brand" not in brand_df.columns:
        st.error("Brands file must have a column named 'Brand'.")
        st.stop()
    if "data_key" not in desc_df.columns:
        st.warning("No 'data_key' column found. Will continue without it.")

    # Clean brand list
    brand_df = brand_df.dropna(subset=["Brand"])
    cleaned_brands = [clean_text(b) for b in brand_df["Brand"]]
    cleaned_to_original = dict(zip(cleaned_brands, brand_df["Brand"]))

    matched_brands_per_description = []
    prog = st.progress(0)
    total = len(desc_df)

    for i, desc in enumerate(desc_df["Description"].astype(str)):
        desc_lower = desc.lower()

        if " by " in desc_lower:
            after_by = desc_lower.split(" by ", 1)[1]
            query = clean_text(after_by)
        else:
            query = clean_text(desc)

        results = process.extract(
            query=query,
            choices=cleaned_brands,
            scorer=fuzz.token_set_ratio,
            limit=int(top_n),
        )
        filtered_matches = [cleaned_to_original[m[0]] for m in results if m[1] >= int(similarity_threshold)]

        # fallback if none matched after "by"
        if not filtered_matches and " by " in desc_lower:
            query2 = clean_text(desc)
            results2 = process.extract(
                query=query2,
                choices=cleaned_brands,
                scorer=fuzz.token_set_ratio,
                limit=int(top_n),
            )
            filtered_matches = [cleaned_to_original[m[0]] for m in results2 if m[1] >= int(similarity_threshold)]

        matched_brands_per_description.append(", ".join(filtered_matches))

        if (i + 1) % max(1, total // 100) == 0:
            prog.progress(min(1.0, (i + 1) / total))

    # Add matches
    desc_df["Matched_Brands"] = matched_brands_per_description

    # Filter matches (Stage 2)
    desc_df["Filtered_Brands"] = desc_df.apply(
        lambda row: filter_matched_brands(row["Description"], row["Matched_Brands"]),
        axis=1
    )

    # Reorder columns
    if "data_key" in desc_df.columns:
        out_df = desc_df[["data_key", "Description", "Matched_Brands", "Filtered_Brands"]]
    else:
        out_df = desc_df[["Description", "Matched_Brands", "Filtered_Brands"]]

    st.success("✅ Matching complete!")
    st.subheader("Results Preview (first 200 rows)")
    st.dataframe(out_df.head(200), use_container_width=True)

    # Download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        out_df.to_excel(writer, index=False, sheet_name="matches")
    output.seek(0)

    st.download_button(
        label="⬇️ Download Excel results",
        data=output,
        file_name="brand_match_results_filtered_with_key.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.caption("Tip: If you see missing matches, lower the threshold or increase Top N.")
