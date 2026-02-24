provider "aws" {
  region = "us-east-1"
}

data "http" "my_ip" {
  url = "https://api.ipify.org"
}

resource "aws_default_vpc" "default" {}

resource "aws_security_group" "redshift_sg" {
  name        = "omnip-redshift-access"
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
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_s3_bucket" "raw_data" {
  bucket        = "omnip-data-lake-dev-2026" 
  force_destroy = true
}

resource "aws_s3_bucket" "athena_results" {
  bucket        = "omnip-athena-results-dev-2026"
  force_destroy = true
}

resource "aws_glue_catalog_database" "dbt_db" {
  name = "omnip_db_dev"
}

resource "aws_athena_workgroup" "main" {
  name          = "omnip_dev_workgroup"
  force_destroy = true

  configuration {
    # Вимикаємо примус, щоб dbt міг сам створювати таблиці (шар Gold)
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/results/"
    }
  }
}

resource "aws_glue_catalog_table" "nbu_rates_raw" {
  name          = "nbu_rates_raw"
  database_name = aws_glue_catalog_database.dbt_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"  = "parquet"
    "compressionType" = "none"
    "typeOfData"      = "file"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw_data.bucket}/bronze/nbu_rates/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "parquet-serde"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "r030"
      type = "int"
    }
    columns {
      name = "txt"
      type = "string"
    }
    columns {
      name = "rate"
      type = "double"
    }
    columns {
      name = "cc"
      type = "string"
    }
    columns {
      name = "exchangedate"
      type = "string"
    }
    columns {
      name = "ingested_at"
      type = "string"
    }
    columns {
      name = "extraction_date"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
}

# --- Outputs для налаштування dbt ---

output "data_lake_bucket" {
  value = aws_s3_bucket.raw_data.id
}

output "athena_results_bucket" {
  value = aws_s3_bucket.athena_results.id
}

output "athena_workgroup_name" {
  value = aws_athena_workgroup.main.name
}

output "s3_staging_dir" {
  description = "Використовуй це значення у своєму profiles.yml для dbt"
  value       = "s3://${aws_s3_bucket.athena_results.bucket}/results/"
}