"""Fixtures compartilhadas pelos testes de integra\u00e7\u00e3o."""

import pytest
from sqlalchemy import text

from db_connection import get_engine
from repositories import temperature_repository


@pytest.fixture
def clean_database():
    """Garante isolamento entre testes que usam o PostgreSQL configurado."""
    get_engine.cache_clear()
    temperature_repository.create_schema()
    with get_engine().begin() as connection:
        connection.execute(text("TRUNCATE TABLE temperature_readings"))
    yield
    with get_engine().begin() as connection:
        connection.execute(text("TRUNCATE TABLE temperature_readings"))
