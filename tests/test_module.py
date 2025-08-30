from os import path as osp, remove
import json
from textwrap import dedent

import pytest
from pytest_infrahouse import terraform_apply

from tests.conftest import LOG, TERRAFORM_ROOT_DIR


@pytest.mark.parametrize("aws_provider_version", ["~> 5.11", "~> 6.0"])
@pytest.mark.parametrize(
    "name, read_only",
    [
        ("state-manager-test", False),
        ("state-manager-ro-test", True),
        (
            "state-manager-very-long-name-that-exceeds-typical-aws-limits-but-should-still-work",
            False,
        ),
    ],
)
def test_module(
    aws_provider_version,
    name,
    read_only,
    aws_region,
    test_role_arn,
    keep_after,
    boto3_session,
):
    terraform_dir = f"{TERRAFORM_ROOT_DIR}/state-manager"

    # Delete .terraform.lock.hcl to allow provider version changes
    lock_file_path = osp.join(terraform_dir, ".terraform.lock.hcl")
    try:
        remove(lock_file_path)
    except FileNotFoundError:
        pass

    # Update provider version
    with open(f"{terraform_dir}/terraform.tf", "w") as fp:
        fp.write(
            f"""
            terraform {{
                required_version = "~> 1.0"
                required_providers {{
                    aws = {{
                      source  = "hashicorp/aws"
                      version = "{aws_provider_version}"
                    }}
                  }}
                }}
            """
        )

    # Get AWS account ID
    sts = boto3_session.client("sts", region_name=aws_region)
    account_id = sts.get_caller_identity()["Account"]
    # Write test variables
    assuming_role_arn = (
        test_role_arn or f"arn:aws:iam::{account_id}:role/state-manager-tester"
    )

    with open(f"{terraform_dir}/terraform.tfvars", "w") as fp:
        fp.write(
            dedent(
                f"""
                assuming_role_arns = ["{assuming_role_arn}"]
                name = "{name}"
                read_only_permissions = {str(read_only).lower()}
                state_bucket = "test-state-bucket"
                state_key = "test/terraform.tfstate"
                terraform_locks_table_arn = "arn:aws:dynamodb:{aws_region}:{account_id}:table/terraform-locks"
                """
            )
        )
        fp.write(
            dedent(
                f"""
                region       = "{aws_region}"
                """
            )
        )
        if test_role_arn:
            fp.write(
                dedent(
                    f"""
                    role_arn     = "{test_role_arn}"
                    """
                )
            )

    with terraform_apply(
        terraform_dir, destroy_after=not keep_after, json_output=True
    ) as tf_output:
        LOG.info(json.dumps(tf_output, indent=4, default=str))

        # Verify outputs exist
        assert "state_manager_role_arn" in tf_output
        assert tf_output["state_manager_role_arn"]["value"].startswith("arn:aws:iam::")
        assert name.startswith(tf_output["state_manager_role_name"]["value"])


@pytest.mark.parametrize("aws_provider_version", ["~> 5.11", "~> 6.0"])
def test_module_defaults(
    aws_provider_version, aws_region, test_role_arn, keep_after, boto3_session
):
    """Test module with default values where applicable"""
    terraform_dir = f"{TERRAFORM_ROOT_DIR}/state-manager"

    # Delete .terraform.lock.hcl to allow provider version changes
    lock_file_path = osp.join(terraform_dir, ".terraform.lock.hcl")
    try:
        remove(lock_file_path)
    except FileNotFoundError:
        pass

    # Update provider version
    with open(f"{terraform_dir}/terraform.tf", "w") as fp:
        fp.write(
            f"""
            terraform {{
                required_version = "~> 1.0"
                required_providers {{
                    aws = {{
                      source  = "hashicorp/aws"
                      version = "{aws_provider_version}"
                    }}
                  }}
                }}
            """
        )

    # Get AWS account ID
    sts = boto3_session.client("sts", region_name=aws_region)
    account_id = sts.get_caller_identity()["Account"]

    # Write minimal required variables, let defaults take effect
    assuming_role_arn = (
        test_role_arn or f"arn:aws:iam::{account_id}:role/state-manager-tester"
    )
    with open(f"{terraform_dir}/terraform.tfvars", "w") as fp:
        fp.write(
            dedent(
                f"""
                assuming_role_arns = ["{assuming_role_arn}"]
                name = "state-manager-defaults"
                state_bucket = "test-state-bucket"
                terraform_locks_table_arn = "arn:aws:dynamodb:{aws_region}:{account_id}:table/terraform-locks"
                """
            )
        )
        fp.write(
            dedent(
                f"""
                region       = "{aws_region}"
                """
            )
        )
        if test_role_arn:
            fp.write(
                dedent(
                    f"""
                    role_arn     = "{test_role_arn}"
                    """
                )
            )

    with terraform_apply(
        terraform_dir, destroy_after=not keep_after, json_output=True
    ) as tf_output:
        LOG.info(json.dumps(tf_output, indent=4, default=str))

        # Verify outputs exist
        assert "state_manager_role_arn" in tf_output
        assert tf_output["state_manager_role_arn"]["value"].startswith("arn:aws:iam::")
        assert "state-manager-defaults" in tf_output["state_manager_role_arn"]["value"]
