"""Reconciliação atômica das camadas Silver e Gold em uma transação."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver
from aviation.processing.bronze_to_silver import (
    get_silver_query,
    get_stale_silver_cleanup_query,
)
from aviation.processing.silver_to_gold import get_gold_query


def reconcile_layers(connection):
    """Executa as três consultas na mesma conexão e transação."""
    removed = connection.execute(get_stale_silver_cleanup_query())
    silver = connection.execute(get_silver_query())
    gold = connection.execute(get_gold_query())
    return removed.rowcount, silver.rowcount, gold.rowcount


def main():
    """Faz commit conjunto; qualquer falha reverte Silver e Gold."""
    load_dotenv()
    url = URL.create(
        drivername=get_db_driver(),
        username=os.environ["DB_USER"],
        password=os.getenv("DB_PASSWORD") or None,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
    )
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            removed, silver, gold = reconcile_layers(connection)
        print(
            f"Silver: {silver} inseridos/atualizados, {removed} removidos; "
            f"Gold: {gold} resumos inseridos/atualizados"
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
