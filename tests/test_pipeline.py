"""Testes unitários do orquestrador com reconciliação atômica."""

from unittest.mock import Mock, call, patch

import pytest

from aviation.pipeline import run_pipeline


@pytest.fixture
def mocked_pipeline():
    order = Mock()
    with (
        patch("aviation.pipeline.save_bronze", side_effect=lambda: order("bronze")) as bronze,
        patch(
            "aviation.pipeline.reconcile_silver_gold",
            side_effect=lambda: order("reconcile"),
        ) as reconcile,
    ):
        yield bronze, reconcile, order


def test_full_mode_runs_ingestion_then_reconciliation(mocked_pipeline):
    bronze, reconcile, order = mocked_pipeline
    run_pipeline(mode="full")
    assert order.call_args_list == [call("bronze"), call("reconcile")]
    bronze.assert_called_once()
    reconcile.assert_called_once()


def test_reprocess_skips_bronze(mocked_pipeline):
    bronze, reconcile, order = mocked_pipeline
    run_pipeline(mode="reprocess")
    bronze.assert_not_called()
    reconcile.assert_called_once()
    assert order.call_args_list == [call("reconcile")]


def test_pipeline_stops_if_bronze_fails(mocked_pipeline):
    bronze, reconcile, _ = mocked_pipeline
    bronze.side_effect = RuntimeError("Falha simulada na Bronze")
    with pytest.raises(RuntimeError, match="Falha simulada na Bronze"):
        run_pipeline()
    reconcile.assert_not_called()


def test_pipeline_propagates_reconciliation_failure(mocked_pipeline):
    bronze, reconcile, _ = mocked_pipeline
    reconcile.side_effect = RuntimeError("Falha simulada na reconciliação")
    with pytest.raises(RuntimeError, match="Falha simulada na reconciliação"):
        run_pipeline()
    bronze.assert_called_once()
    reconcile.assert_called_once()


def test_invalid_pipeline_mode(mocked_pipeline):
    bronze, reconcile, _ = mocked_pipeline
    with pytest.raises(ValueError, match="Modo de execução inválido"):
        run_pipeline(mode="invalid")
    bronze.assert_not_called()
    reconcile.assert_not_called()
