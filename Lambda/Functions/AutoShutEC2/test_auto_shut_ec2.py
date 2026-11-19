'''
Unit tests for auto_shut_ec2.look_for_instances.

boto3 is replaced with a stub, so no AWS account or boto3 install is needed,
and no instance is ever stopped.

Run from this folder:  python -m pytest test_auto_shut_ec2.py
'''
import importlib
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(__file__))


def running(instance_id, tags=None):
    instance = {'InstanceId': instance_id, 'State': {'Name': 'running'}}
    if tags is not None:
        instance['Tags'] = tags
    return instance


@pytest.fixture
def run_with(monkeypatch):
    def _run(instances):
        boto3 = MagicMock()
        boto3.client.return_value.describe_regions.return_value = {'Regions': [{'RegionName': 'us-east-1'}]}
        boto3.client.return_value.describe_instances.return_value = {'Reservations': [{'Instances': instances}]}
        monkeypatch.setitem(sys.modules, 'boto3', boto3)
        sys.modules.pop('auto_shut_ec2', None)
        module = importlib.import_module('auto_shut_ec2')
        module.look_for_instances()
        stopped = [c.args[0] for c in boto3.resource.return_value.Instance.call_args_list]
        sys.modules.pop('auto_shut_ec2', None)
        return stopped
    return _run


def test_instance_without_noshut_tag_is_stopped(run_with):
    assert run_with([running('i-1', [{'Key': 'Name', 'Value': 'web'}])]) == ['i-1']


def test_instance_with_noshut_tag_is_not_stopped(run_with):
    tags = [{'Key': 'Name', 'Value': 'web'}, {'Key': 'noshut', 'Value': ''}]
    assert run_with([running('i-1', tags)]) == []


def test_noshut_in_tag_value_is_respected(run_with):
    assert run_with([running('i-1', [{'Key': 'Policy', 'Value': 'noshut'}])]) == []


def test_instance_with_no_tags_is_stopped(run_with):
    # describe_instances omits 'Tags' entirely for untagged instances
    assert run_with([running('i-1')]) == ['i-1']


def test_stopped_instances_are_ignored(run_with):
    instance = {'InstanceId': 'i-1', 'State': {'Name': 'stopped'}}
    assert run_with([instance]) == []
