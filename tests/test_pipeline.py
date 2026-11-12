
"""Testes unitários do orquestrador Aviation Data Intelligence."""

import sys
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest


# Permite importar o pacote aviation a partir da pasta src.
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))

from aviation.pipeline import run_pipeline


@pytest.fixture
def mocked_pipeline():
    """Simula as três etapas sem acessar serviços externos."""

    execution_order = Mock()

    with (
        patch(
            "aviation.pipeline.save_bronze",
            side_effect=lambda: execution_order("bronze"),
        ) as bronze,
        patch(
            "aviation.pipeline.process_silver",
            side_effect=lambda: execution_order("silver"),
        ) as silver,
        patch(
            "aviation.pipeline.process_gold",
            side_effect=lambda: execution_order("gold"),
        ) as gold,
    ):
        yield bronze, silver, gold, execution_order


def test_pipeline_execution_order(mocked_pipeline):
    """Verifica a ordem Bronze -> Silver -> Gold."""

    bronze, silver, gold, execution_order = mocked_pipeline

    run_pipeline()

    assert execution_order.call_args_list == [
        call("bronze"),
        call("silver"),
        call("gold"),
    ]

    bronze.assert_called_once()
    silver.assert_called_once()
    gold.assert_called_once()


def test_pipeline_stops_if_bronze_fails(mocked_pipeline):
    """Interrompe o pipeline se a ingestão falhar."""

    bronze, silver, gold, _ = mocked_pipeline

    bronze.side_effect = RuntimeError(
        "Falha simulada na Bronze"
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada na Bronze",
    ):
        run_pipeline()

    bronze.assert_called_once()
    silver.assert_not_called()
    gold.assert_not_called()


def test_pipeline_stops_if_silver_fails(mocked_pipeline):
    """Não executa Gold quando Silver falha."""

    bronze, silver, gold, _ = mocked_pipeline

    silver.side_effect = RuntimeError(
        "Falha simulada na Silver"
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada na Silver",
    ):
        run_pipeline()

    bronze.assert_called_once()
    silver.assert_called_once()
    gold.assert_not_called()


def test_pipeline_propagates_gold_failure(mocked_pipeline):
    """Propaga erros da Gold para o chamador."""

    bronze, silver, gold, _ = mocked_pipeline

    gold.side_effect = RuntimeError(
        "Falha simulada na Gold"
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada na Gold",
    ):
        run_pipeline()

    bronze.assert_called_once()
    silver.assert_called_once()
    gold.assert_called_once()


def test_reprocess_skips_bronze(mocked_pipeline):
    """Reprocessamento não deve consultar a OpenSky."""

    bronze, silver, gold, execution_order = mocked_pipeline

    run_pipeline(mode="reprocess")

    bronze.assert_not_called()
    silver.assert_called_once()
    gold.assert_called_once()

    assert execution_order.call_args_list == [
        call("silver"),
        call("gold"),
    ]


def test_full_mode_runs_all_stages(mocked_pipeline):
    """Modo completo executa todas as etapas."""

    bronze, silver, gold, execution_order = mocked_pipeline

    run_pipeline(mode="full")

    bronze.assert_called_once()
    silver.assert_called_once()
    gold.assert_called_once()

    assert execution_order.call_args_list == [
        call("bronze"),
        call("silver"),
        call("gold"),
    ]


def test_invalid_pipeline_mode(mocked_pipeline):
    """Modos inválidos devem ser rejeitados."""

    bronze, silver, gold, _ = mocked_pipeline

    with pytest.raises(
        ValueError,
        match="Modo de execução inválido",
    ):
        run_pipeline(mode="invalid")

    bronze.assert_not_called()
    silver.assert_not_called()
    gold.assert_not_called()
