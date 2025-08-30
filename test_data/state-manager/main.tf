module "test" {
  source = "../.."

  assuming_role_arns        = var.assuming_role_arns
  max_session_duration      = var.max_session_duration
  name                      = var.name
  read_only_permissions     = var.read_only_permissions
  state_bucket              = var.state_bucket
  state_key                 = var.state_key
  terraform_locks_table_arn = var.terraform_locks_table_arn
}
