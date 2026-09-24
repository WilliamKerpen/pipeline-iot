"""Testes com PostgreSQL real para garantir a carga e o acesso do dashboard."""

from sqlalchemy import text
from streamlit.testing.v1 import AppTest

from dashboard import load_temperature_table
from db_connection import get_engine
from services.temperature_service import ingest_csv


def test_ingestion_persists_data_and_prints_last_database_row(clean_database):
    result = ingest_csv()

    with get_engine().connect() as connection:
        last_reading = connection.execute(
            text(
                "SELECT id, room_id_id, noted_date, temp, out_in "
                "FROM temperature_readings ORDER BY noted_date DESC, id DESC LIMIT 1"
            )
        ).mappings().one()

    print(f"\nUltima leitura persistida no banco: {dict(last_reading)}")
    assert result["inserted"] > 0
    assert last_reading["id"]


def test_dashboard_data_loader_reads_from_postgresql(clean_database):
    ingest_csv()
    load_temperature_table.clear()

    readings = load_temperature_table()

    assert not readings.empty
    assert {"id", "room_id_id", "noted_date", "temp", "out_in"}.issubset(readings.columns)


def test_streamlit_dashboard_renders_with_database_data(clean_database):
    """Executa a interface real e confirma que ela n\u00e3o gera exce\u00e7\u00e3o ao consultar o banco."""
    ingest_csv()
    load_temperature_table.clear()

    app = AppTest.from_file("src/dashboard.py")
    app.run(timeout=15)

    assert not app.exception
    assert app.title[0].value == "Dashboard de Temperaturas IoT"
