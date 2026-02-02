import streamlit as st
import pandas as pd
import altair as alt
from utils import industry_heatmap_matrix

st.title('Industry Vacancy Heatmap 🔥')

DB_PATH = st.text_input('SQLite DB path', value='data/visual.db')
TOP_N = st.slider('Top industries', 5, 50, 20)

with st.spinner('Loading industry data...'):
    pivot = industry_heatmap_matrix(DB_PATH, top_n=TOP_N)

if pivot.empty:
    st.info('No industry data available. Run `scripts/build_visual_db.py` to generate `data/visual.db`.')
else:
    st.subheader('Heatmap (industries × time)')
    # Transform pivot to long form for Altair
    df = pivot.reset_index().melt(id_vars='industry', var_name='period', value_name='vacancies')
    # convert period string to datetime (period start)
    df['period_dt'] = pd.to_datetime(df['period'].apply(lambda x: x.split('-')[0]))

    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X('period_dt:T', title='Period', axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('industry:N', sort='-x'),
        color=alt.Color('vacancies:Q', scale=alt.Scale(scheme='reds')),
        tooltip=['industry', 'period', 'vacancies']
    ).properties(height=500)
    st.altair_chart(chart, use_container_width=True)

    st.markdown('Download heatmap data (CSV)')
    st.download_button('Download CSV', pivot.reset_index().to_csv(index=False), file_name='industry_heatmap.csv')