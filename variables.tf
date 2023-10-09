variable "assuming_role_arns" {
  description = "Roles that are allowed to assume this role. For example, a GitHub Actions worker has a role. The GHA role needs to be able to assume the state-manager role."
  type        = list(string)
}

variable "name" {
  description = "Role name"
}
variable "read_only_permissions" {
  description = "Whether the role should have read-only permissions on the state bucket. It's needed for roles that access the state via terraform_remote_state data source."
  type        = bool
  default     = false
}

variable "state_bucket" {
  description = "Name of the S3 bucket with the state"
}

variable "state_key" {
  description = "Path to the state file in the state bucket"
  type        = string
  default     = "terraform.tfstate"
}

variable "terraform_locks_table_arn" {
  description = "DynamoDB table that holds Terraform state locks."
}
