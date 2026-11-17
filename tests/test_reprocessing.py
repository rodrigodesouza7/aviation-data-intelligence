"""Teste de integração do reprocessamento Bronze -> Silver -> Gold."""

import json
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver
from aviation.processing.bronze_to_silver import (
    get_silver_query,
    get_stale_silver_cleanup_query,
)
from aviation.processing.silver_to_gold import get_gold_query


def test_reprocessing_reconciles_changed_and_removed_aircraft():
    if os.getenv("DB_NAME") != "aviation_data_intelligence_test":
        pytest.skip("Teste de integração exclusivo do banco de testes")

    url = URL.create(
        drivername=get_db_driver(),
        username=os.environ["DB_USER"],
        password=os.getenv("DB_PASSWORD") or None,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
    )
    engine = create_engine(url, pool_pre_ping=True)

    def state(icao24, altitude):
        return [
            icao24, "TEST", "Brazil", None, None,
            -46.6, -23.5, altitude, False, 150.0,
        ]

    def reconcile(conn):
        conn.execute(get_stale_silver_cleanup_query())
        conn.execute(get_silver_query())
        conn.execute(get_gold_query())

    try:
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                bronze_id = conn.execute(
                    text("""
                        INSERT INTO bronze.raw_aviation (source, payload)
                        VALUES ('reprocess_test', CAST(:payload AS JSONB))
                        RETURNING id
                    """),
                    {"payload": json.dumps({
                        "time": 1794515682,
                        "states": [state("abc123", 1000), state("def456", 2000)],
                    })},
                ).scalar_one()

                reconcile(conn)

                assert conn.execute(
                    text("""
                        SELECT total_aircraft
                        FROM gold.air_traffic_summary
                        WHERE bronze_id = :id
                    """),
                    {"id": bronze_id},
                ).scalar_one() == 2

                # O Bronze corrigido remove uma aeronave e altera a altitude.
                conn.execute(
                    text("""
                        UPDATE bronze.raw_aviation
                        SET payload = CAST(:payload AS JSONB)
                        WHERE id = :id
                    """),
                    {
                        "id": bronze_id,
                        "payload": json.dumps({
                            "time": 1794515683,
                            "states": [state("abc123", 3000)],
                        }),
                    },
                )

                reconcile(conn)

                rows = conn.execute(
                    text("""
                        SELECT icao24, baro_altitude
                        FROM silver.aircraft_states
                        WHERE bronze_id = :id
                    """),
                    {"id": bronze_id},
                ).all()
                assert rows == [("abc123", 3000.0)]

                summary = conn.execute(
                    text("""
                        SELECT total_aircraft, avg_altitude_m,
                               observation_time
                        FROM gold.air_traffic_summary
                        WHERE bronze_id = :id
                    """),
                    {"id": bronze_id},
                ).one()
                assert summary.total_aircraft == 1
                assert summary.avg_altitude_m == 3000.0
                assert int(summary.observation_time.timestamp()) == 1794515683

                # Reexecutar sem mudanças não causa escrita adicional.
                assert conn.execute(get_stale_silver_cleanup_query()).rowcount == 0
                assert conn.execute(get_silver_query()).rowcount == 0
                assert conn.execute(get_gold_query()).rowcount == 0

                # Um snapshot corrigido para vazio remove os últimos estados.
                conn.execute(
                    text("""
                        UPDATE bronze.raw_aviation
                        SET payload = CAST(:payload AS JSONB)
                        WHERE id = :id
                    """),
                    {
                        "id": bronze_id,
                        "payload": json.dumps({
                            "time": 1794515684,
                            "states": [],
                        }),
                    },
                )
                reconcile(conn)
                assert conn.execute(
                    text("""
                        SELECT COUNT(*) FROM silver.aircraft_states
                        WHERE bronze_id = :id
                    """),
                    {"id": bronze_id},
                ).scalar_one() == 0
                assert conn.execute(
                    text("""
                        SELECT total_aircraft FROM gold.air_traffic_summary
                        WHERE bronze_id = :id
                    """),
                    {"id": bronze_id},
                ).scalar_one() == 0
                # Snapshot válido novamente para verificar entradas incompletas.
                conn.execute(
                    text("""
                        UPDATE bronze.raw_aviation
                        SET payload = CAST(:payload AS JSONB)
                        WHERE id = :id
                    """),
                    {
                        "id": bronze_id,
                        "payload": json.dumps({
                            "time": 1794515685,
                            "states": [state("abc123", 1000)],
                        }),
                    },
                )
                reconcile(conn)

                # A ausência do array não pode apagar estados já processados.
                for invalid_payload in (
                    {"time": 1794515686},
                    {"time": 1794515686, "states": None},
                    {"time": 1794515686, "states": {}},
                ):
                    conn.execute(
                        text("""
                            UPDATE bronze.raw_aviation
                            SET payload = CAST(:payload AS JSONB)
                            WHERE id = :id
                        """),
                        {"id": bronze_id, "payload": json.dumps(invalid_payload)},
                    )
                    assert conn.execute(
                        get_stale_silver_cleanup_query()
                    ).rowcount == 0
                    assert conn.execute(get_silver_query()).rowcount == 0
                    assert conn.execute(
                        text("""
                            SELECT COUNT(*) FROM silver.aircraft_states
                            WHERE bronze_id = :id
                        """),
                        {"id": bronze_id},
                    ).scalar_one() == 1
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
