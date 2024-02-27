output "state_manager_role_arn" {
  description = "ARN of the created state manager role."
  value       = aws_iam_role.state-manager.arn
}
