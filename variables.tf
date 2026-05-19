variable "assuming_role_arns" {
  description = <<-EOT
    Roles that are allowed to assume this role. For example, a GitHub Actions
    worker has a role. The GHA role needs to be able to assume the state-manager role.
  EOT
  type        = list(string)

  validation {
    condition     = length(var.assuming_role_arns) > 0
    error_message = "assuming_role_arns must contain at least one ARN."
  }

  validation {
    condition     = alltrue([for arn in var.assuming_role_arns : can(regex("^arn:aws:iam::", arn))])
    error_message = "All assuming_role_arns must be valid IAM ARNs starting with 'arn:aws:iam::'."
  }
}

variable "assuming_role_patterns" {
  description = <<-EOT
    ARN patterns (with wildcards) for roles allowed to assume this role.
    Uses StringLike condition on aws:PrincipalArn instead of exact matching.
    Useful for AWS SSO roles with auto-generated suffixes.
    Each pattern must include an explicit 12-digit AWS account ID.
    Example: ["arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_AdministratorAccess_*"]
  EOT
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for p in var.assuming_role_patterns : can(regex("^arn:aws:iam::[0-9]{12}:", p))
    ])
    error_message = "Each assuming_role_patterns entry must be a valid IAM ARN pattern starting with 'arn:aws:iam::' followed by a 12-digit account ID."
  }
}

variable "environment" {
  description = "Environment name (e.g., development, staging, production)."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9_]+$", var.environment))
    error_message = "environment must contain only lowercase letters, numbers, and underscores. Got: ${var.environment}."
  }
}

variable "max_session_duration" {
  description = "Maximum session duration (in seconds) that you want to set for the specified role."
  type        = number
  default     = 12 * 3600

  validation {
    condition     = var.max_session_duration >= 3600 && var.max_session_duration <= 43200
    error_message = "max_session_duration must be between 3600 (1 hour) and 43200 (12 hours). Got: ${var.max_session_duration}."
  }
}

variable "name" {
  description = "Role name"
  type        = string

  validation {
    condition     = length(var.name) > 0
    error_message = "name must not be empty."
  }

  validation {
    condition     = can(regex("^[a-zA-Z0-9+=,.@_-]+$", var.name))
    error_message = "name must contain only alphanumeric characters and +=,.@_- characters. Got: ${var.name}."
  }
}

variable "read_only_permissions" {
  description = <<-EOT
    Whether the role should have read-only permissions on the state bucket.
    It's needed for roles that access the state via terraform_remote_state data source.
  EOT
  type        = bool
  default     = false
}

variable "state_bucket" {
  description = "Name of the S3 bucket with the state"
  type        = string

  validation {
    condition     = length(var.state_bucket) > 0
    error_message = "state_bucket must not be empty."
  }

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.state_bucket))
    error_message = "state_bucket must be a valid S3 bucket name. Got: ${var.state_bucket}."
  }
}

variable "state_key" {
  description = "Path to the state file in the state bucket"
  type        = string
  default     = "terraform.tfstate"

  validation {
    condition     = length(var.state_key) > 0
    error_message = "state_key must not be empty."
  }
}

variable "terraform_locks_table_arn" {
  description = "DynamoDB table that holds Terraform state locks."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:dynamodb:", var.terraform_locks_table_arn))
    error_message = "terraform_locks_table_arn must be a valid DynamoDB table ARN starting with 'arn:aws:dynamodb:'. Got: ${var.terraform_locks_table_arn}."
  }
}
