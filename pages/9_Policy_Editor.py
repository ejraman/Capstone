import streamlit as st
import pandas as pd
from utils import load_policy_notes, save_policy_notes

st.title('Policy Editor & Flags 📝')

POLICY_PATH = st.text_input('Policy CSV path', value='data/policy_notes.csv')

df = load_policy_notes(POLICY_PATH)
st.markdown('Use this editor to add notes/flags for companies or industries. Save the CSV to persist changes.')

edited = st.data_editor(df, num_rows="dynamic")

if st.button('Save policy notes'):
    save_policy_notes(edited, POLICY_PATH)
    st.success(f'Saved policy notes to {POLICY_PATH}')

st.markdown('Download current policy notes:')
st.download_button('Download CSV', edited.to_csv(index=False), file_name='policy_notes.csv')