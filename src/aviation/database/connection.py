
"""Configuração e verificação da conexão com PostgreSQL."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")


def get_db_driver():
    """Retorna o driver PostgreSQL configurado para o ambiente."""
    driver = os.getenv("DB_DRIVER", "postgresql+psycopg")

    allowed = {
        "postgresql+psycopg",
        "postgresql+psycopg2",
    }

    if driver not in allowed:
        raise ValueError(
            f"Driver PostgreSQL não suportado: {driver}"
        )

    return driver


def get_engine():
    """Cria o mecanismo de conexão com PostgreSQL."""

    url = URL.create(
        drivername=get_db_driver(),
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD") or None,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(url, pool_pre_ping=True)


def test_connection():
    """Verifica a conexão e o banco selecionado."""

    engine = get_engine()

    try:
        with engine.connect() as connection:
            database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            print(f"Conexão estabelecida: {database}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    test_connection()
