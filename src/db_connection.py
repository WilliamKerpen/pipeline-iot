import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Cria um único engine SQLAlchemy reutilizável para o PostgreSQL."""
    # As variáveis de ambiente permitem usar Docker e execução local sem alterar o código.
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
