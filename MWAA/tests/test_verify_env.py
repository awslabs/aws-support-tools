import argparse
import boto3
import os
import pytest

from moto import mock_s3
from verify_env import verify_env

@pytest.fixture
def env_info():
    '''
    Create the minimal env info needed for testing.
    At the moment only s3 public access tests are using this fixture
    '''
    return {'SourceBucketArn': TEST_BUCKET_ARN,
            'Arn': TEST_ACCOUNT_ARN}


def test_verify_boto3():
    '''
    test version equal to 1.16.25
    test various version numbers below
    '''
    assert verify_env.verify_boto3('1.17.4')
    assert verify_env.verify_boto3('1.17.33')
    assert verify_env.verify_boto3('1.16.27')
    assert verify_env.verify_boto3('1.16.26')
    assert verify_env.verify_boto3('1.16.25')
    assert not verify_env.verify_boto3('1.16.24')
    assert not verify_env.verify_boto3('1.16.23')
    assert not verify_env.verify_boto3('1.16.22')
    assert not verify_env.verify_boto3('1.16.21')
    assert not verify_env.verify_boto3('1.7.65')
    assert not verify_env.verify_boto3('1.9.105')
    assert not verify_env.verify_boto3('1.10.33')


def test_validation_region():
    '''
    test various inputs for regions and all valid MWAA regions
    https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/
    '''
    regions = [
        'us-east-2',
        'us-east-1',
        'us-west-2',
        'ap-southeast-1',
        'ap-southeast-2',
        'ap-northeast-1',
        'eu-central-1',
        'eu-west-1',
        'eu-north-1'
    ]
    for region in regions:
        assert verify_env.validation_region(region) == region
    unsupport_regions = [
        'us-west-1',
        'af-south-1',
        'ap-east-1',
        'ap-south-1',
        'ap-northeast-3',
        'ap-northeast-2',
        'ca-central-1',
        'eu-west-2',
        'eu-south-1',
        'eu-west-3',
        'me-sourth-1',
        'sa-east-1'
    ]
    for unsupport_region in unsupport_regions:
        with pytest.raises(argparse.ArgumentTypeError) as excinfo:
            verify_env.validation_region(unsupport_region)
        assert ("%s is an invalid REGION value" % unsupport_region) in str(excinfo.value)
    bad_regions = [
        'us-east-11',
        'us-west-3',
        'eu-wheat-3'
    ]
    for region in bad_regions:
        with pytest.raises(argparse.ArgumentTypeError) as excinfo:
            verify_env.validation_region(region)
        assert ("%s is an invalid REGION value" % region) in str(excinfo.value)


def test_validate_envname():
    '''
    test invalid and valid names for MWAA environment
    '''
    with pytest.raises(argparse.ArgumentTypeError) as excinfo:
        env_name = '42'
        verify_env.validate_envname(env_name)
    assert ("%s is an invalid environment name value" % env_name) in str(excinfo.value)
    env_name = 'test'
    result = verify_env.validate_envname(env_name)
    assert result == env_name


def test_validate_profile():
    '''
    test invalid and valid names for the profile
    '''
    with pytest.raises(argparse.ArgumentTypeError) as excinfo:
        profile_name = 'test space'
        verify_env.validation_profile(profile_name)
    assert ("%s is an invalid profile name value" % profile_name) in str(excinfo.value)
    profile_name = 'test'
    result = verify_env.validation_profile(profile_name)
    assert result == profile_name
    profile_name = '42'
    result = verify_env.validation_profile(profile_name)
    assert result == profile_name
    profile_name = '4HelloWorld2'
    result = verify_env.validation_profile(profile_name)
    assert result == profile_name
    profile_name = 'HelloWorld'
    result = verify_env.validation_profile(profile_name)
    assert result == profile_name
    profile_name = '_HelloWorld'
    result = verify_env.validation_profile(profile_name)
    assert result == profile_name
    profile_name = 'Hello-World'
    result = verify_env.validation_profile(profile_name)
    assert result == profile_name


def test_check_ingress_acls():
    '''
    Goes through the following scenarios
    * if no acls are passed
    * if there is an allow
    * if there is a deny but no allow
    '''
    acls = []
    src_port_from = 5432
    src_port_to = 5432
    result = verify_env.check_ingress_acls(acls, src_port_from, src_port_to)
    assert result == ''
    acls = [
        {
            'CidrBlock': '0.0.0.0/0',
            'Egress': False,
            'Protocol': '-1',
            'RuleAction': 'allow',
            'RuleNumber': 1
        },
        {
            'CidrBlock': '0.0.0.0/0',
            'Egress': False,
            'Protocol': '-1',
            'RuleAction': 'deny',
            'RuleNumber': 32767
        }
    ]
    result = verify_env.check_ingress_acls(acls, src_port_from, src_port_to)
    assert result
    acls = [
        {
            'CidrBlock': '0.0.0.0/0',
            'Egress': False,
            'Protocol': '-1',
            'RuleAction': 'deny',
            'RuleNumber': 32767
        }
    ]
    result = verify_env.check_ingress_acls(acls, src_port_from, src_port_to)
    assert not result


def test_check_egress_acls():
    '''
    Goes through the following scenarios
    * if no acls are passed
    * if there is an allow
    * if there is a deny but no allow
    '''
    acls = []
    dest_port = 5432
    result = verify_env.check_egress_acls(acls, dest_port)
    assert result == ''
    acls = [
        {
            'CidrBlock': '0.0.0.0/0',
            'Egress': False,
            'Protocol': '-1',
            'RuleAction': 'allow',
            'RuleNumber': 1
        },
        {
            'CidrBlock': '0.0.0.0/0',
            'Egress': False,
            'Protocol': '-1',
            'RuleAction': 'deny',
            'RuleNumber': 32767
        }
    ]
    result = verify_env.check_egress_acls(acls, dest_port)
    assert result
    acls = [
        {
            'CidrBlock': '0.0.0.0/0',
            'Egress': False,
            'Protocol': '-1',
            'RuleAction': 'deny',
            'RuleNumber': 32767
        }
    ]
    result = verify_env.check_egress_acls(acls, dest_port)
    assert not result

# S3 public access tests

TEST_BUCKET_NAME = 'TestBucket'
TEST_BUCKET_ARN = 'arn:aws:s3:::' + TEST_BUCKET_NAME
TEST_ACCOUNT_REGION = 'us-east-1'
TEST_ACCOUNT_ID = os.getenv('MOTO_ACCOUNT_ID')
assert TEST_ACCOUNT_ID, "Please export a moto account id, see README for details"
TEST_ACCOUNT_PARTITION = 'aws'
TEST_ACCOUNT_ARN = ('arn:{partition}:airflow:{region}:{account_id}:environment/TestEnv'
                    .format(region=TEST_ACCOUNT_REGION,
                            account_id=TEST_ACCOUNT_ID,
                            partition=TEST_ACCOUNT_PARTITION))
# Configuration for test cases to be iterated through by pytest.mark.parameterize.
# Each test case includes the settings for bucket and account level public
# access config (True=public access is blocked, False=not blocked, None=no config is set
# at all) as well as the expected output to compare with.
# Public access must be blocked by at least one of either bucket or account, if
# not, the test is a failure case.
TEST_CASES = [
    # Happy cases
    (True, True, verify_env.S3_CHECK_SUCCESS_MSG),
    (True, False, verify_env.S3_CHECK_SUCCESS_MSG),
    (True, None, verify_env.S3_CHECK_SUCCESS_MSG),
    (False, True, verify_env.S3_CHECK_SUCCESS_MSG),
    (None, True, verify_env.S3_CHECK_SUCCESS_MSG),
    # Unhappy cases
    (False, False, verify_env.S3_CHECK_FAILURE_MSG),
    (None, False, verify_env.S3_CHECK_FAILURE_MSG),
    (False, None, verify_env.S3_CHECK_FAILURE_MSG),
    (None, None, verify_env.S3_CHECK_FAILURE_MSG)
]


def create_public_access_config(is_blocked):
    return {
        'BlockPublicAcls': is_blocked,
        'IgnorePublicAcls': is_blocked,
        'BlockPublicPolicy': is_blocked,
        'RestrictPublicBuckets': is_blocked
    }


@pytest.fixture(scope="function")
def init_s3():
    '''
    Init the "virtual" moto aws account. Create the buckets and set access
    permisions
    '''
    @mock_s3
    def _init_s3(is_bucket_access_blocked, is_account_access_blocked):
        s3_client = boto3.client('s3', region_name=TEST_ACCOUNT_REGION)
        s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)

        if is_bucket_access_blocked is not None:
            s3_client.put_public_access_block(
                Bucket=TEST_BUCKET_NAME,
                PublicAccessBlockConfiguration=create_public_access_config(
                    is_blocked=is_bucket_access_blocked
                )
            )

        s3_control_client = boto3.client('s3control', region_name=TEST_ACCOUNT_REGION)
        if is_account_access_blocked is not None:
            s3_control_client.put_public_access_block(
                AccountId=TEST_ACCOUNT_ID,
                PublicAccessBlockConfiguration=create_public_access_config(
                    is_blocked=is_account_access_blocked
                )
            )

        return s3_client, s3_control_client

    return _init_s3


@mock_s3
# Iterate over test cases defined above
@pytest.mark.parametrize("is_bucket_access_blocked,is_account_access_blocked,expected", TEST_CASES)
def test_s3_public_access_block(init_s3, env_info, capfd, is_bucket_access_blocked,
                                is_account_access_blocked, expected):
    s3_client, s3_control_client = init_s3(is_bucket_access_blocked=is_bucket_access_blocked,
                                           is_account_access_blocked=is_account_access_blocked)

    verify_env.check_s3_block_public_access(env_info,
                                            s3_client,
                                            s3_control_client)
    out, _ = capfd.readouterr()

    assert expected.format(bucket_arn=TEST_BUCKET_ARN) in out
