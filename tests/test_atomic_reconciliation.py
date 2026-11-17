"""Verifica rollback de Silver quando a agregação Gold falha."""

import json
import os
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from aviation.database.connection import get_db_driver
from aviation.processing.reconcile import main as reconcile_main


def test_gold_failure_rolls_back_silver():
    if os.getenv("DB_NAME") != "aviation_data_intelligence_test":
        pytest.skip("Exclusivo do banco de testes")

    url = URL.create(
        get_db_driver(),
        username=os.environ["DB_USER"],
        password=os.getenv("DB_PASSWORD") or None,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
    )
    engine = create_engine(url, pool_pre_ping=True)
    bronze_id = None
    try:
        with engine.begin() as conn:
            bronze_id = conn.execute(
                text("""
                    INSERT INTO bronze.raw_aviation (source, payload)
                    VALUES ('atomic_rollback_test', CAST(:payload AS JSONB))
                    RETURNING id
                """),
                {"payload": json.dumps({
                    "time": 1794515682,
                    "states": [
                        ["fef123", "ROLLBACK", "Brazil", None, None,
                         -46.6, -23.5, 1000, False, 120],
                    ],
                })},
            ).scalar_one()

        # Força falha após a escrita na Silver e antes do commit.
        with patch(
            "aviation.processing.reconcile.get_gold_query",
            return_value=text("SELECT 1 / 0"),
        ):
            with pytest.raises(Exception):
                reconcile_main()

        with engine.connect() as conn:
            assert conn.execute(
                text("SELECT COUNT(*) FROM silver.aircraft_states WHERE bronze_id=:id"),
                {"id": bronze_id},
            ).scalar_one() == 0
            assert conn.execute(
                text("SELECT COUNT(*) FROM gold.air_traffic_summary WHERE bronze_id=:id"),
                {"id": bronze_id},
            ).scalar_one() == 0
    finally:
        if bronze_id is not None:
            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM bronze.raw_aviation WHERE id=:id"),
                    {"id": bronze_id},
                )
        engine.dispose()
