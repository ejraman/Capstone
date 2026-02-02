import streamlit as st

import streamlit as st
import pandas as pd

st.title("Skills Analysis")

csv_path = st.session_state.get("csv_path", "data/SGJobData (2).csv")
sample_size = st.session_state.get("sample_size", 20000)

df = pd.read_csv(csv_path, nrows=sample_size)

st.write("Using CSV:", csv_path)
st.write("Rows loaded:", len(df))
st.dataframe(df.head(30))

