variable "region" {}
variable "role_arn" {
  default = null
}

variable "assuming_role_arns" {
  description = "Roles that are allowed to assume this role"
  type        = list(string)
}

variable "max_session_duration" {
  description = "Maximum session duration (in seconds)"
  type        = number
  default     = 12 * 3600
}

variable "name" {
  description = "Role name"
  type        = string
}

variable "read_only_permissions" {
  description = "Whether the role should have read-only permissions"
  type        = bool
  default     = false
}

variable "state_bucket" {
  description = "Name of the S3 bucket with the state"
  type        = string
}

variable "state_key" {
  description = "Path to the state file in the state bucket"
  type        = string
  default     = "terraform.tfstate"
}

variable "terraform_locks_table_arn" {
  description = "DynamoDB table that holds Terraform state locks"
  type        = string
}
