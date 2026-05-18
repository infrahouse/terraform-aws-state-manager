variable "region" {}
variable "role_arn" {
  default = null
}

variable "environment" {
  description = "Environment name"
  type        = string
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

variable "state_key" {
  description = "Path to the state file in the state bucket"
  type        = string
  default     = "terraform.tfstate"
}
