"""Pull scheduled FOMC meeting dates and announcement times from the PDF of the
Lucca and Moench (2015) Internet Appendix, Table IA.I.

Each row of the output is one scheduled meeting:

- date: the meeting (announcement) date
- meeting_number: the meeting's order within the year (1-8)
- announcement_datetime: the announcement's date and time, in Eastern Time (naive)
- excluded: True if the table marks the meeting as excluded from the paper's sample

Excluded meetings are kept and flagged rather than dropped. Note that the paper's
intraday sample also loses Jul 1, 1998 to missing intraday data (footnote 10), which
is not marked in this table, leaving 131 of the 132 non-excluded meetings.
"""

import re

import pandas as pd
import pdfplumber

from settings import config

BASE_DIR = config("BASE_DIR")
DATA_DIR = config("DATA_DIR")

APPENDIX_PATH = (
    BASE_DIR
    / "references"
    / "ThePreFOMCAnnouncementDriftInternetAppendix_Lucca_Moench_2015.pdf"
)
TABLE_TITLE = "Table IA.I Scheduled FOMC Meeting Dates and Times: 1994-2011"

DATE_ROW = re.compile(r"^(?:19|20)\d{2}((?: \d{1,2}-[A-Z][a-z]{2}-\d{2}e?)+)$")
TIME_ROW = re.compile(r"^\[\d{2}:\d{2}\](?: \[\d{2}:\d{2}\])*$")

N_MEETINGS = 138  # 8 per year for 1994-2010, plus 2 in 2011
N_EXCLUDED = 6


def _read_table_text(pdf_path):
    """Return the text of the appendix page that holds Table IA.I."""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if TABLE_TITLE in text:
                return text
    raise ValueError(f"Could not find '{TABLE_TITLE}' in {pdf_path}")


def _parse_table_text(text):
    """Parse the table's alternating rows of dates and bracketed times."""
    rows = []
    dates = None
    for line in text.splitlines():
        line = line.strip()
        if match := DATE_ROW.match(line):
            dates = match.group(1).split()
        elif TIME_ROW.match(line):
            times = line.split()
            if dates is None or len(dates) != len(times):
                raise ValueError(f"Times do not line up with dates: {line}")
            for number, (date, time) in enumerate(zip(dates, times), start=1):
                rows.append(
                    {
                        "date": date.removesuffix("e"),
                        "meeting_number": number,
                        "time": time.strip("[]"),
                        "excluded": date.endswith("e"),
                    }
                )
            dates = None

    df = pd.DataFrame(rows)
    df["announcement_datetime"] = pd.to_datetime(
        df["date"] + " " + df["time"], format="%d-%b-%y %H:%M"
    )
    df["date"] = df["announcement_datetime"].dt.normalize()
    return df[["date", "meeting_number", "announcement_datetime", "excluded"]]


def _validate(df):
    """Check the parsed table against what is known about it from the paper."""
    if len(df) != N_MEETINGS:
        raise ValueError(f"Expected {N_MEETINGS} meetings, parsed {len(df)}")
    if df["excluded"].sum() != N_EXCLUDED:
        raise ValueError(
            f"Expected {N_EXCLUDED} excluded meetings, parsed {df['excluded'].sum()}"
        )
    if not df["date"].is_monotonic_increasing or not df["date"].is_unique:
        raise ValueError("Meeting dates are not strictly increasing")


def pull_fomc_dates(pdf_path=APPENDIX_PATH):
    """Parse Table IA.I from the Internet Appendix PDF into a dataframe."""
    df = _parse_table_text(_read_table_text(pdf_path))
    _validate(df)
    return df


def load_fomc_dates(data_dir=DATA_DIR):
    return pd.read_parquet(data_dir / "fomc_dates.parquet")


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_fomc_dates = pull_fomc_dates()
    df_fomc_dates.to_parquet(DATA_DIR / "fomc_dates.parquet")
