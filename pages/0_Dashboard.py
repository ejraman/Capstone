import streamlit as st
import pandas as pd
import altair as alt
from utils import stream_summary, read_sample, clean_salary_series, parse_categories

st.set_page_config(page_title="Executive Dashboard", layout="wide")

st.title("Executive Dashboard — SG Job Market Overview 🧭")
st.markdown(
    "High-level dashboard consolidating the `pages/` analyses. Target audience: **Employers**, **Talent teams**, **MOM management**. Use the controls to adjust sampling and aggregation for performance.")

# Controls
with st.sidebar:
    st.header("Quick controls")
    csv_path = st.text_input("CSV path", value="data/SGJobData (2).csv")
    sample_size = st.slider("Sample for interactive views", 1000, 200000, 20000, step=1000)
    date_freq = st.selectbox("Time aggregation", ["W", "M"], format_func=lambda x: "Weekly" if x=="W" else "Monthly")
    top_n = st.slider("Top N", 5, 30, 10)
    st.markdown("---")
    st.markdown("**Pages**")
    st.write("• 1_Overview — general view")
    st.write("• 2_Salary_Insights — salary breakdowns")
    st.write("• 3_Company_Trends — employer activity")
    st.write("• 4_Skills_Analysis — skill demand and gaps")

# Load summary (streamed)
with st.spinner("Streaming and summarizing dataset... this may take a moment"):
    summary = stream_summary(csv_path, sample_size=sample_size, date_freq=date_freq)

# KPI row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total postings", f"{summary['total_rows']:,}")
k2.metric("Open postings", f"{summary['status_counts'].get('Open', 0):,}")
k3.metric("Avg. salary (sample)", f"${summary['average_salary']:.0f}")
k4.metric("Unique employers", f"{summary['unique_companies']:,}")

st.markdown("---")

# Trends
st.subheader("Trends & signals 📈")
col1, col2 = st.columns([3,2])
with col1:
    st.markdown("**Postings over time**")
    po = summary['postings_over_time'].reset_index()
    po.columns = ['period', 'postings']
    line = alt.Chart(po).mark_line().encode(x=alt.X('period:T', title='Period'), y='postings:Q')
    st.altair_chart(line, use_container_width=True)

    st.markdown("**Vacancies over time**")
    vac = summary['vacancies_over_time'].reset_index()
    vac.columns = ['period', 'vacancies']
    vline = alt.Chart(vac).mark_line(color='orange').encode(x='period:T', y='vacancies:Q')
    st.altair_chart(vline, use_container_width=True)

with col2:
    st.markdown("**Status mix**")
    st.write(pd.DataFrame.from_dict(summary['status_counts'], orient='index', columns=['count']).sort_values('count', ascending=False))
    st.markdown("**Top employers (by postings)**")
    topc = pd.DataFrame(summary['top_companies'][:top_n], columns=['company','count'])
    st.table(topc.head(top_n))

st.markdown("---")

# Salary snapshot
st.subheader("Salary snapshot 💵")
sal = pd.Series(summary['sample_salaries'])
sal = sal[sal > 0]
if len(sal) == 0:
    st.info("No salary sample available.")
else:
    sal_df = pd.DataFrame({'salary': sal})
    hist = alt.Chart(sal_df).mark_bar().encode(x=alt.X('salary:Q', bin=alt.Bin(maxbins=60)), y='count()')
    st.altair_chart(hist, use_container_width=True)
    st.write(f"Sampled salaries: {len(sal):,}; mean = ${sal.mean():.0f}")

st.markdown("---")

# Skills & categories
st.subheader("Category & skills signals 🧩")
cats = pd.DataFrame(summary['top_categories'][:top_n], columns=['category','count'])
st.table(cats)

# Simple skill extraction from titles (from sample rows)
st.markdown("**Top words in job titles (proxy for skill keywords)**")
from collections import Counter
import re
words = Counter()
for r in summary['sample_rows']:
    t = r.get('title','')
    if not t: continue
    # tokenize
    for w in re.findall(r"\b[A-Za-z0-9\+#\.\-]+\b", t.lower()):
        if len(w) > 2 and w not in ("and","with","for","the","up","to"):
            words[w] += 1
top_words = pd.DataFrame(words.most_common(top_n), columns=['word','count'])
st.table(top_words)

st.markdown("---")

# Audience sections
st.subheader("Audience highlights 🎯")
st.markdown("**Employers:** monitor top competing employers, time peaks, and salary bands for roles you hire for. Use the `3_Company_Trends` page for deep employer activity analysis.")
st.markdown("**Talent search teams:** focus on categories and top title keywords to refine sourcing; use `4_Skills_Analysis` to explore skill gaps and clustering.")
st.markdown("**MOM management:** watch vacancy growth, open vs closed rates, and category concentration for policy signals. The `1_Overview` and `2_Salary_Insights` pages hold complementary views.")

st.markdown("---")

# Quick navigation buttons
st.subheader("Jump to analyses")
col_a, col_b, col_c, col_d = st.columns(4)
if col_a.button("Overview"):
    st.experimental_set_query_params(page='pages/1_Overview')
if col_b.button("Salary insights"):
    st.experimental_set_query_params(page='pages/2_Salary_Insights')
if col_c.button("Company trends"):
    st.experimental_set_query_params(page='pages/3_Company_Trends')
if col_d.button("Skills analysis"):
    st.experimental_set_query_params(page='pages/4_Skills_Analysis')

st.markdown("---")

st.info("This dashboard aggregates the existing `pages/` analyses and provides a one-page executive view. Adjust sample size for faster runs or larger samples for more precision.")
