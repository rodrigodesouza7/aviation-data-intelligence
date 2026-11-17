"""Indicadores de qualidade por snapshot, sem modificar dados de origem."""

from sqlalchemy import text


def get_quality_query():
    """Compara estados recebidos na Bronze com registros persistidos na Silver."""
    return text("""
        WITH received AS (
            SELECT
                b.id AS bronze_id,
                COUNT(state.item) AS received_count,
                COUNT(*) FILTER (
                    WHERE state.item IS NOT NULL
                      AND (
                          NULLIF(BTRIM(state.item->>5), '') IS NULL
                          OR NULLIF(BTRIM(state.item->>6), '') IS NULL
                      )
                ) AS missing_position_count,
                COUNT(*) FILTER (
                    WHERE state.item IS NOT NULL
                      AND (
                          CASE
                              WHEN (state.item->>5) ~ '^-?[0-9]+(\\.[0-9]+)?$'
                              THEN (state.item->>5)::DOUBLE PRECISION NOT BETWEEN -180 AND 180
                              ELSE FALSE
                          END
                          OR
                          CASE
                              WHEN (state.item->>6) ~ '^-?[0-9]+(\\.[0-9]+)?$'
                              THEN (state.item->>6)::DOUBLE PRECISION NOT BETWEEN -90 AND 90
                              ELSE FALSE
                          END
                      )
                ) AS invalid_position_count
            FROM bronze.raw_aviation AS b
            LEFT JOIN LATERAL jsonb_array_elements(
                CASE
                    WHEN jsonb_typeof(b.payload->'states') = 'array'
                    THEN b.payload->'states'
                    ELSE '[]'::jsonb
                END
            ) AS state(item) ON TRUE
            GROUP BY b.id
        ),
        processed AS (
            SELECT bronze_id, COUNT(*) AS accepted_count
            FROM silver.aircraft_states
            GROUP BY bronze_id
        )
        SELECT
            r.bronze_id,
            r.received_count,
            COALESCE(p.accepted_count, 0) AS accepted_count,
            GREATEST(r.received_count - COALESCE(p.accepted_count, 0), 0)
                AS not_loaded_count,
            r.missing_position_count,
            r.invalid_position_count
        FROM received AS r
        LEFT JOIN processed AS p ON p.bronze_id = r.bronze_id
        ORDER BY r.bronze_id
    """)
