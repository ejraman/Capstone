import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from utils import stream_summary, industry_heatmap_matrix, compute_company_yoy_growth, compute_company_growth, load_company_vacancies

st.title('Executive Brief — PDF Export 🧾')

DB_PATH = st.text_input('SQLite DB path', value='data/visual.db')
CSV_PATH = st.text_input('CSV path', value='data/SGJobData (2).csv')
SAMPLE_SIZE = st.number_input('Sample size for summary', value=20000, min_value=1000, step=1000)

if st.button('Generate and download PDF brief'):
    with st.spinner('Building executive PDF...'):
        # Basic summary
        summary = stream_summary(CSV_PATH, sample_size=SAMPLE_SIZE, date_freq='W')
        # Create matplotlib figures and capture as PNG bytes
        imgs = []

        # Postings over time
        po = summary['postings_over_time']
        fig, ax = plt.subplots(figsize=(8,3))
        po.plot(ax=ax)
        ax.set_title('Postings over time')
        ax.set_xlabel('Period')
        ax.set_ylabel('Postings')
        buf = BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); buf.seek(0)
        imgs.append(('Postings', buf.read()))
        plt.close(fig)

        # Salary histogram (sample)
        import numpy as np
        sals = np.array(summary['sample_salaries']); sals = sals[sals>0]
        fig, ax = plt.subplots(figsize=(8,3))
        if len(sals):
            ax.hist(sals, bins=40, color='tab:green')
            ax.set_title('Salary distribution (sample)')
        else:
            ax.text(0.5,0.5,'No salary data', ha='center')
        buf = BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); buf.seek(0)
        imgs.append(('Salaries', buf.read()))
        plt.close(fig)

        # Industry heatmap snapshot (small)
        hm = industry_heatmap_matrix(DB_PATH, top_n=10)
        if not hm.empty:
            fig, ax = plt.subplots(figsize=(8,4))
            import seaborn as sns
            sns.heatmap(hm, ax=ax, cmap='Reds')
            ax.set_title('Industry heatmap (top 10)')
            buf = BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); buf.seek(0)
            imgs.append(('Heatmap', buf.read()))
            plt.close(fig)

        # Top YoY
        yoy = compute_company_yoy_growth(DB_PATH, top_n=10)

        # Build PDF
        pdf_buf = BytesIO()
        c = canvas.Canvas(pdf_buf, pagesize=letter)
        width, height = letter
        # Title
        c.setFont('Helvetica-Bold', 16)
        c.drawString(40, height - 40, 'Executive Brief — SG Job Market')
        c.setFont('Helvetica', 10)
        c.drawString(40, height - 58, f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}')
        # Write KPIs
        c.drawString(40, height - 80, f"Total postings: {summary['total_rows']:,}")
        c.drawString(240, height - 80, f"Open: {summary['status_counts'].get('Open',0):,}")
        c.drawString(40, height - 96, f"Avg salary (sample): ${summary['average_salary']:.0f}")
        # Add images
        y = height - 140
        for title, img in imgs:
            if y < 200:
                c.showPage()
                y = height - 40
            c.setFont('Helvetica-Bold', 12)
            c.drawString(40, y, title)
            y -= 16
            # draw image
            from reportlab.lib.utils import ImageReader
            img_reader = ImageReader(BytesIO(img))
            c.drawImage(img_reader, 40, y-160, width=520, height=150, preserveAspectRatio=True)
            y -= 170
        # Add YoY table
        if not yoy.empty:
            c.showPage()
            c.setFont('Helvetica-Bold', 12)
            c.drawString(40, height - 40, 'Top YoY company movers')
            y = height - 60
            c.setFont('Helvetica', 9)
            cols = ['company','last_year_total','prev_year_total','yoy_pct']
            for i, row in yoy.iterrows():
                txt = f"{row['company'][:40]:40} | {row['last_year_total']:6} | {row['prev_year_total']:6} | {row['yoy_pct']:.1f}%"
                c.drawString(40, y, txt)
                y -= 14
                if y < 60:
                    c.showPage()
                    y = height - 40
        c.save()
        pdf_buf.seek(0)

        st.download_button('Download Executive PDF', pdf_buf, file_name='executive_brief.pdf', mime='application/pdf')
        st.success('PDF ready for download')
