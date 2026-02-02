"""Generate representative PNG screenshots for each Streamlit page by sampling the data
and rendering charts/tables. Images are saved to `screenshots/` directory.
"""
import os
from pathlib import Path
import sys
# ensure project root is on sys.path so imports of local modules work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import numpy as np

from utils import stream_summary, read_sample, clean_salary_series

OUT_DIR = Path('screenshots')
OUT_DIR.mkdir(exist_ok=True)
CSV_PATH = Path('data/SGJobData (2).csv')

print('Sampling data and computing summary (may take a while)')
summary = stream_summary(CSV_PATH, sample_size=20000, date_freq='W')

# 0_Dashboard: create composite image
print('Creating dashboard screenshot')
plt.style.use('ggplot')
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
# Postings over time
post = summary['postings_over_time']
if not post.empty:
    post.plot(ax=axes[0,0], title='Postings over time')
else:
    axes[0,0].text(0.5,0.5,'No data', ha='center')
# Top companies
topc = summary['top_companies'][:10]
if topc:
    comps, counts = zip(*topc)
    axes[0,1].barh(comps, counts)
    axes[0,1].invert_yaxis()
    axes[0,1].set_title('Top employers (by postings)')
else:
    axes[0,1].text(0.5,0.5,'No data', ha='center')
# Salary histogram
sals = np.array(summary['sample_salaries'])
if len(sals):
    sals = sals[sals>0]
    axes[1,0].hist(sals, bins=40, color='tab:green')
    axes[1,0].set_title('Salary distribution (sample)')
else:
    axes[1,0].text(0.5,0.5,'No salary data', ha='center')
# Top categories
topcat = summary['top_categories'][:10]
if topcat:
    cats, ccounts = zip(*topcat)
    axes[1,1].barh(cats, ccounts)
    axes[1,1].invert_yaxis()
    axes[1,1].set_title('Top categories')
else:
    axes[1,1].text(0.5,0.5,'No data', ha='center')

plt.tight_layout()
out0 = OUT_DIR / '0_Dashboard.png'
fig.savefig(out0, dpi=150)
plt.close(fig)
print('Saved', out0)

# For pages 1-4: render a table image using sample rows
sample_df = pd.DataFrame(summary['sample_rows'])
if sample_df.empty:
    sample_df = read_sample(CSV_PATH, nrows=100)

pages = {
    '1_Overview': sample_df.head(10),
    '2_Salary_Insights': sample_df[['title','postedCompany_name','salary_minimum','salary_maximum','average_salary']].head(10) if 'salary_minimum' in sample_df.columns else sample_df.head(10),
    '3_Company_Trends': sample_df[['postedCompany_name','title','metadata_newPostingDate']].head(10) if 'postedCompany_name' in sample_df.columns else sample_df.head(10),
    '4_Skills_Analysis': sample_df[['title','positionLevels']].head(10) if 'positionLevels' in sample_df.columns else sample_df.head(10)
}

# Helper to draw table as image
def df_to_image(df: pd.DataFrame, title: str, out_path: Path):
    # Create white canvas
    font = ImageFont.load_default()
    padding = 10
    col_width = 220
    row_height = 18
    ncols = min(len(df.columns), 6)
    nrows = len(df)
    width = padding*2 + ncols * col_width
    height = padding*3 + 30 + nrows * row_height

    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    # Title
    draw.text((padding, 5), title, fill='black', font=font)
    # Header
    y = 40
    x = padding
    for i, c in enumerate(df.columns[:ncols]):
        draw.text((x + i*col_width, y), str(c), fill='black', font=font)
    y += row_height
    # Rows
    for r in range(nrows):
        for i, c in enumerate(df.columns[:ncols]):
            txt = str(df.iloc[r][c])
            if len(txt) > 60:
                txt = txt[:57] + '...'
            draw.text((x + i*col_width, y + r*row_height), txt, fill='black', font=font)
    img.save(out_path)
    print('Saved', out_path)

for name, df in pages.items():
    out = OUT_DIR / f'{name}.png'
    df_to_image(df, name.replace('_',' '), out)

print('All screenshots generated in', OUT_DIR)
