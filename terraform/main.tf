provider "aws" {
  region = "us-east-1"
}

data "http" "my_ip" {
  url = "https://api.ipify.org"
}

# --- Мережа та безпека ---

resource "aws_default_vpc" "default" {}

resource "aws_security_group" "redshift_sg" {
  name   = "omnip-redshift-access"
  vpc_id = aws_default_vpc.default.id

  ingress {
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = ["${data.http.my_ip.response_body}/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- Зберігання даних (S3) ---

resource "aws_s3_bucket" "raw_data" {
  bucket        = "omnip-data-lake-dev-2026" 
  force_destroy = true
}

resource "aws_s3_bucket_intelligent_tiering_configuration" "raw_data_tiering" {
  bucket = aws_s3_bucket.raw_data.id
  name   = "EntireBucket"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }
}

resource "aws_s3_bucket" "athena_results" {
  bucket        = "omnip-athena-results-dev-2026"
  force_destroy = true
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results_lifecycle" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "auto-delete-athena-results"
    status = "Enabled"

    expiration {
      days = 3
    }
  }
}

# --- Логування та Моніторинг ---

resource "aws_cloudwatch_log_group" "athena_logs" {
  name              = "/aws/athena/omnip_dev_workgroup"
  retention_in_days = 1
}

# --- Каталог даних (Glue & Athena) ---

resource "aws_glue_catalog_database" "dbt_db" {
  name = "omnip_db_dev"
}

resource "aws_athena_workgroup" "main" {
  name          = "omnip_dev_workgroup"
  force_destroy = true

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/results/"
    }
  }
  
  depends_on = [aws_cloudwatch_log_group.athena_logs]
}

# ПРИМІТКА: Таблиця nbu_rates_raw тепер створюється автоматично через Python-скрипт (awswrangler)

# --- Контроль витрат ---

resource "aws_budgets_budget" "monthly_limit" {
  name              = "omnip-monthly-5-usd-limit"
  budget_type       = "COST"
  limit_amount      = "5"
  limit_unit        = "USD"
  time_period_start = "2026-02-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["inxhouse92@gmail.com"]
  }
}

# --- Outputs ---

output "data_lake_bucket" { value = aws_s3_bucket.raw_data.id }
output "athena_results_bucket" { value = aws_s3_bucket.athena_results.id }
output "athena_workgroup_name" { value = aws_athena_workgroup.main.name }
output "s3_staging_dir" { value = "s3://${aws_s3_bucket.athena_results.bucket}/results/" }