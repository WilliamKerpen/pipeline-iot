"""Consultas e comandos de persistência das leituras de temperatura."""

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db_connection import get_engine
from models import Base


def create_schema() -> None:
    """Cria as tabelas mapeadas caso ainda não existam."""
    Base.metadata.create_all(bind=get_engine())


def count_readings() -> int:
    """Retorna a quantidade atual de leituras persistidas."""
    with get_engine().connect() as connection:
        return connection.execute(text("SELECT COUNT(*) FROM temperature_readings")).scalar_one()


def get_existing_ids() -> set[str]:
    """Busca as chaves já gravadas para tornar a carga idempotente."""
    with get_engine().connect() as connection:
        readings = pd.read_sql("SELECT id FROM temperature_readings", con=connection)
    return set(readings["id"])


def append_readings(readings: pd.DataFrame) -> None:
    """Persiste um lote de leituras previamente validado."""
    if not readings.empty:
        readings.to_sql("temperature_readings", con=get_engine(), if_exists="append", index=False, chunksize=2000)


def get_all_readings() -> pd.DataFrame:
    """Retorna a série completa, ordenada para uso no dashboard."""
    readings = pd.read_sql(
        "SELECT id, room_id_id, noted_date, temp, out_in FROM temperature_readings ORDER BY noted_date ASC",
        get_engine(),
    )
    readings["noted_date"] = pd.to_datetime(readings["noted_date"])
    return readings


def create_analytical_views(sql_path: Path) -> None:
    """Executa o script que define as views analíticas do PostgreSQL."""
    statements = [statement.strip() for statement in sql_path.read_text(encoding="utf-8").split(";") if statement.strip()]
    with get_engine().begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
