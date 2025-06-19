from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

with DAG(
    dag_id="cloud_sql_proxy_auto_dag",
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    tags=["cloudsql", "proxy"],
) as dag:

    run_sql_with_proxy = BashOperator(
        task_id="run_sql_with_proxy",
        bash_command="""
        echo "📥 Downloading Cloud SQL Proxy from GCS..."
        gsutil cp gs://your-bucket/scripts/cloud_sql_proxy /tmp/cloud_sql_proxy
        chmod +x /tmp/cloud_sql_proxy

        echo "🚀 Starting Cloud SQL Proxy..."
        /tmp/cloud_sql_proxy -instances={{ var.value.INSTANCE_CONNECTION_NAME }}=tcp:5432 &

        echo "⏳ Waiting for proxy to initialize..."
        sleep 10

        echo "🔗 Connecting to DB via Proxy..."
        PGPASSWORD={{ var.value.DB_PASSWORD }} \
        psql -h 127.0.0.1 -U {{ var.value.DB_USER }} -d {{ var.value.DB_NAME }} -p 5432 -c "SELECT NOW();"

        echo "✅ Query successful."
        """,
    )