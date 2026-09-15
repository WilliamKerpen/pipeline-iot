import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_engine() -> Engine:
    """Cria e retorna um engine SQLAlchemy para PostgreSQL."""
    user = os.getenv("DB_USER", "iot_user")
    password = os.getenv("DB_PASSWORD", "iot_password")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "iot_db")

    connection_url = (
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    )

    engine = create_engine(connection_url, pool_pre_ping=True)
    return engine
