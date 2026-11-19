'''
Unit tests for sns_fast_publish.

boto3 and botocore are replaced with stubs, so no AWS account or boto3
install is needed.

Run from this folder:  python -m pytest test_sns_fast_publish.py
'''
import gzip
import importlib
import io
import json
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(__file__))

ENDPOINT = 'arn:aws:sns:us-west-2:111122223333:endpoint/GCM/MyApp/abc'


class FakeClientError(Exception):
    def __init__(self, error_response, operation_name):
        super().__init__('An error occurred (%s) when calling the %s operation'
                         % (error_response['Error']['Code'], operation_name))
        self.response = error_response


def load(monkeypatch, threads='4', log_time='0'):
    monkeypatch.setenv('REGION', 'us-east-1')
    monkeypatch.setenv('THREADS', threads)
    monkeypatch.setenv('LOG_TIME', log_time)
    botocore = types.ModuleType('botocore')
    botocore.exceptions = types.SimpleNamespace(ClientError=FakeClientError)
    monkeypatch.setitem(sys.modules, 'botocore', botocore)
    monkeypatch.setitem(sys.modules, 'boto3', MagicMock())
    sys.modules.pop('sns_fast_publish', None)
    return importlib.import_module('sns_fast_publish')


def s3_event(key):
    return {'Records': [{'s3': {'bucket': {'name': 'my-bucket'}, 'object': {'key': key}}}]}


def gzipped(payload):
    return io.BytesIO(gzip.compress(json.dumps(payload).encode()))


@pytest.fixture(autouse=True)
def cleanup():
    yield
    sys.modules.pop('sns_fast_publish', None)


def test_env_vars_are_parsed(monkeypatch):
    module = load(monkeypatch, threads='8', log_time='0')
    assert module.max_threads == 8
    assert module.log_time is False
    assert load(monkeypatch, log_time='1').log_time is True


def test_handler_publishes_and_decodes_key(monkeypatch):
    module = load(monkeypatch)
    module.s3.get_object.return_value = {'Body': gzipped(
        {'Endpoints': [{'EndpointArn': ENDPOINT, 'Message': 'hi'}]})}
    module.lambda_handler(s3_event('endpoint+list%281%29.json.gz'), None)
    module.s3.get_object.assert_called_once_with(Bucket='my-bucket', Key='endpoint list(1).json.gz')
    module.sns.publish.assert_called_once_with(
        TargetArn=ENDPOINT, Message='{"GCM": "hi"}', MessageStructure='json')


def test_client_error_is_recorded(monkeypatch):
    module = load(monkeypatch)
    module.sns.publish.side_effect = FakeClientError(
        {'Error': {'Code': 'EndpointDisabled'}, 'ResponseMetadata': {'HTTPStatusCode': 400}}, 'Publish')
    module.publish({'EndpointArn': ENDPOINT, 'Message': 'hi'})
    assert len(module.publish_errors) == 1
    assert 'HTTPStatusCode=400' in module.publish_errors[0]
    assert 'EndpointDisabled' in module.publish_errors[0]
