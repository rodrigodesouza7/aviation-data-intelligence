"""DAG de ingestão periódica OpenSky -> Bronze -> Silver -> Gold (teste)."""

import os
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator


TEST_DATABASE = "aviation_data_intelligence_test"


def execute_scheduled_pipeline():
    """Bloqueia bancos não autorizados antes de acessar a API ou escrever dados."""
    if os.getenv("DB_NAME") != TEST_DATABASE:
        raise RuntimeError(
            "Ingestão agendada bloqueada: DB_NAME deve ser "
            "aviation_data_intelligence_test."
        )

    from aviation.pipeline import run_pipeline

    run_pipeline(mode="full")


with DAG(
    dag_id="aviation_ingestion_scheduled_test",
    description="Coleta OpenSky e reconciliação atômica Silver/Gold no banco de testes",
    start_date=datetime(2026, 11, 17, tzinfo=timezone.utc),
    schedule="*/30 * * * *",
    catchup=False,
    is_paused_upon_creation=True,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["aviation", "opensky", "ingestion", "test"],
) as dag:
    PythonOperator(
        task_id="ingest_and_reconcile",
        python_callable=execute_scheduled_pipeline,
        execution_timeout=timedelta(minutes=10),
    )
