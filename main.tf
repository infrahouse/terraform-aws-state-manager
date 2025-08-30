locals {
  state_resources = [
    "arn:aws:s3:::${var.state_bucket}/${var.state_key}",
    "arn:aws:s3:::${var.state_bucket}/plans/*",
    "arn:aws:s3:::${var.state_bucket}/*.zip"
  ]
}

# IAM role
resource "aws_iam_role" "state-manager" {
  name                 = substr(var.name, 0, 64)
  description          = "Role to manage a terraform state of a repo"
  assume_role_policy   = data.aws_iam_policy_document.assume.json
  max_session_duration = var.max_session_duration
  tags = merge(
    local.tags,
    {
      module_version : local.module_version
    }
  )
}

resource "aws_iam_policy" "permissions_ro" {
  name_prefix = "${var.name}-ro"
  policy      = data.aws_iam_policy_document.permissions_ro.json
  tags        = local.tags
}

resource "aws_iam_policy" "permissions_rw" {
  name_prefix = "${var.name}-rw"
  policy      = data.aws_iam_policy_document.permissions_rw.json
  tags        = local.tags
}

resource "aws_iam_role_policy_attachment" "state-manager-ro" {
  policy_arn = aws_iam_policy.permissions_ro.arn
  role       = aws_iam_role.state-manager.name
}

resource "aws_iam_role_policy_attachment" "state-manager-rw" {
  count      = var.read_only_permissions ? 0 : 1
  policy_arn = aws_iam_policy.permissions_rw.arn
  role       = aws_iam_role.state-manager.name
}
