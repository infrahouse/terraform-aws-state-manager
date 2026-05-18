# Getting Started

## Prerequisites

- Terraform >= 1.0
- AWS provider >= 5.11, < 7.0
- An S3 bucket for storing Terraform state
- A DynamoDB table for state locking
- One or more IAM role ARNs that will assume the state manager role

## First Deployment

### 1. Define the module

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

### 2. Apply

```bash
terraform init
terraform plan
terraform apply
```

### 3. Use the role ARN

After applying, use the output `state_manager_role_arn` in your Terraform backend
configuration or pass it to other modules that need state access.

```hcl
output "state_manager_role_arn" {
  value = module.state_manager.state_manager_role_arn
}
```

## Next Steps

- See [Configuration](configuration.md) for all available variables
- See [Examples](examples.md) for common use cases like read-only access
  and GitHub Actions integration
