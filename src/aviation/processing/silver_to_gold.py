
"""Agregação incremental da camada Silver para Gold."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver


def get_gold_query():
    """Retorna a consulta SQL de agregação da camada Gold."""
    return text("""
        INSERT INTO gold.air_traffic_summary (
            bronze_id,
            observation_time,
            total_aircraft,
            aircraft_with_position,
            aircraft_with_altitude,
            avg_altitude_m,
            avg_velocity_ms
        )
        SELECT
            b.id,
            TO_TIMESTAMP(
                (b.payload->>'time')::DOUBLE PRECISION
            ),
            COUNT(s.id)::INTEGER,
            COUNT(s.id) FILTER (
                WHERE s.latitude IS NOT NULL
                  AND s.longitude IS NOT NULL
            )::INTEGER,
            COUNT(s.baro_altitude)::INTEGER,
            AVG(s.baro_altitude),
            AVG(s.velocity)
        FROM bronze.raw_aviation AS b
        LEFT JOIN silver.aircraft_states AS s
            ON s.bronze_id = b.id
        GROUP BY b.id
        ON CONFLICT (bronze_id) DO UPDATE SET
            observation_time = EXCLUDED.observation_time,
            total_aircraft = EXCLUDED.total_aircraft,
            aircraft_with_position = EXCLUDED.aircraft_with_position,
            aircraft_with_altitude = EXCLUDED.aircraft_with_altitude,
            avg_altitude_m = EXCLUDED.avg_altitude_m,
            avg_velocity_ms = EXCLUDED.avg_velocity_ms
        WHERE (
            gold.air_traffic_summary.observation_time,
            gold.air_traffic_summary.total_aircraft,
            gold.air_traffic_summary.aircraft_with_position,
            gold.air_traffic_summary.aircraft_with_altitude,
            gold.air_traffic_summary.avg_altitude_m,
            gold.air_traffic_summary.avg_velocity_ms
        ) IS DISTINCT FROM (
            EXCLUDED.observation_time,
            EXCLUDED.total_aircraft,
            EXCLUDED.aircraft_with_position,
            EXCLUDED.aircraft_with_altitude,
            EXCLUDED.avg_altitude_m,
            EXCLUDED.avg_velocity_ms
        )
    """)


def main():
    """Executa a agregação incremental da camada Gold."""
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

    query = get_gold_query()

    try:
        with engine.begin() as connection:
            result = connection.execute(query)

            print(
                "Resumos inseridos ou atualizados na Gold: "
                f"{result.rowcount}"
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
