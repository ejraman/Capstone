# Streamlit Dashboard — SG Job Market

This Streamlit app summarizes and visualizes `SGJobData (2).csv` (large file ~273MB) by streaming the CSV in chunks and creating sampled datasets for interactive charts.

## Quick start
1. Create a Python environment (recommended: conda) and install requirements:

   conda create -n jobdash python=3.10 -y
   conda activate jobdash
   pip install -r requirements.txt

2. Run the app from the `capstone/` folder:

   streamlit run streamlit_app.py

3. Open the displayed URL (usually `http://localhost:8501`) and use the sidebar to configure sample size, time aggregation, and percentile clipping.

## Notes
- The loader is designed to stream the data to avoid excessive memory use. It produces a sample for interactive visualizations.
- If you want faster iteration during development, create a small subsampled CSV and point the app at it via the sidebar.

## New visual pages
- **7_Industry_Heatmap:** industry × time heatmap for vacancy intensity (`pages/7_Industry_Heatmap.py`).
- **8_Company_Growth:** top company movers and growth sparklines (`pages/8_Company_Growth.py`).
- **9_Policy_Editor:** editable policy notes/flags for companies/industries (`pages/9_Policy_Editor.py`).

## Visual DB
Use `scripts/build_visual_db.py` to create `data/visual.db` (already included) which powers the company and industry pages. Example:

    python scripts/build_visual_db.py --csv "data/SGJobData (2).csv" --db data/visual.db

The `pages/` UI reads `data/visual.db` by default. If you prefer, you can rebuild the DB with a different date aggregation (weekly/monthly).

## Automation & deployment
- A GitHub Action `refresh_visual_db.yml` (scheduled weekly and run-on-demand) will rebuild `data/visual.db` and upload it as a workflow artifact.
- A Dockerfile and `deploy_docker.yml` workflow are included to build and push a container image to GitHub Container Registry (`ghcr.io/<owner>/capstone:latest`). The workflow uses the repository's `GITHUB_TOKEN` so no additional secrets are required for pushing to GHCR for the same owner. To use a different registry or deploy to a hosting provider, we can update the workflow and add secrets (e.g., cloud provider credentials).
- The executive brief PDF can be exported from the app via the **Executive Brief** page (creates charts and a downloadable PDF).

## Screenshots 📸
Here are example snapshots generated from a representative sample of the dataset. These are saved under the `screenshots/` folder; you can regenerate them using `scripts/generate_screenshots.py`.

- **Executive dashboard:** ![0_Dashboard](screenshots/0_Dashboard.png)
- **Overview:** ![1_Overview](screenshots/1_Overview.png)
- **Salary Insights:** ![2_Salary_Insights](screenshots/2_Salary_Insights.png)
- **Company Trends:** ![3_Company_Trends](screenshots/3_Company_Trends.png)
- **Skills Analysis:** ![4_Skills_Analysis](screenshots/4_Skills_Analysis.png)

## Repository cleanup (important) ⚠️
To keep the repository small and avoid exceeding GitHub file-size limits, the large dataset `data/SGJobData (2).csv` was removed from the repository history.

A backup of the prior remote `main` branch was created as `backup-remote-main` before this change; if you need the previous history, you can inspect or restore from that branch.

If you want me to remove other large files or add metadata about dataset provenance (e.g., external storage links), I can add that as well.
