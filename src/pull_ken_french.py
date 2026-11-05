"""Pull the daily risk-free rate from Ken French's data library.

Each row of the output is one trading day:

- date: the trading date
- rf: the daily risk-free rate, in percent as French reports it

French's rf is the simple daily rate that compounds to the one-month T-bill rate
over the trading days of the month, so it is constant within a month.
"""

from pathlib import Path

import pandas as pd
import pandas_datareader as pdr

from settings import config

DATA_DIR = Path(config("DATA_DIR"))
START_DATE = config("START_DATE")
END_DATE = config("END_DATE")

DATASET = "F-F_Research_Data_Factors_daily"


def pull_ken_french_rf(start_date=START_DATE, end_date=END_DATE):
    """Pull the daily risk-free rate from the Fama-French daily factors file."""
    factors = pdr.DataReader(DATASET, "famafrench", start=start_date, end=end_date)[0]
    df = factors[["RF"]].rename(columns={"RF": "rf"}).reset_index(names="date")
    df["date"] = df["date"].dt.to_timestamp()
    return df


def load_ken_french_rf(data_dir=DATA_DIR):
    return pd.read_parquet(Path(data_dir) / "ken_french_rf.parquet")


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_rf = pull_ken_french_rf()
    df_rf.to_parquet(DATA_DIR / "ken_french_rf.parquet")
