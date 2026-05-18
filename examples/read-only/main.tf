# Read-only example — state reader role
#
# Creates an IAM role with read-only access to Terraform state.
# Useful for roles that only need terraform_remote_state data source access.
# No DynamoDB lock access is granted in this mode.

provider "aws" {
  region = "us-west-2"
  default_tags {
    tags = {
      created_by = "infrahouse/terraform-aws-state-manager"
    }
  }
}

module "state_reader" {
  source  = "registry.infrahouse.com/infrahouse/state-manager/aws"
  version = "1.4.2"

  name                      = "terraform-state-reader"
  state_bucket              = "my-terraform-state-bucket"
  terraform_locks_table_arn = "arn:aws:dynamodb:us-west-2:123456789012:table/terraform-locks"
  read_only_permissions     = true

  assuming_role_arns = [
    "arn:aws:iam::123456789012:role/readonly-access-role"
  ]
}

output "state_reader_role_arn" {
  value = module.state_reader.state_manager_role_arn
}
