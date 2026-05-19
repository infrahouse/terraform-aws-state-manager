# terraform-aws-state-manager

A Terraform module that creates an IAM role for managing Terraform state files
stored in S3 with DynamoDB locking. It provides secure, controlled access to state
resources with support for both read-only and read-write permission modes.

![Architecture](assets/architecture.svg)

## Features

- **IAM Role with Least Privilege** - Separate read-only and read-write policies
  scoped to specific S3 objects and DynamoDB table
- **Read-Only Mode** - Grant `terraform_remote_state` access without write or lock
  permissions
- **Read-Write Mode** - Full state management with S3 put/delete and DynamoDB locking
- **Wildcard Principal Matching** - Support for `assuming_role_patterns` with
  `StringLike` conditions, useful for AWS SSO roles with auto-generated suffixes
- **Automatic Name Truncation** - Role names exceeding 64 characters are automatically
  truncated to meet the AWS limit
- **Configurable Session Duration** - Control how long assumed sessions last
  (default: 12 hours)
- **Resource Tagging** - Consistent tagging with `created_by_module` and `module_version`

## Quick Start

> **Note:** Check the
> [Terraform Registry](https://registry.terraform.io/modules/infrahouse/state-manager/aws/latest)
> or [GitHub Releases](https://github.com/infrahouse/terraform-aws-state-manager/releases)
> for the latest version.

```hcl
module "state_manager" {
  source  = "registry.infrahouse.com/infrahouse/state-manager/aws"
  version = "1.4.2"

  name                      = "my-terraform-state-manager"
  state_bucket              = "my-terraform-state-bucket"
  terraform_locks_table_arn = "arn:aws:dynamodb:us-west-2:123456789012:table/terraform-locks"

  assuming_role_arns = [
    "arn:aws:iam::123456789012:role/github-actions-role"
  ]
}
```

## Documentation

- [Getting Started](getting-started.md) - Prerequisites and first deployment
- [Configuration](configuration.md) - All variables explained with examples
- [Architecture](architecture.md) - How the module works
- [Examples](examples.md) - Common use cases
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Changelog](changelog.md) - Release history
