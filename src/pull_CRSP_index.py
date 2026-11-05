"""Pull the daily CRSP S&P 500 index file from WRDS (crsp_a_indexes.dsp500).

Each row of the output is one trading day:

- caldt: the calendar date
- sprtrn: the S&P 500 index price return, excluding dividends
- vwretd: the value-weighted return on the index constituents, including dividends
- vwretx: the value-weighted return on the index constituents, excluding dividends

All three are simple returns in decimals. The index's cum-dividend return is
sprtrn + (vwretd - vwretx), where the difference is the day's dividend return.

Key resources:
 - Data for indices: https://wrds-www.wharton.upenn.edu/data-dictionary/crsp_a_indexes/
 - Transition FAQ: https://wrds-www.wharton.upenn.edu/pages/support/manuals-and-overviews/crsp/stocks-and-indices/crsp-stock-and-indexes-version-2/crsp-ciz-faq/
"""

from pathlib import Path

import pandas as pd
import wrds

from settings import config

DATA_DIR = Path(config("DATA_DIR"))
WRDS_USERNAME = config("WRDS_USERNAME")
START_DATE = config("START_DATE")
END_DATE = config("END_DATE")


def pull_CRSP_index_files(
    start_date=START_DATE, end_date=END_DATE, wrds_username=WRDS_USERNAME
):
    """Pull daily S&P 500 returns from crsp_a_indexes.dsp500."""
    query = f"""
        SELECT caldt, sprtrn, vwretd, vwretx
        FROM crsp_a_indexes.dsp500
        WHERE caldt BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY caldt
    """
    db = wrds.Connection(wrds_username=wrds_username)
    df = db.raw_sql(query, date_cols=["caldt"])
    db.close()
    return df


def load_CRSP_index_files(data_dir=DATA_DIR):
    path = Path(data_dir) / "CRSP_DSP500.parquet"
    df = pd.read_parquet(path)
    return df


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_dsp500 = pull_CRSP_index_files(start_date=START_DATE, end_date=END_DATE)
    path = DATA_DIR / "CRSP_DSP500.parquet"
    df_dsp500.to_parquet(path)
