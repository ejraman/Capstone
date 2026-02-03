import streamlit as st
import pandas as pd
import numpy as np
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

    # UI controls: select palette and percentile cap, and period range
    palette = st.selectbox('Color palette', options=['reds', 'blues', 'viridis', 'magma', 'greens'], index=0)
    cap_pct = st.slider('Cap color scale (upper percentile)', 90, 100, 99)

    periods = list(pivot.columns)
    if len(periods) > 1:
        default_start = max(0, len(periods) - 24)
        start_idx, end_idx = st.slider('Period range (select index range)', 0, len(periods) - 1, (default_start, len(periods) - 1))
        selected_periods = periods[start_idx:end_idx + 1]
        df = pivot.reset_index().melt(id_vars='industry', var_name='period', value_name='vacancies')
        df = df[df['period'].isin(selected_periods)]
    else:
        df = pivot.reset_index().melt(id_vars='industry', var_name='period', value_name='vacancies')

    # convert period string to datetime (period start)
    df['period_dt'] = pd.to_datetime(df['period'].apply(lambda x: x.split('-')[0]), errors='coerce')

    # compute color cap (upper percentile) to reduce outlier effect
    if not df['vacancies'].empty:
        vmax = float(np.nanpercentile(df['vacancies'].astype(float), cap_pct))
    else:
        vmax = None

    color_scale = alt.Scale(scheme=palette)
    if vmax is not None and vmax > 0:
        color_scale = alt.Scale(scheme=palette, domain=[0, vmax])

    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X('period_dt:T', title='Period', axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('industry:N', sort='-x'),
        color=alt.Color('vacancies:Q', scale=color_scale),
        tooltip=['industry', 'period', 'vacancies']
    ).properties(height=500)

    st.altair_chart(chart, use_container_width=True)

    st.markdown('Download heatmap data (CSV)')
    st.download_button('Download CSV', pivot.reset_index().to_csv(index=False), file_name='industry_heatmap.csv')