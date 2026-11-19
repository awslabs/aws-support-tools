import argparse
from unittest.mock import MagicMock

import pytest

from verify_env import verify_env
from verify_env.networking_verifier import NetworkingVerifier


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


def test_validation_region(monkeypatch):
    '''
    test various inputs for regions and all valid MWAA regions
    https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/
    '''
    regions = [
        'ap-northeast-1',
        'ap-northeast-2',
        'ap-south-1',
        'ap-southeast-1',
        'ap-southeast-2',
        'ca-central-1',
        'eu-central-1',
        'eu-north-1',
        'eu-west-1',
        'eu-west-2',
        'eu-west-3',
        'sa-east-1',
        'us-east-1',
        'us-east-2',
        'us-west-2'
    ]
    # Pin the list botocore reports as MWAA regions, so the test does not
    # change behaviour as AWS adds MWAA regions to newer botocore releases.
    monkeypatch.setattr('boto3.session.Session.get_available_regions',
                        lambda self, service, partition: regions)
    for region in regions:
        assert verify_env.validation_region(region) == region
    unsupport_regions = [
        'us-west-1',
        'af-south-1',
        'ap-east-1',
        'ap-northeast-3',
        'eu-south-1',
        'me-south-1',
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
    test invalid and valid names for AWS configuration and credential file profiles
    '''
    allowed = ["test", "Hello_-_World2", "1Test_2-3", "123", "Test"]
    for profile_name in allowed:
        result = verify_env.validation_profile(profile_name)
        assert result == profile_name

    not_allowed = ["test space", "test/test", "test\ntest", "test&test", "test.py", " ", ""]
    for profile_name in not_allowed:
        with pytest.raises(argparse.ArgumentTypeError) as excinfo:
            verify_env.validation_profile(profile_name)
        assert ("%s is an invalid profile name value" % profile_name) in str(excinfo.value)


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
    result = NetworkingVerifier._check_ingress_acls(acls, src_port_from, src_port_to)
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
    result = NetworkingVerifier._check_ingress_acls(acls, src_port_from, src_port_to)
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
    result = NetworkingVerifier._check_ingress_acls(acls, src_port_from, src_port_to)
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
    result = NetworkingVerifier._check_egress_acls(acls, dest_port)
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
    result = NetworkingVerifier._check_egress_acls(acls, dest_port)
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
    result = NetworkingVerifier._check_egress_acls(acls, dest_port)
    assert not result


def _port_acl(action, port, egress=False):
    return {
        'CidrBlock': '0.0.0.0/0',
        'Egress': egress,
        'Protocol': '6',
        'PortRange': {'From': port, 'To': port},
        'RuleAction': action,
        'RuleNumber': 100,
    }


def test_check_ingress_acls_matches_the_requested_port_only():
    '''
    A rule for a different port must not be treated as a match for 5432, and a
    rule for exactly 5432 must be.
    '''
    assert NetworkingVerifier._check_ingress_acls([_port_acl('allow', 80)], 5432, 5432) == ''
    assert NetworkingVerifier._check_ingress_acls([_port_acl('deny', 22)], 5432, 5432) == ''
    assert NetworkingVerifier._check_ingress_acls([_port_acl('allow', 5432)], 5432, 5432) is True
    assert NetworkingVerifier._check_ingress_acls([_port_acl('deny', 5432)], 5432, 5432) is False


def _check_nacl_report(egress_action, ingress_action):
    '''Run check_nacl against one NACL and return everything it reported.'''
    verifier = NetworkingVerifier.__new__(NetworkingVerifier)
    verifier.report = MagicMock()
    verifier.ec2 = MagicMock()
    verifier.ec2.describe_network_acls.return_value = {'NetworkAcls': [{
        'NetworkAclId': 'acl-1',
        'Entries': [_port_acl(egress_action, 5432, egress=True),
                    _port_acl(ingress_action, 5432)],
    }]}
    verifier.check_nacl([{'VpcId': 'vpc-1'}], ['subnet-1'])
    calls = (verifier.report.write_all_locations.call_args_list +
             verifier.report.write_full_report.call_args_list)
    return ' '.join(' '.join(str(arg) for arg in call.args) for call in calls)


def test_check_nacl_reports_issue_when_port_is_denied():
    output = _check_nacl_report('allow', 'deny')
    assert 'denied port 5432 on ingress' in output
    assert 'Please investigate the nacl issue.' in output
    assert 'All nacls are as expected.' not in output


def test_check_nacl_reports_ok_when_port_is_allowed():
    output = _check_nacl_report('allow', 'allow')
    assert 'All nacls are as expected.' in output
    assert 'Please investigate the nacl issue.' not in output
