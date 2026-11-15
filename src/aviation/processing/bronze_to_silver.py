
"""Transformação incremental da camada Bronze para Silver."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver


def main():
    """Transforma registros da camada Bronze para Silver."""

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
        INSERT INTO silver.aircraft_states (
            bronze_id,
            icao24,
            callsign,
            origin_country,
            longitude,
            latitude,
            baro_altitude,
            velocity,
            observation_time
        )
        SELECT
            raw.id,
            state->>0,
            NULLIF(TRIM(state->>1), ''),
            state->>2,
            (state->>5)::DOUBLE PRECISION,
            (state->>6)::DOUBLE PRECISION,
            (state->>7)::DOUBLE PRECISION,
            (state->>9)::DOUBLE PRECISION,
            TO_TIMESTAMP((raw.payload->>'time')::DOUBLE PRECISION)
        FROM bronze.raw_aviation AS raw
        CROSS JOIN LATERAL jsonb_array_elements(
            raw.payload->'states'
        ) AS state
        WHERE state->>0 IS NOT NULL
          AND raw.payload->>'time' IS NOT NULL
        ON CONFLICT (bronze_id, icao24) DO NOTHING
    """)

    try:
        with engine.begin() as connection:
            result = connection.execute(query)

            print(
                f"Registros inseridos na Silver: {result.rowcount}"
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
