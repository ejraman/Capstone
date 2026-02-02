import streamlit as st

import streamlit as st
import pandas as pd

st.title("Salary Insights")

csv_path = st.session_state.get("csv_path", "data/SGJobData (2).csv")
sample_size = st.session_state.get("sample_size", 20000)
clip_pct = st.session_state.get("clip_pct", 99)
top_n = st.session_state.get("top_n", 15)

df = pd.read_csv(csv_path, nrows=sample_size)

st.write("Using CSV:", csv_path)
st.write("Rows loaded:", len(df))
st.dataframe(df.head(30))

