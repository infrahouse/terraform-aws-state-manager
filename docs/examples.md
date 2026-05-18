# Examples

## Basic Read-Write Access

The simplest configuration — creates a state manager role with full read-write access.

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

## Read-Only State Access

For roles that only need `terraform_remote_state` data source access. No DynamoDB
lock access is granted, so `terraform plan`/`apply` will not work with this role.

```hcl
module "state_reader" {
  source  = "registry.infrahouse.com/infrahouse/state-manager/aws"
  version = "1.4.2"

  name                      = "terraform-state-reader"
  state_bucket              = "my-terraform-state-bucket"
  terraform_locks_table_arn = "arn:aws:dynamodb:us-west-2:123456789012:table/terraform-locks"
  read_only_permissions     = true

  assuming_role_arns = [
    "arn:aws:iam::123456789012:role/readonly-role"
  ]
}
```

## GitHub Actions Integration

Create a state manager role alongside a GitHub Actions identity, with a custom
state key per workspace.

```hcl
module "state_manager" {
  source  = "registry.infrahouse.com/infrahouse/state-manager/aws"
  version = "1.4.2"

  name = "ih-tf-${var.repo_name}-state-manager"

  assuming_role_arns = concat(
    [aws_iam_role.github.arn],
    var.trusted_arns
  )

  state_bucket              = var.state_bucket
  state_key                 = "environments/${terraform.workspace}/terraform.tfstate"
  terraform_locks_table_arn = var.terraform_locks_table_arn
  max_session_duration      = 3600
}
```

## Multiple Roles for the Same State

Create both a read-write role for CI/CD and a read-only role for monitoring.

```hcl
module "state_manager_rw" {
  source  = "registry.infrahouse.com/infrahouse/state-manager/aws"
  version = "1.4.2"

  name                      = "my-state-manager-rw"
  state_bucket              = "my-terraform-state-bucket"
  terraform_locks_table_arn = var.terraform_locks_table_arn

  assuming_role_arns = [
    aws_iam_role.github_actions.arn
  ]
}

module "state_manager_ro" {
  source  = "registry.infrahouse.com/infrahouse/state-manager/aws"
  version = "1.4.2"

  name                      = "my-state-manager-ro"
  state_bucket              = "my-terraform-state-bucket"
  terraform_locks_table_arn = var.terraform_locks_table_arn
  read_only_permissions     = true

  assuming_role_arns = [
    aws_iam_role.monitoring.arn
  ]
}
```

## Working Examples

See the [`examples/`](https://github.com/infrahouse/terraform-aws-state-manager/tree/main/examples)
directory for complete, runnable examples:

- [`examples/basic/`](https://github.com/infrahouse/terraform-aws-state-manager/tree/main/examples/basic) -
  Basic read-write state manager
- [`examples/read-only/`](https://github.com/infrahouse/terraform-aws-state-manager/tree/main/examples/read-only) -
  Read-only state access
