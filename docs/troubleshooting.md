# Troubleshooting

## Access Denied when running `terraform plan`

**Symptom:** `AccessDenied` error when Terraform tries to acquire a DynamoDB lock.

**Cause:** The role was created with `read_only_permissions = true`, which does not
grant DynamoDB access.

**Fix:** Set `read_only_permissions = false` (the default) for roles that need to run
`terraform plan` or `terraform apply`.

## Role name is different from what was specified

**Symptom:** The `state_manager_role_name` output is shorter than the `name` variable.

**Cause:** AWS IAM role names have a 64-character limit. The module automatically
truncates names using `substr(var.name, 0, 64)`.

**Fix:** This is expected behavior. Use the `state_manager_role_name` output to get the
actual role name, or use a shorter name.

## Cannot assume the state manager role

**Symptom:** `AccessDenied` when trying to `sts:AssumeRole` on the state manager role.

**Cause:** The calling role's ARN is not in the `assuming_role_arns` list.

**Fix:** Add the caller's role ARN to `assuming_role_arns`:

```hcl
assuming_role_arns = [
  "arn:aws:iam::123456789012:role/my-calling-role"
]
```

## Session expired during long Terraform runs

**Symptom:** `ExpiredToken` error partway through a `terraform apply`.

**Cause:** The assumed role session exceeded `max_session_duration`.

**Fix:** Increase the session duration (default is 12 hours, AWS maximum is also
12 hours / 43200 seconds):

```hcl
max_session_duration = 43200  # 12 hours (maximum)
```

Also ensure the calling role requests a session duration that does not exceed this
limit.

## State file not accessible but bucket is correct

**Symptom:** Can list the bucket but get `AccessDenied` on `GetObject` or `PutObject`.

**Cause:** The `state_key` variable does not match the actual path of the state file
in S3.

**Fix:** Verify the `state_key` matches your backend configuration:

```hcl
# In the state manager module:
state_key = "environments/production/terraform.tfstate"

# Must match your backend config:
terraform {
  backend "s3" {
    key = "environments/production/terraform.tfstate"
  }
}
```
