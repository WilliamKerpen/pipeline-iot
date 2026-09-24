"""Testes unit\u00e1rios das transforma\u00e7\u00f5es e filtros do dom\u00ednio."""

from datetime import date

import pandas as pd

from services.temperature_service import (
    compare_periods,
    filter_by_period,
    make_month_options,
    normalize_columns,
)


def sample_readings() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["a", "b", "c", "d"],
            "noted_date": pd.to_datetime(
                ["2024-01-01 10:00", "2024-01-28 10:00", "2024-02-01 10:00", "2024-02-03 10:00"]
            ),
            "temp": [20.0, 22.0, 24.0, 26.0],
        }
    )


def test_normalize_columns_converts_csv_headers():
    dataframe = pd.DataFrame(columns=["room_id/id", "out/in", " Temp * "])

    assert list(normalize_columns(dataframe).columns) == ["room_id_id", "out_in", "temp_"]


def test_filter_by_period_returns_last_week_from_most_recent_reading():
    result = filter_by_period(sample_readings(), "\u00daltima semana")

    assert result["id"].tolist() == ["b", "c", "d"]


def test_make_month_options_returns_chronological_month_starts():
    assert make_month_options(sample_readings()) == [date(2024, 1, 1), date(2024, 2, 1)]


def test_compare_periods_compares_two_months():
    result = compare_periods(sample_readings(), "Comparar dois meses", date(2024, 1, 1), date(2024, 2, 1))

    assert result is not None
    assert result["avg_a"] == 21.0
    assert result["avg_b"] == 25.0
    assert result["diff"] == -4.0
