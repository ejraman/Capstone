import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def read_sample(csv_path: str, nrows: int = 20000):
    """Read only first nrows for fast interactive charts."""
    return pd.read_csv(csv_path, nrows=nrows)
def clean_salary_series(s: pd.Series) -> pd.Series:
    """
    Convert salary column that may contain text like '$5,000', '5000-7000', etc. into numeric.
    Returns float Series with NaNs for non-parsable values.
    """
    if s is None:
        return pd.Series(dtype="float64")

    # If already numeric, just return
    if pd.api.types.is_numeric_dtype(s):
        return s.astype("float64")

    x = s.astype(str).str.lower().str.strip()

    # Remove currency symbols and commas
    x = x.str.replace(r"[\$,]", "", regex=True)

    # Handle ranges like "5000-7000" -> take midpoint
    is_range = x.str.contains(r"^\d+(\.\d+)?\s*-\s*\d+(\.\d+)?$")
    mid = pd.Series([None] * len(x), index=x.index, dtype="float64")
    if is_range.any():
        parts = x[is_range].str.split("-", expand=True)
        a = pd.to_numeric(parts[0].str.strip(), errors="coerce")
        b = pd.to_numeric(parts[1].str.strip(), errors="coerce")
        mid.loc[is_range] = (a + b) / 2

    # For non-range, parse as number
    num = pd.to_numeric(x, errors="coerce")

    # Prefer midpoint where range exists
    out = num.astype("float64")
    out.loc[is_range] = mid.loc[is_range]
    return out

import json
from collections import Counter, defaultdict
from datetime import datetime
import math


def parse_categories(cat_str):
    """Return list of category strings from the stored JSON-like string."""
    if not cat_str or not isinstance(cat_str, str):
        return []
    try:
        # data appears to be a JSON array string
        parsed = json.loads(cat_str)
        return [c.get('category') for c in parsed if 'category' in c]
    except Exception:
        # fallback: try to heuristically extract text
        try:
            s = cat_str.strip().strip('[]')
            parts = s.split('"category":')
            cats = []
            for p in parts[1:]:
                # take up to next '"' or '}'
                p = p.strip()
                end = p.find('"')
                if end > 0:
                    cats.append(p[1:end])
            return cats
        except Exception:
            return []


def stream_summary(path, sample_size=20000, date_freq='W'):
    """Stream the CSV and compute summary statistics + a sampled set of rows for interactive charts.

    Returns a dict containing:
      - total_rows
      - status_counts (Counter)
      - top_companies (list of (company, count))
      - top_categories (list of (category, count))
      - average_salary (approx from sums)
      - sample_rows (list of dicts)
      - sample_salaries (list)
      - postings_over_time (pd.Series indexed by period)
      - vacancies_over_time (pd.Series)
      - experience_counts (dict)
      - unique_companies
    """
    chunksize = 20000
    it = pd.read_csv(path, chunksize=chunksize, iterator=True, dtype=str)

    total_rows = 0
    status_counts = Counter()
    company_counts = Counter()
    category_counts = Counter()
    experience_counts = Counter()

    sample_rows = []
    sample_salaries = []

    sum_salary = 0.0
    count_salary = 0

    postings_time = Counter()
    vacancies_time = Counter()

    # for speed: parse column names to expected
    for chunk in it:
        total_rows += len(chunk)
        # status
        sc = chunk['status_jobStatus'].fillna('')
        status_counts.update(sc.values)
        # companies
        companies = chunk['postedCompany_name'].fillna('')
        company_counts.update(companies.values)
        # categories: parse primary category
        cats = chunk['categories'].fillna('')
        for s in cats.values:
            parsed = parse_categories(s)
            if parsed:
                category_counts.update([parsed[0]])
        # experience
        minexp = chunk['minimumYearsExperience'].fillna('')
        # clean and count
        for v in minexp.values:
            try:
                experience_counts[int(v)] += 1
            except Exception:
                experience_counts['unspecified'] += 1
        # salaries
        if 'average_salary' in chunk.columns:
            av = chunk['average_salary'].fillna('')
            for v in av.values:
                try:
                    fv = float(v)
                    count_salary += 1
                    sum_salary += fv
                    if fv > 0:
                        sample_salaries.append(fv)
                except Exception:
                    continue
        # postings over time
        if 'metadata_newPostingDate' in chunk.columns:
            dates = pd.to_datetime(chunk['metadata_newPostingDate'], errors='coerce')
            # group by period
            periods = dates.dt.to_period(date_freq).dropna().astype(str).values
            for p in periods:
                postings_time[p] += 1
        # vacancies
        if 'numberOfVacancies' in chunk.columns and 'metadata_newPostingDate' in chunk.columns:
            dates = pd.to_datetime(chunk['metadata_newPostingDate'], errors='coerce')
            vacancies = chunk['numberOfVacancies'].fillna('0')
            for d, v in zip(dates.values, vacancies.values):
                if pd.isna(d):
                    continue
                try:
                    n = int(v)
                except Exception:
                    n = 0
                p = pd.Period(d, freq=date_freq).strftime('%Y-%m-%d')
                vacancies_time[p] += n
        # reservoir-like sample: sample fractionally from chunk to keep sample <= sample_size
        if len(sample_rows) < sample_size:
            need = sample_size - len(sample_rows)
            # sample min(need, chunk_size)
            s = chunk.sample(n=min(len(chunk), need))
            sample_rows.extend(s.to_dict(orient='records'))
        else:
            # replace with small prob to maintain randomness
            # For simplicity, occasionally replace some samples
            replace_prob = 0.001
            mask = np.random.rand(len(chunk)) < replace_prob
            if mask.any():
                s = chunk[mask]
                for _, r in s.iterrows():
                    idx = np.random.randint(0, len(sample_rows))
                    sample_rows[idx] = r.to_dict()

    avg_salary = sum_salary / count_salary if count_salary else 0.0

    # Postings over time to series
    if postings_time:
        # convert period strings back to timestamp for plotting (period start)
        pst = {pd.Period(k, freq=date_freq).start_time: v for k, v in postings_time.items()}
        postings_series = pd.Series(pst).sort_index()
    else:
        postings_series = pd.Series(dtype=int)

    vacancies_series = pd.Series(dict(sorted(vacancies_time.items())))

    result = {
        'total_rows': total_rows,
        'status_counts': status_counts,
        'top_companies': company_counts.most_common(50),
        'top_categories': category_counts.most_common(50),
        'average_salary': avg_salary,
        'sample_rows': sample_rows,
        'sample_salaries': sample_salaries,
        'postings_over_time': postings_series,
        'vacancies_over_time': vacancies_series,
        'experience_counts': experience_counts,
        'unique_companies': len(company_counts)
    }
    return result
