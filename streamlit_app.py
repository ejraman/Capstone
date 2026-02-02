import streamlit as st
from utils import read_sample  # we will add this in utils.py below

st.set_page_config(page_title="SG Job Market Dashboard", layout="wide")

st.title("Singapore Job Market — Interactive Dashboard 📊")

# --- Sidebar controls ---
st.sidebar.header("Configuration & Filters")

csv_path = st.sidebar.text_input(
    "CSV path",
    "data/SGJobData (2).csv",
    key="main_csv_path"
)

sample_size = st.sidebar.slider(
    "Sample size",
    min_value=1000,
    max_value=50000,
    value=20000,
    step=1000,
    key="main_sample_size"
)

clip_pct = st.sidebar.slider(
    "Clip salary at percentile (upper)",
    min_value=80,
    max_value=99,
    value=95,
    step=1,
    key="main_clip_pct"
)

top_n = st.sidebar.slider(
    "Top N for companies/categories",
    min_value=5,
    max_value=50,
    value=15,
    step=1,
    key="main_top_n"
)

# --- Share with all pages (MUST be AFTER the variables above) ---
st.session_state["csv_path"] = csv_path
st.session_state["sample_size"] = sample_size
st.session_state["clip_pct"] = clip_pct
st.session_state["top_n"] = top_n







# --- Main content (Overview inside main page) ---
st.subheader("Overview (sample preview)")

try:
    df = read_sample(csv_path, nrows=sample_size)
    st.write("Columns:", list(df.columns))
    st.dataframe(df.head(50), use_container_width=True)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
