
import json

from sqlalchemy import text

from aviation.database.connection import get_engine
from aviation.ingestion.opensky_client import get_aircraft_states


def save_bronze():
    """Consulta a OpenSky e armazena o JSON bruto."""

    data = get_aircraft_states()

    states = data.get("states")

    if not isinstance(states, list):
        raise ValueError(
            "Resposta sem lista valida de aeronaves."
        )

    timestamp = data.get("time")

    if (
        isinstance(timestamp, bool)
        or not isinstance(timestamp, (int, float))
        or not (0 < timestamp < 253402300800)
    ):
        raise ValueError(
            "Timestamp invalido na resposta da OpenSky."
        )

    engine = get_engine()

    try:
        with engine.begin() as connection:
            record_id = connection.execute(
                text("""
                    INSERT INTO bronze.raw_aviation (
                        source,
                        payload
                    )
                    VALUES (
                        :source,
                        CAST(:payload AS JSONB)
                    )
                    RETURNING id
                """),
                {
                    "source": "opensky",
                    "payload": json.dumps(data),
                },
            ).scalar_one()

        print("Ingestao Bronze concluida.")
        print(f"ID do registro: {record_id}")
        print(f"Aeronaves na resposta: {len(states)}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    save_bronze()
