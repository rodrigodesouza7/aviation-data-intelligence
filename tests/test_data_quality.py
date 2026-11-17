"""Valida o cálculo de qualidade com dados sintéticos no PostgreSQL de testes."""

import json
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver
from aviation.quality import get_quality_query


def test_quality_metrics_for_synthetic_snapshot():
    assert os.environ["DB_NAME"] == "aviation_data_intelligence_test"
    url = URL.create(
        get_db_driver(),
        username=os.environ["DB_USER"],
        password=os.getenv("DB_PASSWORD") or None,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
    )
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                payload = {
                    "time": 1794515682,
                    "states": [
                        ["abc123", "A", "Brazil", None, None, -46.6, -23.5, 1000, False, 100],
                        [None, "B", "Brazil", None, None, None, None, None, False, None],
                        ["def456", "C", "Brazil", None, None, -200.0, -23.5, 1000, False, 100],
                    ],
                }
                bronze_id = conn.execute(
                    text("""
                        INSERT INTO bronze.raw_aviation(source, payload)
                        VALUES ('quality_test', CAST(:payload AS JSONB))
                        RETURNING id
                    """),
                    {"payload": json.dumps(payload)},
                ).scalar_one()
                conn.execute(
                    text("""
                        INSERT INTO silver.aircraft_states(
                            bronze_id, icao24, observation_time
                        ) VALUES (:id, 'abc123', NOW()), (:id, 'def456', NOW())
                    """),
                    {"id": bronze_id},
                )
                row = next(
                    r for r in conn.execute(get_quality_query()).mappings()
                    if r["bronze_id"] == bronze_id
                )
                assert row["received_count"] == 3
                assert row["accepted_count"] == 2
                assert row["not_loaded_count"] == 1
                assert row["missing_position_count"] == 1
                assert row["invalid_position_count"] == 1
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
