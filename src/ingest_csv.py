"""Ponto de entrada compatível para executar a ingestão pelo terminal."""

from repositories.temperature_repository import create_schema
from services.temperature_service import ingest_csv


def create_table_if_not_exists() -> None:
    """Mantém compatibilidade com chamadas anteriores da aplicação."""
    create_schema()


if __name__ == "__main__":
    ingest_csv()
