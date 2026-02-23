variable "db_password" {
  description = "Master password for the Redshift cluster"
  type        = string
  sensitive   = true 
}