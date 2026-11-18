'''
Unit tests for check_ses_quota.check_quota.

ALERT_THRESHOLD comes from a Lambda environment variable, so it arrives as a
string. These tests make sure it is compared as a number. boto3 is replaced
with a stub, so no AWS account or boto3 install is needed.

Run from this folder:  python -m pytest test_check_ses_quota.py
'''
import importlib
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture
def quota_module(monkeypatch):
    monkeypatch.setenv('REGION', 'us-east-1')
    monkeypatch.setenv('ALERT_THRESHOLD', '80')
    monkeypatch.setenv('TOPIC', 'arn:aws:sns:us-east-1:111122223333:MyTopic')
    monkeypatch.setitem(sys.modules, 'boto3', MagicMock())
    sys.modules.pop('check_ses_quota', None)
    module = importlib.import_module('check_ses_quota')
    yield module
    sys.modules.pop('check_ses_quota', None)


def set_quota(module, max_send, sent):
    client = module.boto3.client.return_value
    client.get_send_quota.return_value = {'Max24HourSend': max_send, 'SentLast24Hours': sent}
    client.publish.return_value = {'MessageId': 'test-id'}
    return client


def test_threshold_is_numeric(quota_module):
    assert quota_module.alert_threshold == 80.0


def test_over_threshold_publishes_alert(quota_module):
    client = set_quota(quota_module, 200.0, 190.0)  # 95% used
    result = quota_module.check_quota()
    assert 'threshold of 95% has been reached' in result
    client.publish.assert_called_once()


def test_under_threshold_does_not_publish(quota_module):
    client = set_quota(quota_module, 200.0, 50.0)  # 25% used
    assert quota_module.check_quota() == 'Sending quota within threshold.'
    client.publish.assert_not_called()
