import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

st.title('Company-wise Vacancies 📊')

DB_PATH = st.text_input('SQLite DB path', value='data/visual.db')

@st.cache_data
def load_companies(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql('SELECT id, name FROM companies ORDER BY name', conn)
    conn.close()
    return df

if not st.button('Ensure DB exists (build if missing)'):
    pass

try:
    comps = load_companies(DB_PATH)
except Exception as e:
    st.error(f'Error loading DB: {e}')
    st.info('Run the build script: `python scripts/build_visual_db.py --csv data/SGJobData\\ \\(2\\).csv --db data/visual.db`')
    st.stop()

company = st.selectbox('Company', options=['All'] + comps['name'].tolist())
period_agg = st.selectbox('Period aggregation display', options=['period'], index=0)

conn = sqlite3.connect(DB_PATH)
if company == 'All':
    q = 'SELECT period, SUM(vacancies) as vacancies, SUM(postings) as postings FROM vacancies GROUP BY period ORDER BY period'
    df = pd.read_sql(q, conn)
else:
    cid = int(comps.loc[comps['name']==company, 'id'].iloc[0])
    q = 'SELECT period, vacancies, postings FROM vacancies WHERE company_id=? ORDER BY period'
    df = pd.read_sql(q, conn, params=(cid,))
conn.close()

if df.empty:
    st.info('No vacancy data available for selection.')
else:
    st.subheader('Vacancies over time')
    df['period_dt'] = pd.to_datetime(df['period'], errors='coerce')
    chart = alt.Chart(df).mark_line(point=True).encode(
        x='period_dt:T',
        y='vacancies:Q'
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader('Top companies by cumulative vacancies')
    conn = sqlite3.connect(DB_PATH)
    topq = 'SELECT c.name, SUM(v.vacancies) as total_vac FROM vacancies v JOIN companies c ON v.company_id=c.id GROUP BY c.name ORDER BY total_vac DESC LIMIT 20'
    topdf = pd.read_sql(topq, conn)
    conn.close()
    st.table(topdf)

    st.markdown('Download aggregated CSV:')
    st.download_button('Download CSV', df.to_csv(index=False), file_name='company_vacancies.csv')
