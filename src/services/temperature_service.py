"""Casos de uso para carregar e consultar temperaturas IoT."""

from pathlib import Path

import pandas as pd

from repositories import temperature_repository

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CSV_PATH = BASE_DIR / "data" / "temperature_readings.csv"
VIEWS_PATH = BASE_DIR / "src" / "create_views.sql"
REQUIRED_COLUMNS = {"id", "room_id_id", "noted_date", "temp", "out_in"}


def normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Converte os nomes originais do CSV para o padrão interno."""
    normalized = dataframe.copy()
    normalized.columns = [str(column).strip().lower().replace("*", "").replace("/", "_").replace(" ", "_") for column in normalized.columns]
    return normalized


def load_temperature_data() -> pd.DataFrame:
    """Lê, valida, limpa e remove duplicidades do arquivo de entrada."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {CSV_PATH}")

    dataframe = normalize_columns(pd.read_csv(CSV_PATH))
    missing_columns = REQUIRED_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(f"O CSV não possui as colunas obrigatórias: {', '.join(sorted(missing_columns))}")

    dataframe["room_id_id"] = dataframe["room_id_id"].astype(str).str.strip()
    dataframe["noted_date"] = pd.to_datetime(dataframe["noted_date"], format="%d-%m-%Y %H:%M", errors="coerce")
    dataframe["temp"] = pd.to_numeric(dataframe["temp"].astype(str).str.replace("*", "", regex=False), errors="coerce")
    dataframe["out_in"] = dataframe["out_in"].astype(str).str.replace("*", "", regex=False).str.strip()

    # A chave id identifica uma leitura e impede que o mesmo evento seja gravado duas vezes.
    dataframe = dataframe.dropna(subset=REQUIRED_COLUMNS).copy()
    return dataframe[list(REQUIRED_COLUMNS)].drop_duplicates(subset=["id"], keep="first")


def ingest_csv() -> dict[str, int]:
    """Carrega o CSV no banco sem repetir leituras já persistidas."""
    temperature_repository.create_schema()
    dataframe = load_temperature_data()
    existing_ids = temperature_repository.get_existing_ids()
    new_rows = dataframe[~dataframe["id"].isin(existing_ids)].copy()
    temperature_repository.append_readings(new_rows)
    result = {"processed": len(dataframe), "inserted": len(new_rows), "existing": len(dataframe) - len(new_rows)}
    print("Dados processados: {processed} | novos: {inserted} | já existentes: {existing}".format(**result))
    return result


def initialize_database() -> dict[str, int] | None:
    """Prepara tabelas e views; carrega o CSV apenas no primeiro uso."""
    temperature_repository.create_schema()
    ingestion_result = ingest_csv() if temperature_repository.count_readings() == 0 else None
    temperature_repository.create_analytical_views(VIEWS_PATH)
    return ingestion_result


def get_temperature_readings() -> pd.DataFrame:
    """Entrega ao dashboard os dados prontos para filtros e gráficos."""
    return temperature_repository.get_all_readings()


def filter_by_period(dataframe: pd.DataFrame, option: str, selected_day=None) -> pd.DataFrame:
    """Aplica à série o período escolhido pelo usuário."""
    if dataframe.empty or option == "Ver tudo":
        return dataframe

    max_date = dataframe["noted_date"].max()
    if option == "Último mês":
        return dataframe[dataframe["noted_date"] >= max_date - pd.Timedelta(days=30)].copy()
    if option == "Última semana":
        return dataframe[dataframe["noted_date"] >= max_date - pd.Timedelta(days=7)].copy()
    if option == "Um dia":
        selected_day = selected_day or max_date.date()
        return dataframe[dataframe["noted_date"].dt.date == selected_day].copy()
    return dataframe


def make_month_options(dataframe: pd.DataFrame) -> list:
    """Gera os meses disponíveis em ordem cronológica."""
    if dataframe.empty:
        return []
    months = dataframe["noted_date"].dt.to_period("M").drop_duplicates().sort_values()
    return [period.to_timestamp().date() for period in months]


def compare_periods(dataframe: pd.DataFrame, period_mode: str, selected_a, selected_b):
    """Compara médias e devolve as séries de dois períodos selecionados."""
    if dataframe.empty or selected_a is None or selected_b is None:
        return None

    selected_a_ts = pd.to_datetime(selected_a, errors="coerce")
    selected_b_ts = pd.to_datetime(selected_b, errors="coerce")
    if pd.isna(selected_a_ts) or pd.isna(selected_b_ts):
        return None

    if period_mode == "Comparar dois meses":
        end_a = selected_a_ts + pd.offsets.MonthBegin(1)
        end_b = selected_b_ts + pd.offsets.MonthBegin(1)
        period_a = dataframe[(dataframe["noted_date"] >= selected_a_ts) & (dataframe["noted_date"] < end_a)].copy()
        period_b = dataframe[(dataframe["noted_date"] >= selected_b_ts) & (dataframe["noted_date"] < end_b)].copy()
    elif period_mode == "Comparar duas semanas":
        period_a = dataframe[(dataframe["noted_date"] >= selected_a_ts) & (dataframe["noted_date"] < selected_a_ts + pd.Timedelta(days=7))].copy()
        period_b = dataframe[(dataframe["noted_date"] >= selected_b_ts) & (dataframe["noted_date"] < selected_b_ts + pd.Timedelta(days=7))].copy()
    else:
        period_a = dataframe[dataframe["noted_date"].dt.date == selected_a_ts.date()].copy()
        period_b = dataframe[dataframe["noted_date"].dt.date == selected_b_ts.date()].copy()

    if period_a.empty or period_b.empty:
        return None

    is_daily_or_weekly = period_mode in {"Comparar dois dias", "Comparar duas semanas"}
    date_format = "%d-%m-%Y" if is_daily_or_weekly else "%b/%Y"
    return {
        "avg_a": period_a["temp"].mean(),
        "avg_b": period_b["temp"].mean(),
        "diff": period_a["temp"].mean() - period_b["temp"].mean(),
        "period_a_df": period_a,
        "period_b_df": period_b,
        "period_a_label": selected_a_ts.strftime(date_format),
        "period_b_label": selected_b_ts.strftime(date_format),
    }
