"""Verificações da DAG de ingestão agendada sem depender do Airflow local."""

import ast
from pathlib import Path

import pytest


DAG_PATH = Path(__file__).resolve().parents[1] / "dags" / "aviation_ingestion_scheduled_test.py"


def test_scheduled_dag_configuration():
    source = DAG_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "DAG"
    ]
    assert len(calls) == 1
    kwargs = {kw.arg: kw.value for kw in calls[0].keywords}
    assert ast.literal_eval(kwargs["dag_id"]) == "aviation_ingestion_scheduled_test"
    assert ast.literal_eval(kwargs["schedule"]) == "*/30 * * * *"
    assert ast.literal_eval(kwargs["catchup"]) is False
    assert ast.literal_eval(kwargs["is_paused_upon_creation"]) is True
    assert ast.literal_eval(kwargs["max_active_runs"]) == 1


def test_scheduled_pipeline_refuses_other_databases(monkeypatch):
    # Compila a função isoladamente, evitando import do Airflow no ambiente CI.
    tree = ast.parse(DAG_PATH.read_text(encoding="utf-8"))
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "execute_scheduled_pipeline"
    )
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = {"os": __import__("os"), "TEST_DATABASE": "aviation_data_intelligence_test"}
    exec(compile(module, str(DAG_PATH), "exec"), namespace)
    monkeypatch.setenv("DB_NAME", "aviation_data_intelligence")
    with pytest.raises(RuntimeError, match="bloqueada"):
        namespace["execute_scheduled_pipeline"]()
