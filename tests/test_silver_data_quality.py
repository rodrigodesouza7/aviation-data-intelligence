
"""Testes de qualidade dos dados da camada Silver."""

import pytest
from sqlalchemy import text

from test_gold_integrity import connection


def test_no_duplicate_aircraft_per_batch(connection):
    query = text("""
        SELECT COUNT(*)
        FROM (
            SELECT bronze_id, icao24
            FROM silver.aircraft_states
            GROUP BY bronze_id, icao24
            HAVING COUNT(*) > 1
        ) AS duplicates
    """)

    duplicates = connection.execute(query).scalar_one()

    assert duplicates == 0


def test_all_silver_records_have_bronze_source(connection):
    query = text("""
        SELECT COUNT(*)
        FROM silver.aircraft_states AS s
        LEFT JOIN bronze.raw_aviation AS b
            ON b.id = s.bronze_id
        WHERE b.id IS NULL
    """)

    missing = connection.execute(query).scalar_one()

    assert missing == 0


def test_coordinates_within_valid_ranges(connection):
    query = text("""
        SELECT COUNT(*)
        FROM silver.aircraft_states
        WHERE
            (latitude IS NOT NULL
                AND (latitude < -90 OR latitude > 90))
            OR
            (longitude IS NOT NULL
                AND (longitude < -180 OR longitude > 180))
    """)

    invalid = connection.execute(query).scalar_one()

    assert invalid == 0
