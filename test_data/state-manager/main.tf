data "aws_caller_identity" "current" {}

locals {
  bucket_name = "${substr(var.name, 0, 40)}-${data.aws_caller_identity.current.account_id}"
  table_name  = "${substr(var.name, 0, 40)}-locks"
}

resource "aws_s3_bucket" "state" {
  bucket        = local.bucket_name
  force_destroy = true
}

resource "aws_dynamodb_table" "locks" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}

module "test" {
  source = "../.."

  environment               = var.environment
  assuming_role_arns        = var.assuming_role_arns
  assuming_role_patterns    = var.assuming_role_patterns
  max_session_duration      = var.max_session_duration
  name                      = var.name
  read_only_permissions     = var.read_only_permissions
  state_bucket              = aws_s3_bucket.state.bucket
  state_key                 = var.state_key
  terraform_locks_table_arn = aws_dynamodb_table.locks.arn
}
