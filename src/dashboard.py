from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import text

from db_connection import get_engine
from ingest_csv import Base, ingest_csv


def ensure_database_ready() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    try:
        with engine.connect() as connection:
            count = connection.execute(text("SELECT COUNT(*) FROM temperature_readings")).scalar()
    except Exception:
        count = 0

    if count == 0:
        ingest_csv()


def ensure_views() -> None:
    engine = get_engine()
    sql_path = Path(__file__).resolve().parent / "create_views.sql"
    sql_text = sql_path.read_text(encoding="utf-8")

    statements = [statement.strip() for statement in sql_text.split(";") if statement.strip()]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


@st.cache_data
def load_temperature_table():
    engine = get_engine()
    df = pd.read_sql(
        "SELECT id, room_id_id, noted_date, temp, out_in FROM temperature_readings ORDER BY noted_date ASC",
        engine,
    )
    df["noted_date"] = pd.to_datetime(df["noted_date"])
    return df


@st.cache_data
def load_avg_temp_por_sala():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM avg_temp_por_sala ORDER BY avg_temp DESC", engine)


@st.cache_data
def load_leituras_por_hora():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM leituras_por_hora ORDER BY hora ASC", engine)


@st.cache_data
def load_temp_max_min_por_dia():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM temp_max_min_por_dia ORDER BY dia ASC", engine)


def filter_by_period(df: pd.DataFrame, option: str, selected_day=None) -> pd.DataFrame:
    if df.empty:
        return df

    if option == "Ver tudo":
        return df

    max_date = df["noted_date"].max()

    if option == "Último mês":
        start_date = max_date - pd.Timedelta(days=30)
        return df[df["noted_date"] >= start_date].copy()

    if option == "Última semana":
        start_date = max_date - pd.Timedelta(days=7)
        return df[df["noted_date"] >= start_date].copy()

    if option == "Um dia":
        if selected_day is None:
            selected_day = max_date.date()
        return df[df["noted_date"].dt.date == selected_day].copy()

    return df


def make_month_options(df: pd.DataFrame):
    if df.empty:
        return []
    months = df["noted_date"].dt.to_period("M").drop_duplicates().sort_values()
    return [period.to_timestamp().date() for period in months]


def format_brazilian_date(value):
    return pd.to_datetime(value).strftime("%d-%m-%Y")


def compare_periods(df: pd.DataFrame, period_mode: str, selected_a, selected_b):
    if df.empty or selected_a is None or selected_b is None:
        return None

    selected_a_ts = pd.to_datetime(selected_a, errors="coerce")
    selected_b_ts = pd.to_datetime(selected_b, errors="coerce")

    if pd.isna(selected_a_ts) or pd.isna(selected_b_ts):
        return None

    if period_mode == "Comparar dois meses":
        start_a = selected_a_ts
        end_a = (selected_a_ts + pd.offsets.MonthEnd(1))
        start_b = selected_b_ts
        end_b = (selected_b_ts + pd.offsets.MonthEnd(1))

        period_a = df[(df["noted_date"] >= start_a) & (df["noted_date"] < end_a)].copy()
        period_b = df[(df["noted_date"] >= start_b) & (df["noted_date"] < end_b)].copy()

    elif period_mode == "Comparar duas semanas":
        start_a = selected_a_ts
        end_a = start_a + pd.Timedelta(days=7)
        start_b = selected_b_ts
        end_b = start_b + pd.Timedelta(days=7)

        period_a = df[(df["noted_date"] >= start_a) & (df["noted_date"] < end_a)].copy()
        period_b = df[(df["noted_date"] >= start_b) & (df["noted_date"] < end_b)].copy()

    else:
        period_a = df[df["noted_date"].dt.date == selected_a_ts.date()].copy()
        period_b = df[df["noted_date"].dt.date == selected_b_ts.date()].copy()

    if period_a.empty or period_b.empty:
        return None

    avg_a = period_a["temp"].mean()
    avg_b = period_b["temp"].mean()
    diff = avg_a - avg_b

    return {
        "avg_a": avg_a,
        "avg_b": avg_b,
        "diff": diff,
        "period_a_df": period_a,
        "period_b_df": period_b,
        "period_a_label": selected_a_ts.strftime("%d-%m-%Y") if period_mode in {"Comparar dois dias", "Comparar duas semanas"} else selected_a_ts.strftime("%b/%Y"),
        "period_b_label": selected_b_ts.strftime("%d-%m-%Y") if period_mode in {"Comparar dois dias", "Comparar duas semanas"} else selected_b_ts.strftime("%b/%Y"),
    }


def main() -> None:
    st.set_page_config(page_title="Dashboard de Temperaturas IoT", layout="wide")
    st.title("Dashboard de Temperaturas IoT")

    ensure_database_ready()
    ensure_views()

    temperature_df = load_temperature_table()
    if temperature_df.empty:
        st.warning("Nenhum dado encontrado no banco.")
        return

    min_date = temperature_df["noted_date"].min().date()
    max_date = temperature_df["noted_date"].max().date()

    st.sidebar.header("Filtros")
    period_option = st.sidebar.selectbox(
        "Selecione o período",
        ["Ver tudo", "Último mês", "Última semana", "Um dia"],
        index=0,
    )
    selected_day = None
    if period_option == "Um dia":
        selected_day = st.sidebar.date_input("Dia específico", value=max_date, min_value=min_date, max_value=max_date)

    filtered_df = filter_by_period(temperature_df, period_option, selected_day)

    if filtered_df.empty:
        st.warning("Nenhum dado disponível para o filtro selecionado.")
        return

    st.sidebar.markdown("---")
    st.sidebar.subheader("Comparar temperatura médias dos períodos")
    compare_enabled = st.sidebar.checkbox("Ativar comparação")

    comparison_result = None
    if compare_enabled:
        compare_mode = st.sidebar.selectbox(
            "Tipo de comparação",
            ["Comparar dois meses", "Comparar duas semanas", "Comparar dois dias"],
            index=0,
        )

        if compare_mode == "Comparar dois meses":
            month_options = make_month_options(temperature_df)
            if len(month_options) >= 2:
                month_a = st.sidebar.selectbox("Mês A", month_options, index=0)
                month_b = st.sidebar.selectbox("Mês B", month_options, index=len(month_options) - 1)
                comparison_result = compare_periods(temperature_df, compare_mode, month_a, month_b)
        elif compare_mode == "Comparar duas semanas":
            week_start_options = pd.date_range(start=min_date, end=max_date, freq="7D").date
            if len(week_start_options) >= 2:
                week_a = st.sidebar.selectbox("Início semana A", week_start_options, index=0)
                week_b = st.sidebar.selectbox("Início semana B", week_start_options, index=len(week_start_options) - 1)
                comparison_result = compare_periods(temperature_df, compare_mode, week_a, week_b)
        else:
            day_options = pd.date_range(start=min_date, end=max_date, freq="D").date
            if len(day_options) >= 2:
                day_a = st.sidebar.selectbox("Dia A", day_options, index=0)
                day_b = st.sidebar.selectbox("Dia B", day_options, index=len(day_options) - 1)
                comparison_result = compare_periods(temperature_df, compare_mode, day_a, day_b)

    if comparison_result:
        diff = comparison_result["diff"]
        if diff > 0:
            comparison_text = f"{comparison_result['period_a_label']} ficou {diff:.2f}°C mais quente que {comparison_result['period_b_label']}."
        elif diff < 0:
            comparison_text = f"{comparison_result['period_b_label']} ficou {abs(diff):.2f}°C mais quente que {comparison_result['period_a_label']}."
        else:
            comparison_text = f"As médias foram iguais em {comparison_result['period_a_label']} e {comparison_result['period_b_label']}"

        st.subheader("Comparação entre períodos")
        st.info(comparison_text)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"### {comparison_result['period_a_label']}")
            st.metric("Média do período A", f"{comparison_result['avg_a']:.2f}°C")
            a_daily = comparison_result["period_a_df"].assign(dia=comparison_result["period_a_df"]["noted_date"].dt.date).groupby("dia", as_index=False)["temp"].mean()
            if not a_daily.empty:
                a_daily["dia"] = a_daily["dia"].apply(format_brazilian_date)
                st.line_chart(a_daily.set_index("dia")["temp"].rename("Temperatura média"))
        with col_b:
            st.markdown(f"### {comparison_result['period_b_label']}")
            st.metric("Média do período B", f"{comparison_result['avg_b']:.2f}°C")
            b_daily = comparison_result["period_b_df"].assign(dia=comparison_result["period_b_df"]["noted_date"].dt.date).groupby("dia", as_index=False)["temp"].mean()
            if not b_daily.empty:
                b_daily["dia"] = b_daily["dia"].apply(format_brazilian_date)
                st.line_chart(b_daily.set_index("dia")["temp"].rename("Temperatura média"))

    if period_option == "Um dia":
        st.subheader(f"Resumo do dia {selected_day.strftime('%d-%m-%Y')}")
        col_min, col_max, col_avg = st.columns(3)
        with col_min:
            st.metric("Mínima do dia", f"{filtered_df['temp'].min():.2f}°C")
        with col_max:
            st.metric("Máxima do dia", f"{filtered_df['temp'].max():.2f}°C")
        with col_avg:
            st.metric("Média do dia", f"{filtered_df['temp'].mean():.2f}°C")

        st.subheader("Temperatura ao longo do dia")
        hourly = filtered_df.copy()
        hourly["hora"] = hourly["noted_date"].dt.strftime("%H:%M")
        hourly = hourly.groupby("hora", as_index=False)["temp"].mean()
        if not hourly.empty:
            st.line_chart(hourly.set_index("hora")["temp"].rename("Temperatura (°C)"))
        else:
            st.warning("Nenhuma leitura registrada para este dia.")

    temp_media_por_dia = filtered_df.assign(dia=filtered_df["noted_date"].dt.date).groupby("dia", as_index=False)["temp"].mean().rename(columns={"dia": "Dia", "temp": "Média da temperatura"})
    leituras_por_dia = filtered_df.assign(dia=filtered_df["noted_date"].dt.date).groupby("dia", as_index=False).size().rename(columns={"size": "Quantidade de leituras", "dia": "Dia"})

    st.subheader("Média de temperatura por dia")
    if not temp_media_por_dia.empty:
        temp_media_por_dia = temp_media_por_dia.sort_values("Dia").copy()
        temp_media_por_dia["Dia"] = temp_media_por_dia["Dia"].apply(format_brazilian_date)
        st.line_chart(temp_media_por_dia.set_index("Dia")["Média da temperatura"])
    else:
        st.warning("Nenhuma média de temperatura por dia disponível.")

    temp_max_min_por_dia = filtered_df.assign(dia=filtered_df["noted_date"].dt.date).groupby("dia", as_index=False).agg(
        temp_max=("temp", "max"),
        temp_min=("temp", "min"),
    ).rename(columns={"dia": "Dia"})

    st.subheader("Temperatura máxima e mínima por dia")
    if not temp_max_min_por_dia.empty:
        temp_max_min_por_dia = temp_max_min_por_dia.sort_values("Dia").copy()
        temp_max_min_por_dia["Dia"] = temp_max_min_por_dia["Dia"].apply(format_brazilian_date)
        st.line_chart(temp_max_min_por_dia.set_index("Dia")[["temp_max", "temp_min"]])
    else:
        st.warning("Nenhuma temperatura máxima e mínima por dia disponível.")

    st.subheader("Quantidades de leituras por dia")
    if not leituras_por_dia.empty:
        leituras_por_dia = leituras_por_dia.sort_values("Dia").copy()
        leituras_por_dia["Dia"] = leituras_por_dia["Dia"].apply(format_brazilian_date)
        st.bar_chart(leituras_por_dia.set_index("Dia")["Quantidade de leituras"])
    else:
        st.warning("Nenhuma quantidade de leituras por dia disponível.")


if __name__ == "__main__":
    main()
