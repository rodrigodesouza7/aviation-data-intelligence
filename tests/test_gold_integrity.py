
"""Testes de integridade da camada Gold."""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


@pytest.fixture(scope="module")
def connection():
    load_dotenv()

    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.getenv("DB_PASSWORD") or None,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
    )

    engine = create_engine(url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            yield conn
    finally:
        engine.dispose()


def test_gold_matches_silver(connection):
    """Valida os totais de aeronaves entre Silver e Gold."""
    query = text("""
        SELECT
            g.bronze_id,
            g.total_aircraft,
            g.aircraft_with_position,
            g.aircraft_with_altitude,
            s.total_aircraft AS silver_total,
            s.aircraft_with_position AS silver_position,
            s.aircraft_with_altitude AS silver_altitude
        FROM gold.air_traffic_summary AS g
        JOIN (
            SELECT
                bronze_id,
                COUNT(*) AS total_aircraft,
                COUNT(*) FILTER (
                    WHERE latitude IS NOT NULL
                      AND longitude IS NOT NULL
                ) AS aircraft_with_position,
                COUNT(baro_altitude) AS aircraft_with_altitude
            FROM silver.aircraft_states
            GROUP BY bronze_id
        ) AS s
            ON s.bronze_id = g.bronze_id
    """)

    rows = connection.execute(query).mappings().all()

    assert rows, "Nenhum resumo Gold encontrado."

    for row in rows:
        assert row["total_aircraft"] == row["silver_total"]
        assert (
            row["aircraft_with_position"]
            == row["silver_position"]
        )
        assert (
            row["aircraft_with_altitude"]
            == row["silver_altitude"]
        )


def test_gold_has_no_missing_silver_batches(connection):
    """Verifica se todos os lotes Silver possuem resumo Gold."""
    query = text("""
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT bronze_id
            FROM silver.aircraft_states
        ) AS s
        LEFT JOIN gold.air_traffic_summary AS g
            ON g.bronze_id = s.bronze_id
        WHERE g.bronze_id IS NULL
    """)

    missing = connection.execute(query).scalar_one()

    assert missing == 0, (
        f"Existem {missing} lotes Silver sem resumo Gold."
    )


def test_gold_averages_match_silver(connection):
    """Valida as médias de altitude e velocidade na Gold."""
    query = text("""
        SELECT
            g.bronze_id,
            g.avg_altitude_m,
            g.avg_velocity_ms,
            AVG(s.baro_altitude) AS expected_altitude,
            AVG(s.velocity) AS expected_velocity
        FROM gold.air_traffic_summary AS g
        JOIN silver.aircraft_states AS s
            ON s.bronze_id = g.bronze_id
        GROUP BY
            g.bronze_id,
            g.avg_altitude_m,
            g.avg_velocity_ms
    """)

    rows = connection.execute(query).mappings().all()

    assert rows, "Nenhum resumo Gold encontrado."

    for row in rows:
        if row["expected_altitude"] is None:
            assert row["avg_altitude_m"] is None
        else:
            assert row["avg_altitude_m"] == pytest.approx(
                row["expected_altitude"]
            )

        if row["expected_velocity"] is None:
            assert row["avg_velocity_ms"] is None
        else:
            assert row["avg_velocity_ms"] == pytest.approx(
                row["expected_velocity"]
            )


def test_all_bronze_batches_have_gold_summary(connection):
    """Verifica se todos os lotes Bronze possuem resumo Gold."""
    query = text("""
        SELECT b.id
        FROM bronze.raw_aviation AS b
        LEFT JOIN gold.air_traffic_summary AS g
            ON g.bronze_id = b.id
        WHERE g.bronze_id IS NULL
        ORDER BY b.id
    """)

    missing_batches = connection.execute(query).scalars().all()

    assert not missing_batches, (
        f"Lotes Bronze sem resumo Gold: {missing_batches}"
    )


