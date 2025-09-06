FROM apache/airflow:2.9.0

USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client gcc g++ libpq-dev make && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create directories and set permissions
RUN mkdir -p /opt/airflow/dags && \
    chown -R airflow:root /opt/airflow

# Switch to airflow user
USER airflow
WORKDIR /opt/airflow

# Install Python packages
COPY --chown=airflow:root requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy DAGs
COPY --chown=airflow:root dags/ /opt/airflow/dags/
