
"""Orquestração do pipeline Aviation Data Intelligence."""

import argparse
import logging
import time

from aviation.ingestion.save_bronze import save_bronze
from aviation.processing.reconcile import main as reconcile_silver_gold


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def run_pipeline(mode="full"):
    """Executa o pipeline completo ou reprocessa dados existentes."""

    if mode not in {"full", "reprocess"}:
        raise ValueError(f"Modo de execução inválido: {mode}")

    start = time.perf_counter()

    logger.info("Iniciando Aviation Data Intelligence")
    logger.info("Modo de execução: %s", mode)

    try:
        if mode == "full":
            logger.info("Etapa 1/3: ingestão Bronze")
            save_bronze()
        else:
            logger.info(
                "Reprocessamento: utilizando dados Bronze existentes"
            )

        logger.info("Reconciliação transacional Bronze -> Silver -> Gold")
        reconcile_silver_gold()

    except Exception:
        logger.exception("Falha na execução do pipeline")
        raise

    duration = time.perf_counter() - start

    logger.info(
        "Pipeline concluído em %.2f segundos",
        duration,
    )


def main():
    """Interpreta os argumentos da linha de comando."""

    parser = argparse.ArgumentParser(
        description="Aviation Data Intelligence Pipeline"
    )

    parser.add_argument(
        "--mode",
        choices=["full", "reprocess"],
        default="full",
        help="Modo de execução do pipeline",
    )

    args = parser.parse_args()

    run_pipeline(mode=args.mode)


if __name__ == "__main__":
    main()
