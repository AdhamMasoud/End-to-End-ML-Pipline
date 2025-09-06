from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import sqlalchemy  # for DB connection
import pickle as pkl
import logging

# Step A: Define function (your notebook code goes here)
def run_ml_pipeline():
    try:
        logging.info("Starting ML pipeline...")
        
        # 1. Connect to DB
        logging.info("Connecting to database...")

        # 1. Connect to DB (example with Postgres)
        engine = sqlalchemy.create_engine("postgresql://postgres:password@host.docker.internal:5432/database_name")
        
        # 2. Load data
        logging.info("Loading data from database...")
        df = pd.read_sql("SELECT * FROM subscription", engine)
        logging.info(f"Loaded {len(df)} rows from database")

        # 3. Apply model
        logging.info("Loading model and encoder...")
        with open("/opt/airflow/dags/bank_classification.pkl", "rb") as model_file:
            model = pkl.load(model_file)
        logging.info("Model loaded successfully")
        
        with open("/opt/airflow/dags/encoder.pkl", "rb") as encoder_file:
            encoders = pkl.load(encoder_file)
        logging.info("Encoder loaded successfully")

        # 4. Transform data
        logging.info("Transforming data...")
        for column in encoders.keys():
            if column in df.columns:
                le = encoders[column]
                df[column] = le.transform(df[column])
        
        # 5. Make predictions
        logging.info("Making predictions...")
        df["pred_prob"] = model.predict_proba(df)[:, 1]
        df["prediction"] = (df["pred_prob"] >= 0.3).astype(int)

        # 6. Inverse transform
        logging.info("Inverse transforming categorical columns...")
        for column in encoders.keys():
            if column in df.columns:
                le = encoders[column]
                df[column] = le.inverse_transform(df[column])

        # 7. Write results
        logging.info("Writing results back to database...")
        df.to_sql("subscription_predictions", engine, if_exists="replace", index=False)
        
        logging.info("✅ ML pipeline finished successfully")
        return True
    
    except Exception as e:
        logging.error(f"❌ Error in ML pipeline: {str(e)}")
        raise

with DAG(
    dag_id="ml_pipeline_dag",
    start_date=datetime(2025, 8, 1),
    schedule_interval="@daily",
    catchup=False
) as dag:

    run_pipeline = PythonOperator(
        task_id="run_ml_pipeline",
        python_callable=run_ml_pipeline
    )