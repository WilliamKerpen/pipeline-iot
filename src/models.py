"""Modelos SQLAlchemy que representam as tabelas do domínio."""

from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarativa compartilhada pelos modelos do banco."""


class TemperatureReading(Base):
    """Representa uma leitura de temperatura recebida de um sensor IoT."""

    __tablename__ = "temperature_readings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    room_id_id: Mapped[str] = mapped_column(String, nullable=False)
    noted_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temp: Mapped[float] = mapped_column(Float, nullable=False)
    out_in: Mapped[str] = mapped_column(String, nullable=False)
