# Terraform AWS State Manager

This Terraform module creates an IAM role designed to manage Terraform state files stored in S3 with DynamoDB locking.
The role provides secure, controlled access to state resources while supporting both read-only and read-write permissions.

## Features

- Creates IAM role with configurable assume role policies
- Supports both read-only and read-write permissions for state management
- Automatic role name truncation to meet AWS 64-character limit
- DynamoDB integration for state locking
- Configurable session duration
- Comprehensive resource tagging

## Usage

### Basic Configuration
```hcl
module "state_manager" {
  source  = "infrahouse/state-manager/aws"
  version = "1.4.0"

  name                      = "my-terraform-state-manager"
  state_bucket              = "my-terraform-state-bucket"
  terraform_locks_table_arn = "arn:aws:dynamodb:us-west-2:123456789012:table/terraform-locks"

  assuming_role_arns = [
    "arn:aws:iam::123456789012:role/github-actions-role"
  ]
}
```

### Advanced Configuration with GitHub Actions
```hcl
module "state_manager" {
  source  = "infrahouse/state-manager/aws"
  version = "1.4.0"

  name = "ih-tf-${var.repo_name}-state-manager"

  assuming_role_arns = concat(
    [
      aws_iam_role.github.arn
    ],
    var.trusted_arns
  )

  state_bucket              = var.state_bucket
  state_key                 = "environments/${terraform.workspace}/terraform.tfstate"
  terraform_locks_table_arn = var.terraform_locks_table_arn
  max_session_duration      = 3600  # 1 hour
  read_only_permissions     = false
}
```

### Read-Only State Access
```hcl
module "state_reader" {
  source  = "infrahouse/state-manager/aws"
  version = "1.4.0"

  name                      = "terraform-state-reader"
  state_bucket              = "my-terraform-state-bucket" 
  terraform_locks_table_arn = "arn:aws:dynamodb:us-west-2:123456789012:table/terraform-locks"
  read_only_permissions     = true

  assuming_role_arns = [
    "arn:aws:iam::123456789012:role/readonly-access-role"
  ]
}
```
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 5.11, < 7.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 5.11, < 7.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_iam_policy.permissions_ro](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.permissions_rw](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role.state-manager](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.state-manager-ro](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.state-manager-rw](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_policy_document.assume](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.permissions_ro](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.permissions_rw](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_assuming_role_arns"></a> [assuming\_role\_arns](#input\_assuming\_role\_arns) | Roles that are allowed to assume this role. For example, a GitHub Actions worker has a role. The GHA role needs to be able to assume the state-manager role. | `list(string)` | n/a | yes |
| <a name="input_max_session_duration"></a> [max\_session\_duration](#input\_max\_session\_duration) | Maximum session duration (in seconds) that you want to set for the specified role. | `number` | `43200` | no |
| <a name="input_name"></a> [name](#input\_name) | Role name | `string` | n/a | yes |
| <a name="input_read_only_permissions"></a> [read\_only\_permissions](#input\_read\_only\_permissions) | Whether the role should have read-only permissions on the state bucket. It's needed for roles that access the state via terraform\_remote\_state data source. | `bool` | `false` | no |
| <a name="input_state_bucket"></a> [state\_bucket](#input\_state\_bucket) | Name of the S3 bucket with the state | `string` | n/a | yes |
| <a name="input_state_key"></a> [state\_key](#input\_state\_key) | Path to the state file in the state bucket | `string` | `"terraform.tfstate"` | no |
| <a name="input_terraform_locks_table_arn"></a> [terraform\_locks\_table\_arn](#input\_terraform\_locks\_table\_arn) | DynamoDB table that holds Terraform state locks. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_state_manager_role_arn"></a> [state\_manager\_role\_arn](#output\_state\_manager\_role\_arn) | ARN of the created state manager role. |
| <a name="output_state_manager_role_name"></a> [state\_manager\_role\_name](#output\_state\_manager\_role\_name) | Name of the created state manager role. |
