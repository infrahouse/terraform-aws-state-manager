data "aws_iam_policy_document" "assume" {
  statement {
    sid     = "000"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = var.assuming_role_arns
    }
  }

  dynamic "statement" {
    for_each = length(var.assuming_role_patterns) > 0 ? [1] : []
    content {
      sid     = "001"
      actions = ["sts:AssumeRole"]
      principals {
        type        = "AWS"
        identifiers = ["*"]
      }
      condition {
        test     = "StringLike"
        variable = "aws:PrincipalArn"
        values   = var.assuming_role_patterns
      }
    }
  }
}

data "aws_iam_policy_document" "permissions_ro" {
  statement {
    actions = ["s3:ListBucket"]
    resources = [
      "arn:aws:s3:::${var.state_bucket}"
    ]
  }
  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = local.state_resources
  }
}

data "aws_iam_policy_document" "permissions_rw" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = local.state_resources
  }
  statement {
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem"
    ]
    resources = [
      var.terraform_locks_table_arn
    ]
  }
}
