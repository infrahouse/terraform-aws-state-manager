# Basic example — read-write state manager role
#
# Creates an IAM role that allows a GitHub Actions role
# to read and write Terraform state in S3 with DynamoDB locking.

provider "aws" {
  region = "us-west-2"
  default_tags {
    tags = {
      created_by = "infrahouse/terraform-aws-state-manager"
    }
  }
}

module "state_manager" {
  source  = "registry.infrahouse.com/infrahouse/state-manager/aws"
  version = "1.4.2"

  name                      = "my-terraform-state-manager"
  state_bucket              = "my-terraform-state-bucket"
  state_key                 = "environments/production/terraform.tfstate"
  terraform_locks_table_arn = "arn:aws:dynamodb:us-west-2:123456789012:table/terraform-locks"

  assuming_role_arns = [
    "arn:aws:iam::123456789012:role/github-actions-role"
  ]
}

output "state_manager_role_arn" {
  value = module.state_manager.state_manager_role_arn
}

output "state_manager_role_name" {
  value = module.state_manager.state_manager_role_name
}
