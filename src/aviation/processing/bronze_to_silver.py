
"""Transformação incremental da camada Bronze para Silver."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver


def get_silver_query():
    """Insere novos estados e atualiza estados que realmente mudaram."""
    return text("""
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
            CASE
                WHEN jsonb_typeof(raw.payload->'states') = 'array'
                THEN raw.payload->'states'
                ELSE '[]'::jsonb
            END
        ) AS state
        WHERE state->>0 IS NOT NULL
          AND raw.payload->>'time' IS NOT NULL
          AND jsonb_typeof(raw.payload->'states') = 'array'
        ON CONFLICT (bronze_id, icao24) DO UPDATE SET
            callsign = EXCLUDED.callsign,
            origin_country = EXCLUDED.origin_country,
            longitude = EXCLUDED.longitude,
            latitude = EXCLUDED.latitude,
            baro_altitude = EXCLUDED.baro_altitude,
            velocity = EXCLUDED.velocity,
            observation_time = EXCLUDED.observation_time
        WHERE (
            silver.aircraft_states.callsign,
            silver.aircraft_states.origin_country,
            silver.aircraft_states.longitude,
            silver.aircraft_states.latitude,
            silver.aircraft_states.baro_altitude,
            silver.aircraft_states.velocity,
            silver.aircraft_states.observation_time
        ) IS DISTINCT FROM (
            EXCLUDED.callsign,
            EXCLUDED.origin_country,
            EXCLUDED.longitude,
            EXCLUDED.latitude,
            EXCLUDED.baro_altitude,
            EXCLUDED.velocity,
            EXCLUDED.observation_time
        )
    """)


def get_stale_silver_cleanup_query():
    """Remove estados Silver ausentes dos respectivos snapshots Bronze."""
    return text("""
        DELETE FROM silver.aircraft_states AS existing
        USING bronze.raw_aviation AS raw
        WHERE existing.bronze_id = raw.id
          AND jsonb_typeof(raw.payload->'states') = 'array'
          AND raw.payload->>'time' IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM jsonb_array_elements(
                  CASE
                      WHEN jsonb_typeof(raw.payload->'states') = 'array'
                      THEN raw.payload->'states'
                      ELSE '[]'::jsonb
                  END
              ) AS state
              WHERE state->>0 = existing.icao24
          )
    """)


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

    cleanup_query = get_stale_silver_cleanup_query()
    upsert_query = get_silver_query()

    try:
        with engine.begin() as connection:
            removed = connection.execute(cleanup_query)
            result = connection.execute(upsert_query)

            print(
                f"Registros inseridos ou atualizados na Silver: {result.rowcount}; "
                f"registros obsoletos removidos: {removed.rowcount}"
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
