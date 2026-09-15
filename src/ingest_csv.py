from pathlib import Path

import pandas as pd
from sqlalchemy import Float, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from db_connection import get_engine


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "temperature_readings.csv"


class Base(DeclarativeBase):
    pass


class TemperatureReading(Base):
    __tablename__ = "temperature_readings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    room_id_id: Mapped[str] = mapped_column(String, nullable=False)
    noted_date: Mapped[pd.Timestamp] = mapped_column(DateTime, nullable=False)
    temp: Mapped[float] = mapped_column(Float, nullable=False)
    out_in: Mapped[str] = mapped_column(String, nullable=False)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [
        str(column).strip().lower().replace("*", "").replace("/", "_").replace(" ", "_")
        for column in normalized.columns
    ]
    return normalized


def load_temperature_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df = normalize_columns(df)

    df["room_id_id"] = df["room_id_id"].astype(str).str.strip()
    df["noted_date"] = pd.to_datetime(
        df["noted_date"], format="%d-%m-%Y %H:%M", errors="coerce"
    )
    df["temp"] = pd.to_numeric(
        df["temp"].astype(str).str.replace("*", "", regex=False),
        errors="coerce",
    )
    df["out_in"] = (
        df["out_in"].astype(str).str.replace("*", "", regex=False).str.strip()
    )

    df = df.dropna(subset=["id", "room_id_id", "noted_date", "temp", "out_in"]).copy()
    df = df[["id", "room_id_id", "noted_date", "temp", "out_in"]].drop_duplicates(subset=["id"], keep="first")
    return df


def create_table_if_not_exists() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def ingest_csv() -> None:
    engine = get_engine()
    dataframe = load_temperature_data()

    create_table_if_not_exists()

    with engine.connect() as connection:
        try:
            existing_ids = pd.read_sql(
                "SELECT id FROM temperature_readings",
                con=connection,
            )["id"].tolist()
        except Exception:
            existing_ids = []

    new_rows = dataframe[~dataframe["id"].isin(existing_ids)].copy()

    if not new_rows.empty:
        new_rows.to_sql(
            "temperature_readings",
            con=engine,
            if_exists="append",
            index=False,
            chunksize=2000,
        )

    print(
        f"Dados processados: {len(dataframe)} | novos: {len(new_rows)} | já existentes: {len(dataframe) - len(new_rows)}"
    )


if __name__ == "__main__":
    ingest_csv()
