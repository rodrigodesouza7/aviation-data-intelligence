
"""Agregação incremental da camada Silver para Gold."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver


def main():
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

    query = text("""
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
            bronze_id,
            observation_time,
            COUNT(*)::INTEGER,
            COUNT(*) FILTER (
                WHERE latitude IS NOT NULL
                  AND longitude IS NOT NULL
            )::INTEGER,
            COUNT(baro_altitude)::INTEGER,
            AVG(baro_altitude),
            AVG(velocity)
        FROM silver.aircraft_states
        GROUP BY bronze_id, observation_time
        ON CONFLICT (bronze_id) DO NOTHING
    """)

    try:
        with engine.begin() as connection:
            result = connection.execute(query)

            print(
                "Resumos inseridos na Gold: "
                f"{result.rowcount}"
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
