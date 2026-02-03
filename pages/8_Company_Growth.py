import streamlit as st
import pandas as pd
import altair as alt
from utils import compute_company_growth, load_company_vacancies, compute_company_yoy_growth, cluster_companies

st.title('Company Vacancy Growth — Top Movers & Clusters 📈')

DB_PATH = st.text_input('SQLite DB path', value='data/visual.db')
TOP_N = st.slider('Top movers N', 5, 200, 20)

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
    show_yoy = st.checkbox('Also show Year-over-Year top table', value=True)
    if show_yoy:
        yoy = compute_company_yoy_growth(DB_PATH, top_n=TOP_N)
        if not yoy.empty:
            yoy['yoy_pct'] = yoy['yoy_pct'].apply(lambda x: ('∞ (new)' if x==float('inf') else f"{x:.1f}%"))
            st.markdown('**Year-over-year (annual) top movers**')
            st.table(yoy)
            st.download_button('Download YoY CSV', yoy.to_csv(index=False), file_name='company_yoy_top.csv')

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

    # --- Clustering interface ---
    st.markdown('---')
    st.subheader('Cluster companies by vacancy patterns')
    n_clusters = st.slider('Number of clusters', 2, 20, 5)
    cluster_top_n = st.slider('Number of companies to consider (top by vacancies)', 20, 1000, 200)
    if st.button('Run clustering'):
        cl_df, pca, kmeans = cluster_companies(DB_PATH, n_clusters=n_clusters, top_n=cluster_top_n)
        if cl_df.empty:
            st.info('Clustering produced no results. Ensure DB is available and contains data.')
        else:
            st.markdown('**Cluster assignments (sample)**')
            st.table(cl_df.head(50))
            # cluster counts
            counts = cl_df['cluster'].value_counts().sort_index()
            st.bar_chart(counts)
            chosen = st.selectbox('Select cluster to inspect', options=sorted(cl_df['cluster'].unique().tolist()))
            members = cl_df[cl_df['cluster']==chosen]['company'].tolist()
            st.markdown(f'Companies in cluster {chosen} (showing up to 200)')
            st.write(members[:200])
            # plot time series for selected cluster
            if members:
                dfc = load_company_vacancies(DB_PATH)
                dfc = dfc[dfc['company'].isin(members)].copy()
                dfc['period_dt'] = pd.to_datetime(dfc['period'], errors='coerce')
                chart2 = alt.Chart(dfc).mark_line().encode(x='period_dt:T', y='vacancies:Q', color='company:N')
                st.altair_chart(chart2, use_container_width=True)
            st.download_button('Download cluster assignments CSV', cl_df.to_csv(index=False), file_name='company_clusters.csv')