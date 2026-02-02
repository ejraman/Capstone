import streamlit as st
import pandas as pd
import altair as alt
from utils import compute_company_growth, load_company_vacancies

st.title('Company Vacancy Growth — Top Movers 📈')

DB_PATH = st.text_input('SQLite DB path', value='data/visual.db')
TOP_N = st.slider('Top movers N', 5, 50, 20)

with st.spinner('Computing growth rates...'):
    growth = compute_company_growth(DB_PATH, top_n=TOP_N)

if growth.empty:
    st.info('No company vacancy data available. Run `scripts/build_visual_db.py` to generate `data/visual.db`.')
else:
    st.subheader('Top movers (percent change from last period to previous)')
    # Present table with formatted pct
    display = growth.copy()
    def fmt(x):
        if x==float('inf'):
            return '∞ (new)'
        return f"{x:.1f}%"
    display['pct_change'] = display['pct_change'].apply(fmt)
    st.table(display[['company','last_vacancies','prev_vacancies','pct_change']])

    st.subheader('Sparklines for selected companies')
    companies = st.multiselect('Select companies', options=display['company'].tolist(), default=display['company'].tolist()[:5])
    if companies:
        df = load_company_vacancies(DB_PATH)
        df = df[df['company'].isin(companies)].copy()
        df['period_dt'] = pd.to_datetime(df['period'], errors='coerce')
        chart = alt.Chart(df).mark_line(point=True).encode(x='period_dt:T', y='vacancies:Q', color='company:N')
        st.altair_chart(chart, use_container_width=True)

    st.markdown('Download CSV of top movers')
    st.download_button('Download CSV', growth.to_csv(index=False), file_name='company_growth_top_movers.csv')