
"""Orquestração do pipeline Aviation Data Intelligence."""

import logging
import time

from aviation.ingestion.save_bronze import save_bronze
from aviation.processing.bronze_to_silver import main as process_silver
from aviation.processing.silver_to_gold import main as process_gold


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def run_pipeline():
    """Executa o fluxo OpenSky -> Bronze -> Silver -> Gold."""

    start = time.perf_counter()

    logger.info("Iniciando Aviation Data Intelligence")

    try:
        logger.info("Etapa 1/3: ingestão Bronze")
        save_bronze()

        logger.info("Etapa 2/3: transformação Silver")
        process_silver()

        logger.info("Etapa 3/3: agregação Gold")
        process_gold()

    except Exception:
        logger.exception("Falha na execução do pipeline")
        raise

    duration = time.perf_counter() - start

    logger.info(
        "Pipeline concluído em %.2f segundos",
        duration,
    )


if __name__ == "__main__":
    run_pipeline()
