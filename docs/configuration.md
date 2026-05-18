# Configuration

## Required Variables

### `name`

- **Type:** `string`

The IAM role name. If the name exceeds 64 characters, it is automatically truncated
to meet the AWS limit.

```hcl
name = "ih-tf-my-repo-state-manager"
```

### `state_bucket`

- **Type:** `string`

Name of the S3 bucket that stores Terraform state files.

```hcl
state_bucket = "my-org-terraform-states"
```

### `terraform_locks_table_arn`

- **Type:** `string`

ARN of the DynamoDB table used for Terraform state locking.

```hcl
terraform_locks_table_arn = "arn:aws:dynamodb:us-west-2:123456789012:table/terraform-locks"
```

### `assuming_role_arns`

- **Type:** `list(string)`

List of IAM role ARNs that are allowed to assume this state manager role. Typically,
these are CI/CD worker roles (e.g., GitHub Actions) or other service roles.

```hcl
assuming_role_arns = [
  "arn:aws:iam::123456789012:role/github-actions-role",
  "arn:aws:iam::123456789012:role/admin-role"
]
```

### `assuming_role_patterns`

- **Type:** `list(string)`
- **Default:** `[]`

ARN patterns with wildcards for roles allowed to assume this role. Uses a `StringLike`
condition on `aws:PrincipalArn` instead of exact matching. This is useful for AWS SSO
roles, which have auto-generated suffixes that change when permission sets are recreated.

```hcl
assuming_role_patterns = [
  "arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_AdministratorAccess_*"
]
```

Can be used alongside `assuming_role_arns` — exact ARNs are matched by the trust policy's
principal list, while patterns are matched via a `StringLike` condition.

## Optional Variables

### `read_only_permissions`

- **Type:** `bool`
- **Default:** `false`

When `true`, the role only gets S3 read permissions (`s3:ListBucket`, `s3:GetObject`).
No DynamoDB lock access is granted. Use this for roles that only need
`terraform_remote_state` data source access.

When `false` (default), the role also gets S3 write permissions (`s3:PutObject`,
`s3:DeleteObject`) and DynamoDB lock operations (`DescribeTable`, `GetItem`, `PutItem`,
`DeleteItem`).

```hcl
read_only_permissions = true
```

### `state_key`

- **Type:** `string`
- **Default:** `"terraform.tfstate"`

Path to the state file within the S3 bucket. The module also grants access to
`plans/*` and `*.zip` paths in the same bucket for plan artifacts.

```hcl
state_key = "environments/production/terraform.tfstate"
```

### `max_session_duration`

- **Type:** `number`
- **Default:** `43200` (12 hours)

Maximum session duration in seconds for the IAM role. AWS allows values between
3600 (1 hour) and 43200 (12 hours).

```hcl
max_session_duration = 3600  # 1 hour
```

## Outputs

### `state_manager_role_arn`

ARN of the created IAM role.

### `state_manager_role_name`

Name of the created IAM role (may be truncated from the input `name` if it exceeded
64 characters).
