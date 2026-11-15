
"""DAG de reprocessamento do Aviation Data Intelligence."""

import os
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


TEST_DATABASE = "aviation_data_intelligence_test"


def execute_reprocessing():
    """Reprocessa Bronze -> Silver -> Gold no banco de testes."""

    database = os.getenv("DB_NAME")

    if database != TEST_DATABASE:
        raise RuntimeError(
            "Execução bloqueada: banco de dados diferente "
            "de aviation_data_intelligence_test."
        )

    from aviation.pipeline import run_pipeline

    run_pipeline(mode="reprocess")


with DAG(
    dag_id="aviation_reprocess_test",
    description="Reprocessamento Bronze, Silver e Gold no PostgreSQL de testes",
    start_date=datetime(2026, 11, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["aviation", "data-engineering", "reprocess", "test"],
) as dag:

    reprocess_data = PythonOperator(
        task_id="reprocess_bronze_silver_gold",
        python_callable=execute_reprocessing,
        retries=0,
    )
