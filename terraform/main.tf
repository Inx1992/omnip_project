provider "aws" {
  region = "us-east-1"
}

# 1. Отримуємо твій поточний IP для доступу
data "http" "my_ip" {
  url = "https://api.ipify.org"
}

# 2. Використовуємо стандартну мережу
resource "aws_default_vpc" "default" {}

# 3. Security Group (Файрвол)
resource "aws_security_group" "redshift_sg" {
  name        = "redshift-allow-my-ip-v2"
  description = "Allow access to Redshift from my current IP"
  vpc_id      = aws_default_vpc.default.id

  ingress {
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = ["${data.http.my_ip.response_body}/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4. S3 бакети
# Основний бакет для даних (Bronze, Silver, Gold папки будуть тут)
resource "aws_s3_bucket" "raw_data" {
  bucket = "omnip-raw-data-dev-2026-v1" 
}

# Бакет для технічних результатів Athena (обов'язково для роботи SQL)
resource "aws_s3_bucket" "athena_results" {
  bucket = "omnip-athena-results-dev-2026-v1"
}

# 5. AWS Athena (Serverless SQL двигун)
resource "aws_athena_workgroup" "main" {
  name = "primary"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/"
    }
  }
}

# --- REDSHIFT ТИМЧАСОВО ВИМКНЕНО ДЛЯ ЕКОНОМІЇ ---
/*
resource "aws_redshift_cluster" "omnip_redshift" {
  cluster_identifier = "omnip-cluster-dev-v2"
  database_name      = "dev"
  master_username    = "admin"
  master_password    = var.db_password 

  node_type          = "ra3.xlplus"
  cluster_type       = "single-node"
  
  vpc_security_group_ids = [aws_security_group.redshift_sg.id]

  publicly_accessible = true
  skip_final_snapshot = true
}
*/

# --- OUTPUTS ---

output "s3_bucket_name" {
  value = aws_s3_bucket.raw_data.id
}

output "athena_workgroup" {
  value = aws_athena_workgroup.main.name
}

# output "redshift_endpoint" {
#   value = aws_redshift_cluster.omnip_redshift.endpoint
# }