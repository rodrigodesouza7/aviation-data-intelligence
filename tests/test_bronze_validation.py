
"""Testes da validação de ingestão Bronze."""

from unittest.mock import patch

import pytest

from aviation.ingestion.save_bronze import save_bronze


@pytest.mark.parametrize(
    "timestamp",
    [
        None,
        0,
        -1,
        "1794434404",
        True,
        float("nan"),
        float("inf"),
        253402300800,
    ],
)
def test_rejects_invalid_timestamp(timestamp):
    """Rejeita timestamps inválidos antes de acessar o banco."""

    payload = {
        "time": timestamp,
        "states": [],
    }

    with (
        patch(
            "aviation.ingestion.save_bronze.get_aircraft_states",
            return_value=payload,
        ),
        patch(
            "aviation.ingestion.save_bronze.get_engine"
        ) as mocked_engine,
    ):
        with pytest.raises(
            ValueError,
            match="Timestamp invalido",
        ):
            save_bronze()

    mocked_engine.assert_not_called()
