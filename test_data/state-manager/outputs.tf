output "state_manager_role_arn" {
  value = module.test.state_manager_role_arn
}

output "state_manager_role_name" {
  value = module.test.state_manager_role_name
}

output "state_bucket" {
  description = "Name of the S3 bucket created for testing."
  value       = aws_s3_bucket.state.bucket
}

output "locks_table_name" {
  description = "Name of the DynamoDB table created for testing."
  value       = aws_dynamodb_table.locks.name
}
