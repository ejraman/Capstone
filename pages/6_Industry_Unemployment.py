import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

st.title('Industry Unemployment & Vacancy Contrast 🏭')

# Try to use a pre-built unemployment file if present
UPLOAD_KEY = 'data/unemployment_industry.csv'

st.markdown('You can upload an `unemployment_industry.csv` file with columns: `industry`, `period` (YYYY-MM-DD), `unemployment_rate` (percentage). If absent, upload using the control below.')
uploaded = st.file_uploader('Upload unemployment CSV', type=['csv'])

if uploaded is not None:
    df_unemp = pd.read_csv(uploaded)
    st.success('Unemployment data loaded from upload.')
else:
    try:
        df_unemp = pd.read_csv(UPLOAD_KEY)
        st.info(f'Loaded unemployment data from `{UPLOAD_KEY}`')
    except Exception:
        df_unemp = pd.DataFrame()

# Load industry vacancies from sqlite
DB_PATH = st.text_input('SQLite DB path', value='data/visual.db')
try:
    conn = sqlite3.connect(DB_PATH)
    ind_df = pd.read_sql('SELECT industry, period, SUM(vacancies) as vacancies, SUM(postings) as postings FROM industry_vacancies GROUP BY industry, period', conn)
    conn.close()
except Exception:
    ind_df = pd.DataFrame()

if ind_df.empty and df_unemp.empty:
    st.info('No industry vacancy or unemployment data available. Run `scripts/build_visual_db.py` to generate `data/visual.db`, or upload unemployment CSV to proceed.')
    st.stop()

if not df_unemp.empty:
    st.subheader('Unemployment trends (uploaded)')
    df_unemp['period_dt'] = pd.to_datetime(df_unemp['period'], errors='coerce')
    chart = alt.Chart(df_unemp).mark_line().encode(x='period_dt:T', y='unemployment_rate:Q', color='industry:N')
    st.altair_chart(chart, use_container_width=True)

if not ind_df.empty:
    st.subheader('Industry vacancies over time (from job postings)')
    ind_df['period_dt'] = pd.to_datetime(ind_df['period'], errors='coerce')
    chart = alt.Chart(ind_df).mark_line().encode(x='period_dt:T', y='vacancies:Q', color='industry:N')
    st.altair_chart(chart, use_container_width=True)

    st.markdown('You can compare unemployment vs vacancies by industry by uploading an unemployment CSV and using the download below for sample joining steps.')
    sample_join_instructions = '''
    Sample join approach (pandas):
    df_unemp['period'] = pd.to_datetime(df_unemp['period']).dt.to_period('W').astype(str)
    ind_df['period'] = pd.to_datetime(ind_df['period']).dt.to_period('W').astype(str)
    merged = df_unemp.merge(ind_df, on=['industry','period'], how='left')
    '''
    st.code(sample_join_instructions)

st.markdown('Download industry vacancy aggregates:')
if not ind_df.empty:
    st.download_button('Download CSV', ind_df.to_csv(index=False), file_name='industry_vacancies.csv')
