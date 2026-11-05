import pytest

import pull_ken_french


@pytest.fixture(scope="module")
def df_paper_sample():
    df = pull_ken_french.load_ken_french_rf()
    return df[df["date"].between("1994-09-01", "2011-03-31")]


def test_columns_and_trading_days_in_paper_sample(df_paper_sample):
    assert list(df_paper_sample.columns) == ["date", "rf"]
    assert len(df_paper_sample) == 4176
    assert df_paper_sample["rf"].notna().all()


def test_rf_is_constant_within_month_and_in_percent(df_paper_sample):
    months = df_paper_sample["date"].dt.to_period("M")
    assert df_paper_sample.groupby(months)["rf"].nunique().eq(1).all()
    assert df_paper_sample["rf"].mean() == pytest.approx(0.0129, abs=0.0005)
