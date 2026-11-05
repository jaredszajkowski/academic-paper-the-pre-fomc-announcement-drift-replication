import pandas as pd
import pytest

import pull_CRSP_index


@pytest.fixture(scope="module")
def df_dsp500():
    return pull_CRSP_index.load_CRSP_index_files()


def test_columns_and_trading_days_in_paper_sample(df_dsp500):
    assert list(df_dsp500.columns) == ["caldt", "sprtrn", "vwretd", "vwretx"]
    in_sample = df_dsp500["caldt"].between("1994-09-01", "2011-03-31")
    assert in_sample.sum() == 4176
    assert df_dsp500.loc[in_sample].notna().all().all()


def test_known_index_returns_are_decimals(df_dsp500):
    sprtrn = df_dsp500.set_index("caldt")["sprtrn"]
    assert sprtrn[pd.Timestamp("2008-10-13")] == pytest.approx(0.1158, abs=0.001)
    assert sprtrn[pd.Timestamp("2008-10-15")] == pytest.approx(-0.0903, abs=0.001)
