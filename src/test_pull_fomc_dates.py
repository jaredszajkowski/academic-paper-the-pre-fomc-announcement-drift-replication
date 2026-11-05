import pandas as pd
import pytest

import pull_fomc_dates
from settings import config

BASE_DIR = config("BASE_DIR")
PAPER_PATH = (
    BASE_DIR / "references" / "ThePreFOMCAnnouncementDrift_Lucca_Moench_2015.pdf"
)


@pytest.fixture(scope="module")
def df_fomc_dates():
    return pull_fomc_dates.pull_fomc_dates()


def test_columns_and_types(df_fomc_dates):
    assert list(df_fomc_dates.columns) == [
        "date",
        "meeting_number",
        "announcement_datetime",
        "excluded",
    ]
    assert pd.api.types.is_datetime64_any_dtype(df_fomc_dates["date"])
    assert pd.api.types.is_datetime64_any_dtype(df_fomc_dates["announcement_datetime"])
    assert pd.api.types.is_bool_dtype(df_fomc_dates["excluded"])


def test_eight_meetings_per_year_through_2010(df_fomc_dates):
    per_year = df_fomc_dates.groupby(df_fomc_dates["date"].dt.year).size()
    assert per_year.index.tolist() == list(range(1994, 2012))
    assert (per_year.loc[:2010] == 8).all()
    assert per_year.loc[2011] == 2


def test_meetings_numbered_in_order_within_year(df_fomc_dates):
    expected = df_fomc_dates.groupby(df_fomc_dates["date"].dt.year).cumcount() + 1
    assert df_fomc_dates["meeting_number"].tolist() == expected.tolist()


@pytest.mark.parametrize(
    "date, meeting_number, time, excluded",
    [
        ("1994-02-04", 1, "11:05", True),  # First row of the table
        ("1994-09-27", 6, "14:18", False),  # First meeting not excluded
        ("1996-03-26", 2, "11:39", True),  # Morning release, paper footnote 7
        ("1998-07-01", 4, "14:14", False),  # Paper footnote 10
        ("2008-12-16", 8, "14:11", False),  # Earliest time in the paper's sample
        ("2011-03-15", 2, "14:13", False),  # Last entry of the table
    ],
)
def test_known_meetings(df_fomc_dates, date, meeting_number, time, excluded):
    row = df_fomc_dates[df_fomc_dates["date"] == pd.Timestamp(date)]
    assert len(row) == 1
    assert row["meeting_number"].item() == meeting_number
    assert row["announcement_datetime"].item() == pd.Timestamp(f"{date} {time}")
    assert row["excluded"].item() == excluded


def test_excluded_meetings_match_table(df_fomc_dates):
    excluded = df_fomc_dates.loc[df_fomc_dates["excluded"], "date"]
    assert excluded.tolist() == [
        pd.Timestamp(date)
        for date in [
            "1994-02-04",
            "1994-03-22",
            "1994-05-17",
            "1994-07-06",
            "1994-08-16",
            "1996-03-26",
        ]
    ]


def test_sample_size_matches_paper(df_fomc_dates):
    """The paper reports 131 meetings after losing Jul 1, 1998 (footnote 10)."""
    sample = df_fomc_dates[
        ~df_fomc_dates["excluded"]
        & (df_fomc_dates["date"] != pd.Timestamp("1998-07-01"))
    ]
    assert len(sample) == 131


def test_sample_announcements_are_not_before_2_10_pm(df_fomc_dates):
    """The paper states that no announcement in its sample came before 2:10 pm."""
    sample = df_fomc_dates[~df_fomc_dates["excluded"]]
    times = sample["announcement_datetime"].dt.time
    assert (times >= pd.Timestamp("14:10").time()).all()
    assert (times <= pd.Timestamp("14:30").time()).all()


def test_announcement_falls_on_meeting_date(df_fomc_dates):
    assert (
        df_fomc_dates["announcement_datetime"].dt.normalize() == df_fomc_dates["date"]
    ).all()


def test_meetings_fall_on_weekdays(df_fomc_dates):
    assert (df_fomc_dates["date"].dt.day_of_week < 5).all()


def test_load_returns_what_was_saved(df_fomc_dates, tmp_path):
    df_fomc_dates.to_parquet(tmp_path / "fomc_dates.parquet")
    df_loaded = pull_fomc_dates.load_fomc_dates(data_dir=tmp_path)
    pd.testing.assert_frame_equal(df_loaded, df_fomc_dates)


def test_parser_reads_marker_and_ignores_other_lines():
    text = (
        "Year 1st 2nd\n"
        "2000 2-Feb-00 21-Mar-00e\n"
        "[14:14] [11:15]\n"
        "2001 31-Jan-01\n"
        "[14:15]\n"
        "9\n"
    )
    df = pull_fomc_dates._parse_table_text(text)
    assert df["date"].tolist() == [
        pd.Timestamp("2000-02-02"),
        pd.Timestamp("2000-03-21"),
        pd.Timestamp("2001-01-31"),
    ]
    assert df["meeting_number"].tolist() == [1, 2, 1]
    assert df["excluded"].tolist() == [False, True, False]
    assert df["announcement_datetime"].iloc[1] == pd.Timestamp("2000-03-21 11:15")


def test_parser_raises_when_times_do_not_line_up():
    with pytest.raises(ValueError, match="do not line up"):
        pull_fomc_dates._parse_table_text("2000 2-Feb-00 21-Mar-00\n[14:14]\n")


def test_read_raises_when_table_is_missing():
    with pytest.raises(ValueError, match="Could not find"):
        pull_fomc_dates._read_table_text(PAPER_PATH)


@pytest.mark.parametrize(
    "corrupt",
    [
        lambda df: df.iloc[1:],  # A meeting is missing
        lambda df: df.assign(excluded=False),  # The markers were lost
        lambda df: df.iloc[::-1],  # The dates are out of order
    ],
)
def test_validate_rejects_bad_tables(df_fomc_dates, corrupt):
    with pytest.raises(ValueError):
        pull_fomc_dates._validate(corrupt(df_fomc_dates))
