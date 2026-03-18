# NBU Currency Analytics: AWS Athena & dbt Cloud Pipeline

A professional Python-based solution for automated currency data ingestion, cloud-based analytical modeling, and financial volatility visualization.

## 📁 Project Structure

- `src/ingest_nbu_rates.py`: **Ingestion Engine** that fetches daily exchange rates from the NBU API and loads them into AWS S3 (Bronze Layer).
- `models/`: **Transformation Layer** featuring dbt models, schemas, and window-function logic for financial data modeling in AWS Athena.
- `src/visualize_rates.py`: **Analytics Module** leveraging the Seaborn API to generate high-fidelity volatility and correlation charts.
- `Dockerfile`: **Infrastructure Manifest** ensuring environment isolation and 1:1 parity between development and GitHub Actions.
- `.github/workflows/main.yml`: **Orchestration Layer** (CI/CD) automating the entire ELT lifecycle, from ingestion to artifact generation.

## 🛠 Modern ELT Architecture (Core Pipeline)

Unlike traditional ETL, this tool follows a **Load-then-Transform** approach to optimize cloud compute costs and maintain data lineage:

1. **Phase 1: Extract & Load (Python + AWS SDK)**
   - Raw currency data—including **USD**, **EUR**, and other major pairs—is ingested and stored in **Parquet** format within the S3-based Data Lake (Bronze Layer).
2. **Phase 2: Transformation (dbt + AWS Athena)**
   - Applies tiered business logic to raw data, generating optimized **Silver** (cleansed/deduplicated) and **Gold** (analytical marts) tables.
3. **Phase 3: Visualization (Seaborn API)**
   - Automatically generates statistical insights (e.g., **Daily Yield %**) and saves them as high-resolution image artifacts.

## 🔍 Data Quality & Engineering Features

- **Automated Partition Management**: Handles S3 partitions (`year`, `month`) automatically via dbt-athena configuration.
- **Volatility Engine**: Implements SQL Window Functions (`LAG`) to calculate day-over-day growth/decline percentages.
- **Type Safety & Schema Control**: Explicitly handles data types to prevent Athena `TYPE_MISMATCH` errors during incremental loads.
- **Containerized Parity**: The entire stack is isolated via Docker, ensuring identical execution in local and cloud environments.

## 📊 Performance Metrics (Current Run)

The latest pipeline execution achieved a high-quality linkage with the following breakdown:

- **Total Execution Time**: **1m 11s** (From API trigger to final PNG generation).
- **Automation Level**: **100%** (Triggered automatically via GitHub Actions on every push).
- **Transformation Success**: **11/11 dbt models** and tests passed (including incremental overwrites).
- **Build Efficiency**: Optimized Docker image assembly in **<50 seconds**.

## 🚀 Installation & Usage

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Inx1992/omnip_project.git
   cd omnip_project

   ```

2. **Run the pipeline (Docker)**:

   ```bash
   # Ensure .env file is configured with AWS credentials
    docker build -t nbu-analytics .
    docker run --env-file .env nbu-analytics
   ```

3. **Access the results**:
   - **GitHub Actions**: Download generated artifacts (e.g., `usd_eur_bivariate.png`) from the workflow summary.
   - **AWS Athena**: Query the `omnip_db_dev_silver` or `gold` databases.

## ⚙️ Tech Stack Configuration 

**The performance and analytical depth are controlled by the interaction of the following components**:

- **Compute & Storage**: AWS Athena & S3 (Serverless Data Warehouse).
- **Transformation**: dbt (Handles modular SQL modeling, partitioning, and testing).
- **Visualization**: Seaborn & Matplotlib (High-fidelity statistical graphics).
- **Containerization**: Docker (Ensures reproducible and isolated runtime).

## 📝 Technical Notes

- **The pipeline is considered Highly Reliable if**:
  - The GitHub Actions workflow finishes with a Success status for all jobs.
  - **AND** the dbt test suite confirms that daily_yield_pct contains no null values in the Silver layer.
