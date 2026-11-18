'''
Unit tests for NetworkingVerifier._check_access_blocked.

MWAA needs "Block all public access" on the source bucket (or account), which
means all four PublicAccessBlockConfiguration settings must be true. These
tests use stub clients, so no AWS account or moto is needed.

Run from the MWAA folder:  python -m pytest tests/test_s3_public_access_block.py
'''
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'verify_env'))

from networking_verifier import NetworkingVerifier  # noqa: E402

SETTINGS = ('BlockPublicAcls', 'IgnorePublicAcls', 'BlockPublicPolicy', 'RestrictPublicBuckets')


def make_verifier():
    verifier = NetworkingVerifier.__new__(NetworkingVerifier)
    verifier.report = MagicMock()
    return verifier


def client_returning(config):
    client = MagicMock()
    client.get_public_access_block.return_value = {'PublicAccessBlockConfiguration': config}
    return client


def test_all_settings_on_is_blocked():
    config = {name: True for name in SETTINGS}
    assert make_verifier()._check_access_blocked('bucket', client_returning(config), Bucket='b') is True


@pytest.mark.parametrize('off', SETTINGS)
def test_any_setting_off_is_not_blocked(off):
    config = {name: name != off for name in SETTINGS}
    assert make_verifier()._check_access_blocked('bucket', client_returning(config), Bucket='b') is False


def test_only_block_public_acls_on_is_not_blocked():
    # A public bucket policy is still allowed here, so the bucket is not fully blocked.
    config = {'BlockPublicAcls': True, 'IgnorePublicAcls': False,
              'BlockPublicPolicy': False, 'RestrictPublicBuckets': False}
    assert make_verifier()._check_access_blocked('bucket', client_returning(config), Bucket='b') is False
