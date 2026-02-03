"""Build a visual SQLite database from the large job CSV for fast dashboard queries.

Produces `data/visual.db` with tables:
 - companies(id INTEGER PRIMARY KEY, name TEXT)
 - vacancies(company_id INTEGER, period TEXT, year INTEGER, month INTEGER, week INTEGER, vacancies INTEGER, postings INTEGER)
 - industry_vacancies(industry TEXT, period TEXT, vacancies INTEGER, postings INTEGER)

Usage:
    python scripts/build_visual_db.py --csv data/SGJobData\ \(2\).csv --db data/visual.db --date-freq W
"""
import argparse
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict
import json


def primary_category(cat_str):
    if not isinstance(cat_str, str) or not cat_str:
        return None
    try:
        arr = json.loads(cat_str)
        if isinstance(arr, list) and arr:
            return arr[0].get('category')
    except Exception:
        # naive parse
        try:
            s = cat_str
            idx = s.find('"category":')
            if idx >= 0:
                sub = s[idx+len('"category":'):]
                # find next '"'
                q = sub.find('"')
                if q >= 0:
                    return sub[q+1:sub.find('"', q+1)]
        except Exception:
            pass
    return None


def build_db(csv_path, db_path, chunksize=20000, date_freq='W'):
    p_csv = Path(csv_path)
    p_db = Path(db_path)
    if not p_csv.exists():
        raise FileNotFoundError(f"CSV not found: {p_csv}")

    conn = sqlite3.connect(str(p_db))
    cur = conn.cursor()

    # create tables
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS vacancies (
        company_id INTEGER,
        period TEXT,
        year INTEGER,
        month INTEGER,
        week INTEGER,
        vacancies INTEGER,
        postings INTEGER
    );
    CREATE TABLE IF NOT EXISTS industry_vacancies (
        industry TEXT,
        period TEXT,
        vacancies INTEGER,
        postings INTEGER
    );
    ''')
    conn.commit()

    company_id_map = {}

    # aggregates as dicts: (company, period) -> (vacancies_sum, postings_count)
    comp_period_vac = defaultdict(lambda: [0, 0])
    ind_period_vac = defaultdict(lambda: [0, 0])

    it = pd.read_csv(p_csv, chunksize=chunksize, iterator=True, dtype=str)
    total = 0
    print('Streaming CSV and aggregating...')
    for chunk in it:
        total += len(chunk)
        # parse dates
        dates = pd.to_datetime(chunk['metadata_newPostingDate'], errors='coerce')
        periods = dates.dt.to_period(date_freq)
        companies = chunk['postedCompany_name'].fillna('UNKNOWN')
        vacs = chunk.get('numberOfVacancies', pd.Series(1, index=chunk.index)).fillna('1')
        # ensure numeric
        vacs = pd.to_numeric(vacs, errors='coerce').fillna(0).astype(int)

        # categories
        cats = chunk['categories'].fillna('')
        for comp, p, v, cat_str in zip(companies.values, periods.values, vacs.values, cats.values):
            if pd.isna(p):
                continue
            period = str(p)
            comp_period_vac[(comp, period)][0] += int(v)
            comp_period_vac[(comp, period)][1] += 1
            ind = primary_category(cat_str) or 'Unknown'
            ind_period_vac[(ind, period)][0] += int(v)
            ind_period_vac[(ind, period)][1] += 1
    print('Aggregated rows:', total)

    print('Inserting companies...')
    # insert companies
    comps = set(k[0] for k in comp_period_vac.keys())
    for c in comps:
        if c in ('', None):
            continue
        try:
            cur.execute('INSERT OR IGNORE INTO companies (name) VALUES (?)', (c,))
        except Exception:
            continue
    conn.commit()

    # load company id map
    cur.execute('SELECT id, name FROM companies')
    for _id, name in cur.fetchall():
        company_id_map[name] = _id

    print('Inserting vacancy aggregates (companies)...')
    rows = []
    for (comp, period), (vac_sum, postings) in comp_period_vac.items():
        cid = company_id_map.get(comp)
        if cid is None:
            # try to insert
            cur.execute('INSERT OR IGNORE INTO companies (name) VALUES (?)', (comp,))
            conn.commit()
            cur.execute('SELECT id FROM companies WHERE name=?', (comp,))
            cid = cur.fetchone()[0]
            company_id_map[comp] = cid
        # parse year/month/week
        try:
            per = pd.Period(period)
            year = per.start_time.year
            month = per.start_time.month
            week = per.start_time.isocalendar()[1]
        except Exception:
            year = month = week = None
        rows.append((cid, period, year, month, week, vac_sum, postings))

    cur.executemany('INSERT INTO vacancies VALUES (?,?,?,?,?,?,?)', rows)
    conn.commit()

    print('Inserting industry vacancy aggregates...')
    rows = []
    for (ind, period), (vac_sum, postings) in ind_period_vac.items():
        rows.append((ind, period, vac_sum, postings))
    cur.executemany('INSERT INTO industry_vacancies VALUES (?,?,?,?)', rows)
    conn.commit()

    conn.close()
    print('DB built at', p_db)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='data/SGJobData (2).csv')
    parser.add_argument('--db', default='data/visual.db')
    parser.add_argument('--chunksize', type=int, default=20000)
    parser.add_argument('--date-freq', default='W')
    args = parser.parse_args()
    build_db(args.csv, args.db, chunksize=args.chunksize, date_freq=args.date_freq)
