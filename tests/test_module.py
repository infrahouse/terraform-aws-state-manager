from os import path as osp, remove
import json
from textwrap import dedent
from time import sleep
from typing import Dict, List, Optional

import boto3
import pytest
from botocore.exceptions import ClientError
from infrahouse_core.timeout import timeout
from pytest_infrahouse import terraform_apply

from tests.conftest import LOG, TERRAFORM_ROOT_DIR


def _write_provider_version(terraform_dir: str, aws_provider_version: str) -> None:
    """Write terraform.tf with the specified provider version."""
    lock_file_path = osp.join(terraform_dir, ".terraform.lock.hcl")
    try:
        remove(lock_file_path)
    except FileNotFoundError:
        pass

    with open(f"{terraform_dir}/terraform.tf", "w") as fp:
        fp.write(dedent(f"""\
                terraform {{
                    required_version = "~> 1.0"
                    required_providers {{
                        aws = {{
                          source  = "hashicorp/aws"
                          version = "{aws_provider_version}"
                        }}
                      }}
                    }}
                """))


def _write_tfvars(
    terraform_dir: str,
    aws_region: str,
    test_role_arn: Optional[str],
    name: str,
    assuming_role_arns: List[str],
    assuming_role_patterns: Optional[List[str]] = None,
    read_only: bool = False,
) -> None:
    """Write terraform.tfvars for a test run."""
    arns_str = ", ".join(f'"{a}"' for a in assuming_role_arns)

    with open(f"{terraform_dir}/terraform.tfvars", "w") as fp:
        fp.write(dedent(f"""\
                assuming_role_arns = [{arns_str}]
                environment = "development"
                name = "{name}"
                read_only_permissions = {str(read_only).lower()}
                region = "{aws_region}"
                """))
        if assuming_role_patterns is not None:
            patterns_str = ", ".join(f'"{p}"' for p in assuming_role_patterns)
            fp.write(f'assuming_role_patterns = [{patterns_str}]\n')
        if test_role_arn:
            fp.write(f'role_arn = "{test_role_arn}"\n')


def _assume_role_via_session(
    session: boto3.Session,
    role_arn: str,
    aws_region: str,
    session_name: str,
    wait_timeout: int = 30,
) -> boto3.Session:
    """
    Assume a role using an existing boto3 session, with retries.

    :param session: Authenticated boto3 session to assume from.
    :param role_arn: ARN of the role to assume.
    :param aws_region: AWS region.
    :param session_name: STS session name.
    :param wait_timeout: Timeout in seconds for IAM propagation retries.
    :return: A new boto3.Session authenticated as the assumed role.
    """
    sts = session.client("sts", region_name=aws_region)
    sleep_time = 2
    with timeout(seconds=wait_timeout):
        while True:
            try:
                assumed = sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName=session_name,
                )
                return boto3.Session(
                    aws_access_key_id=assumed["Credentials"]["AccessKeyId"],
                    aws_secret_access_key=assumed["Credentials"]["SecretAccessKey"],
                    aws_session_token=assumed["Credentials"]["SessionToken"],
                )
            except ClientError as exc:
                if exc.response["Error"]["Code"] == "AccessDenied":
                    LOG.info(
                        "Assume role %s failed (IAM propagation), retrying in %ds",
                        role_arn,
                        sleep_time,
                    )
                    sleep(sleep_time)
                    sleep_time *= 2
                else:
                    raise


def _get_state_manager_session(
    boto3_session: boto3.Session,
    aws_region: str,
    probe_role: Dict,
    state_manager_role_arn: str,
) -> boto3.Session:
    """
    Assume state-manager role via probe role chain.

    boto3_session (test role) -> probe role -> state-manager role.

    :param boto3_session: The test session (state-manager-tester).
    :param aws_region: AWS region.
    :param probe_role: Output from the probe_role fixture.
    :param state_manager_role_arn: ARN of the state-manager role to assume.
    :return: A boto3.Session authenticated as the state-manager role.
    """
    probe_role_arn = probe_role["role_arn"]["value"]

    probe_session = _assume_role_via_session(
        boto3_session, probe_role_arn, aws_region, "probe-session"
    )
    return _assume_role_via_session(
        probe_session, state_manager_role_arn, aws_region, "sm-permission-test"
    )


def _check_rw_permissions(s3, dynamodb, bucket_name: str, table_name: str) -> None:
    """Exercise all RW operations on S3 and DynamoDB."""
    response = s3.list_objects_v2(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    LOG.info("ListBucket on %s: OK", bucket_name)

    s3.put_object(Bucket=bucket_name, Key="terraform.tfstate", Body=b"test-state-data")
    LOG.info("PutObject terraform.tfstate: OK")

    response = s3.get_object(Bucket=bucket_name, Key="terraform.tfstate")
    assert response["Body"].read() == b"test-state-data"
    LOG.info("GetObject terraform.tfstate: OK")

    s3.delete_object(Bucket=bucket_name, Key="terraform.tfstate")
    LOG.info("DeleteObject terraform.tfstate: OK")

    dynamodb.describe_table(TableName=table_name)
    LOG.info("DescribeTable %s: OK", table_name)

    dynamodb.put_item(TableName=table_name, Item={"LockID": {"S": "test-lock-id"}})
    LOG.info("PutItem: OK")

    response = dynamodb.get_item(
        TableName=table_name, Key={"LockID": {"S": "test-lock-id"}}
    )
    assert response["Item"]["LockID"]["S"] == "test-lock-id"
    LOG.info("GetItem: OK")

    dynamodb.delete_item(
        TableName=table_name, Key={"LockID": {"S": "test-lock-id"}}
    )
    LOG.info("DeleteItem: OK")


def _check_ro_permissions(
    s3, dynamodb, boto3_session, aws_region, bucket_name: str, table_name: str
) -> None:
    """Verify RO role can read but not write."""
    response = s3.list_objects_v2(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    LOG.info("ListBucket on %s: OK", bucket_name)

    test_s3 = boto3_session.client("s3", region_name=aws_region)
    test_s3.put_object(
        Bucket=bucket_name, Key="terraform.tfstate", Body=b"ro-test-state"
    )
    LOG.info("Seeded terraform.tfstate via test session")

    response = s3.get_object(Bucket=bucket_name, Key="terraform.tfstate")
    assert response["Body"].read() == b"ro-test-state"
    LOG.info("GetObject terraform.tfstate: OK (read-only role)")

    with pytest.raises(ClientError) as exc_info:
        s3.put_object(
            Bucket=bucket_name, Key="terraform.tfstate", Body=b"should-fail"
        )
    assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
    LOG.info("PutObject correctly denied for read-only role")

    with pytest.raises(ClientError) as exc_info:
        dynamodb.describe_table(TableName=table_name)
    assert exc_info.value.response["Error"]["Code"] == "AccessDeniedException"
    LOG.info("DynamoDB correctly denied for read-only role")

    test_s3.delete_object(Bucket=bucket_name, Key="terraform.tfstate")
    LOG.info("Cleaned up seeded terraform.tfstate")


def _verify_permissions(
    boto3_session: boto3.Session,
    aws_region: str,
    probe_role: Dict,
    tf_output: Dict,
    read_only: bool = False,
) -> None:
    """
    Verify granted permissions by performing actual AWS operations.

    Assumes state-manager role via probe_role chain, then exercises
    S3 and DynamoDB permissions against real resources.

    :param boto3_session: The test session (state-manager-tester).
    :param aws_region: AWS region.
    :param probe_role: Output from the probe_role fixture.
    :param tf_output: Terraform output dictionary.
    :param read_only: Whether the role has read-only permissions.
    """
    role_arn = tf_output["state_manager_role_arn"]["value"]
    bucket_name = tf_output["state_bucket"]["value"]
    table_name = tf_output["locks_table_name"]["value"]

    sm_session = _get_state_manager_session(
        boto3_session, aws_region, probe_role, role_arn
    )

    s3 = sm_session.client("s3", region_name=aws_region)
    dynamodb = sm_session.client("dynamodb", region_name=aws_region)

    # Retry for IAM policy propagation — any action can fail until
    # all policy attachments have propagated.
    sleep_time = 2
    with timeout(seconds=60):
        while True:
            try:
                if not read_only:
                    _check_rw_permissions(s3, dynamodb, bucket_name, table_name)
                else:
                    _check_ro_permissions(
                        s3, dynamodb, boto3_session, aws_region,
                        bucket_name, table_name,
                    )
                break
            except ClientError as exc:
                code = exc.response["Error"]["Code"]
                if code in ("AccessDenied", "AccessDeniedException"):
                    LOG.info(
                        "Permission check failed (%s, IAM propagation), retrying in %ds",
                        code,
                        sleep_time,
                    )
                    sleep(sleep_time)
                    sleep_time = min(sleep_time * 2, 10)
                else:
                    raise


@pytest.mark.parametrize("aws_provider_version", ["~> 6.0"], ids=["aws-6"])
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
    ids=["rw", "ro", "long-name"],
)
def test_module(
    aws_provider_version,
    name,
    read_only,
    aws_region,
    test_role_arn,
    keep_after,
    boto3_session,
    probe_role,
):
    terraform_dir = f"{TERRAFORM_ROOT_DIR}/state-manager"

    _write_provider_version(terraform_dir, aws_provider_version)

    probe_role_arn = probe_role["role_arn"]["value"]

    _write_tfvars(
        terraform_dir,
        aws_region,
        test_role_arn,
        name,
        assuming_role_arns=[probe_role_arn],
        read_only=read_only,
    )

    with terraform_apply(
        terraform_dir, destroy_after=not keep_after, json_output=True
    ) as tf_output:
        LOG.info(json.dumps(tf_output, indent=4, default=str))

        assert "state_manager_role_arn" in tf_output
        assert tf_output["state_manager_role_arn"]["value"].startswith("arn:aws:iam::")
        assert name.startswith(tf_output["state_manager_role_name"]["value"])

        _verify_permissions(
            boto3_session, aws_region, probe_role, tf_output, read_only=read_only
        )


@pytest.mark.parametrize("aws_provider_version", ["~> 6.0"], ids=["aws-6"])
def test_module_defaults(
    aws_provider_version,
    aws_region,
    test_role_arn,
    keep_after,
    boto3_session,
    probe_role,
):
    """Test module with default values where applicable."""
    terraform_dir = f"{TERRAFORM_ROOT_DIR}/state-manager"

    _write_provider_version(terraform_dir, aws_provider_version)

    probe_role_arn = probe_role["role_arn"]["value"]

    _write_tfvars(
        terraform_dir,
        aws_region,
        test_role_arn,
        "state-manager-defaults",
        assuming_role_arns=[probe_role_arn],
    )

    with terraform_apply(
        terraform_dir, destroy_after=not keep_after, json_output=True
    ) as tf_output:
        LOG.info(json.dumps(tf_output, indent=4, default=str))

        assert "state_manager_role_arn" in tf_output
        assert tf_output["state_manager_role_arn"]["value"].startswith("arn:aws:iam::")
        assert "state-manager-defaults" in tf_output["state_manager_role_arn"]["value"]

        _verify_permissions(boto3_session, aws_region, probe_role, tf_output)


@pytest.mark.parametrize("aws_provider_version", ["~> 5.11"], ids=["aws-5"])
def test_module_aws5_compat(
    aws_provider_version,
    aws_region,
    test_role_arn,
    keep_after,
    boto3_session,
    probe_role,
):
    """Test backward compatibility with AWS provider 5.x."""
    terraform_dir = f"{TERRAFORM_ROOT_DIR}/state-manager"

    _write_provider_version(terraform_dir, aws_provider_version)

    probe_role_arn = probe_role["role_arn"]["value"]

    _write_tfvars(
        terraform_dir,
        aws_region,
        test_role_arn,
        "state-manager-aws5-compat",
        assuming_role_arns=[probe_role_arn],
    )

    with terraform_apply(
        terraform_dir, destroy_after=not keep_after, json_output=True
    ) as tf_output:
        LOG.info(json.dumps(tf_output, indent=4, default=str))

        assert "state_manager_role_arn" in tf_output
        assert tf_output["state_manager_role_arn"]["value"].startswith("arn:aws:iam::")

        _verify_permissions(boto3_session, aws_region, probe_role, tf_output)


@pytest.mark.parametrize("aws_provider_version", ["~> 6.0"], ids=["aws-6"])
def test_module_wildcard(
    aws_provider_version,
    aws_region,
    test_role_arn,
    keep_after,
    boto3_session,
    probe_role,
):
    """Test assuming_role_patterns with wildcard principal matching."""
    terraform_dir = f"{TERRAFORM_ROOT_DIR}/state-manager"

    _write_provider_version(terraform_dir, aws_provider_version)

    probe_role_arn = probe_role["role_arn"]["value"]
    probe_role_pattern = probe_role_arn.rsplit("-", 1)[0] + "-*"

    sts = boto3_session.client("sts", region_name=aws_region)
    caller_arn = sts.get_caller_identity()["Arn"]
    # Resolve full role ARN via IAM — assumed-role ARNs strip the
    # IAM path (e.g. SSO's aws-reserved/sso.amazonaws.com/<region>/)
    # so reconstructing from the ARN string gives an invalid principal.
    if ":assumed-role/" in caller_arn:
        role_name = caller_arn.split(":")[5].split("/")[1]
        iam = boto3_session.client("iam", region_name=aws_region)
        caller_role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]
    else:
        caller_role_arn = caller_arn

    _write_tfvars(
        terraform_dir,
        aws_region,
        test_role_arn,
        "state-manager-wildcard",
        assuming_role_arns=[caller_role_arn],
        assuming_role_patterns=[probe_role_pattern],
    )

    with terraform_apply(
        terraform_dir, destroy_after=not keep_after, json_output=True
    ) as tf_output:
        LOG.info(json.dumps(tf_output, indent=4, default=str))

        assert "state_manager_role_arn" in tf_output
        assert tf_output["state_manager_role_arn"]["value"].startswith("arn:aws:iam::")

        _verify_permissions(boto3_session, aws_region, probe_role, tf_output)
