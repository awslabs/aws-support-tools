'''
Unit tests for sns_reflect.

boto3 and botocore are replaced with stubs, so no AWS account or boto3
install is needed.

Run from this folder:  python -m pytest test_sns_reflect.py
'''
import importlib
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(__file__))


class FakeClientError(Exception):
    def __init__(self, error_response, operation_name):
        super().__init__('An error occurred (%s) when calling the %s operation'
                         % (error_response['Error']['Code'], operation_name))
        self.response = error_response


@pytest.fixture
def reflect(monkeypatch):
    monkeypatch.setenv('REGION', 'us-east-1')
    monkeypatch.setenv('TOPIC', 'arn:aws:sns:us-east-1:111122223333:Target')
    botocore = types.ModuleType('botocore')
    botocore.exceptions = types.SimpleNamespace(ClientError=FakeClientError)
    monkeypatch.setitem(sys.modules, 'botocore', botocore)
    monkeypatch.setitem(sys.modules, 'boto3', MagicMock())
    sys.modules.pop('sns_reflect', None)
    module = importlib.import_module('sns_reflect')
    yield module
    sys.modules.pop('sns_reflect', None)


def event(type_='Notification'):
    return {'Records': [{'Sns': {'Type': type_, 'Subject': 'hello', 'Message': 'body'}}]}


def test_notification_is_republished(reflect):
    reflect.lambda_handler(event(), None)
    reflect.sns.publish.assert_called_once_with(
        TopicArn='arn:aws:sns:us-east-1:111122223333:Target', Subject='hello', Message='body')


def test_non_notification_is_ignored(reflect):
    reflect.lambda_handler(event('SubscriptionConfirmation'), None)
    reflect.sns.publish.assert_not_called()


def test_client_error_is_logged_not_crashing(reflect, capsys):
    reflect.sns.publish.side_effect = FakeClientError(
        {'Error': {'Code': 'AuthorizationError'}, 'ResponseMetadata': {'HTTPStatusCode': 403}}, 'Publish')
    reflect.lambda_handler(event(), None)
    out = capsys.readouterr().out
    assert 'HTTPStatusCode=403' in out
    assert 'AuthorizationError' in out


def test_unexpected_error_is_reraised(reflect, capsys):
    with pytest.raises(KeyError):
        reflect.lambda_handler({'Records': [{}]}, None)
    assert 'Aborting...' in capsys.readouterr().out
