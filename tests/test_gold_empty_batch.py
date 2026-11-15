
"""Teste de integração da Gold para lotes Bronze vazios."""

import json
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver
from aviation.processing.silver_to_gold import get_gold_query


def test_gold_empty_batch():
    load_dotenv(dotenv_path=".env")

    test_database = "aviation_data_intelligence_test"

    url = URL.create(
        drivername=get_db_driver(),
        username=os.environ["DB_USER"],
        password=os.getenv("DB_PASSWORD") or None,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=test_database,
    )

    engine = create_engine(url, pool_pre_ping=True)

    try:
        with engine.connect() as connection:
            try:
                database = connection.execute(
                    text("SELECT current_database()")
                ).scalar_one()

                assert database == test_database

                bronze_id = connection.execute(
                    text("""
                        INSERT INTO bronze.raw_aviation (
                            source, payload
                        )
                        VALUES (
                            :source,
                            CAST(:payload AS JSONB)
                        )
                        RETURNING id
                    """),
                    {
                        "source": "test_empty_batch",
                        "payload": json.dumps({
                            "time": 1794515682,
                            "states": [],
                        }),
                    },
                ).scalar_one()

                # Executa a consulta real da camada Gold.
                connection.execute(get_gold_query())

                summary = connection.execute(
                    text("""
                        SELECT
                            bronze_id,
                            total_aircraft,
                            aircraft_with_position,
                            aircraft_with_altitude,
                            avg_altitude_m,
                            avg_velocity_ms,
                            observation_time
                        FROM gold.air_traffic_summary
                        WHERE bronze_id = :bronze_id
                    """),
                    {"bronze_id": bronze_id},
                ).mappings().one()

                assert summary["bronze_id"] == bronze_id
                assert summary["total_aircraft"] == 0
                assert summary["aircraft_with_position"] == 0
                assert summary["aircraft_with_altitude"] == 0
                assert summary["avg_altitude_m"] is None
                assert summary["avg_velocity_ms"] is None
                assert summary["observation_time"] is not None

                # Segunda execução: não deve duplicar o resumo.
                connection.execute(get_gold_query())

                total = connection.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM gold.air_traffic_summary
                        WHERE bronze_id = :bronze_id
                    """),
                    {"bronze_id": bronze_id},
                ).scalar_one()

                assert total == 1

            finally:
                connection.rollback()

    finally:
        engine.dispose()
