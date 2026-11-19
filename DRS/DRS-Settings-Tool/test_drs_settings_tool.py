'''
Unit tests for the DRS Settings Tool.

boto3 and botocore are replaced with stubs, so no AWS account or boto3
install is needed and no AWS resources are touched.

Run from this folder:  python -m pytest test_drs_settings_tool.py
'''
import csv
import importlib
import logging
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOL_DIR)


class FakeClientError(Exception):
    pass


@pytest.fixture(autouse=True)
def stub_aws(monkeypatch):
    boto3 = types.ModuleType('boto3')
    boto3.client = MagicMock(side_effect=lambda service: MagicMock(name=service))
    botocore = types.ModuleType('botocore')
    botocore.exceptions = types.SimpleNamespace(ClientError=FakeClientError)
    botocore.client = types.SimpleNamespace(BaseClient=object)
    monkeypatch.setitem(sys.modules, 'boto3', boto3)
    monkeypatch.setitem(sys.modules, 'botocore', botocore)
    monkeypatch.setitem(sys.modules, 'botocore.exceptions', botocore.exceptions)
    for name in list(sys.modules):
        if name.split('.')[0] in ('classes', 'object_builders', 'utils', 'get_settings', 'update_settings'):
            monkeypatch.delitem(sys.modules, name)
    yield


def load(module):
    return importlib.import_module(module)


# --- Paths and logging -----------------------------------------------------

def test_tool_path_and_csv_paths_work_on_any_os():
    logger_module = load('utils.logger')
    csv_settings = load('utils.csv_settings')
    assert logger_module.path == TOOL_DIR
    assert csv_settings.SETTINGS_CSV == os.path.join(TOOL_DIR, 'DRS_Settings.csv')
    assert csv_settings.ORIGINAL_SETTINGS_CSV == os.path.join(TOOL_DIR, 'DRS_Settings-DO_NOT_EDIT.csv')


def test_logger_does_not_add_duplicate_console_handlers():
    logger_module = load('utils.logger')
    first = logger_module.get_logger('TEST-DUP')
    second = logger_module.get_logger('TEST-DUP')
    assert first is second
    assert len(first.handlers) == 1


def test_logger_does_not_record_debug_output(monkeypatch):
    logger_module = load('utils.logger')
    basic_config = MagicMock()
    monkeypatch.setattr(logger_module.logging, 'basicConfig', basic_config)
    logger_module.get_logger('TEST-LEVEL')
    # NOTSET would also write DEBUG output from boto3/botocore to the log file
    assert basic_config.call_args.kwargs['level'] == logging.INFO
    assert basic_config.call_args.kwargs['filename'] == os.path.join(TOOL_DIR, 'DRS-Update-Tool.log')


# --- Exporting settings (get_settings.py) ----------------------------------

def test_both_csv_files_get_the_same_header(tmp_path, monkeypatch):
    get_settings = load('get_settings')
    settings_csv = tmp_path / 'DRS_Settings.csv'
    original_csv = tmp_path / 'DRS_Settings-DO_NOT_EDIT.csv'
    monkeypatch.setattr(get_settings, 'SETTINGS_CSV', str(settings_csv))
    monkeypatch.setattr(get_settings, 'ORIGINAL_SETTINGS_CSV', str(original_csv))
    monkeypatch.setattr(get_settings, 'get_settings', lambda: [['host', 's-1'] + [''] * 31])

    get_settings.generate_settings_csv()

    with open(settings_csv, newline='') as f1, open(original_csv, newline='') as f2:
        header1, header2 = next(csv.reader(f1)), next(csv.reader(f2))
    assert header1 == header2 == get_settings.CSV_HEADER
    assert header1[10:12] == ['Target Instance Type', 'Target Key Pair']


def test_launch_template_without_tags_does_not_crash():
    builder = load('object_builders.launch_template_obj_builder')
    for tag_specifications in (None, [], [{'ResourceType': 'instance', 'Tags': [{'Key': 'a', 'Value': 'b'}]}]):
        instance_tags, volume_tags = builder.tag_obj_builder_for_csv(tag_specifications)
        assert isinstance(instance_tags.Tags, list)
        assert volume_tags.Tags == []


def test_missing_daily_pit_rule_does_not_crash():
    builder = load('object_builders.replication_settings_obj_builder')
    assert builder.pit_policy_obj_builder_for_csv([{'units': 'HOUR', 'retentionDuration': 24}]) is None


def test_one_failing_server_does_not_stop_the_export(monkeypatch):
    get_settings = load('get_settings')
    get_settings.all_settings.clear()
    servers = [
        {'sourceServerID': 's-good-1', 'dataReplicationInfo': {'dataReplicationState': 'CONTINUOUS'}},
        {'sourceServerID': 's-broken', 'dataReplicationInfo': {'dataReplicationState': 'CONTINUOUS'}},
        {'sourceServerID': 's-disconnected', 'dataReplicationInfo': {'dataReplicationState': 'DISCONNECTED'}},
        {'sourceServerID': 's-good-2', 'dataReplicationInfo': {'dataReplicationState': 'CONTINUOUS'}},
    ]
    get_settings.drs.client.describe_source_servers.return_value = {'items': servers}

    def fake_server_settings(server):
        if server['sourceServerID'] == 's-broken':
            raise FakeClientError('AccessDenied')
        return [server['sourceServerID']]

    monkeypatch.setattr(get_settings, 'get_server_settings', fake_server_settings)
    assert get_settings.get_settings() == [['s-good-1'], ['s-good-2']]


# --- Updating settings (update_settings.py and classes) ---------------------

def test_launch_template_update_keeps_settings_not_in_the_csv():
    module = load('classes.launch_template_settings')
    ec2 = module.ec2.client
    ec2.describe_launch_template_versions.return_value = {'LaunchTemplateVersions': [{'LaunchTemplateData': {
        'UserData': 'IyEvYmluL2Jhc2g=',
        'MetadataOptions': {'HttpTokens': 'required'},
        'InstanceType': 't3.micro',
        'KeyName': 'old-key',
    }}]}
    ec2.create_launch_template_version.return_value = {'LaunchTemplateVersion': {'VersionNumber': 7}}

    settings = module.LaunchTemplateSettings(InstanceType='m5.large', KeyName='', ImageId='ami-123')
    settings.update_launch_template('lt-1', settings)

    data = ec2.create_launch_template_version.call_args.kwargs['LaunchTemplateData']
    assert data['UserData'] == 'IyEvYmluL2Jhc2g='
    assert data['MetadataOptions'] == {'HttpTokens': 'required'}
    assert data['InstanceType'] == 'm5.large'
    assert data['ImageId'] == 'ami-123'
    assert 'KeyName' not in data  # cleared in the CSV, so removed
    ec2.modify_launch_template.assert_called_once_with(LaunchTemplateId='lt-1', DefaultVersion='7')


def test_replication_update_keeps_existing_pit_rules():
    module = load('classes.replication_settings')
    drs = module.drs.client
    drs.get_replication_configuration.return_value = {'pitPolicy': [
        {'enabled': False, 'interval': 10, 'retentionDuration': 30, 'ruleID': 1, 'units': 'MINUTE'},
        {'enabled': True, 'interval': 2, 'retentionDuration': 48, 'ruleID': 2, 'units': 'HOUR'},
        {'enabled': True, 'interval': 1, 'retentionDuration': 7, 'ruleID': 3, 'units': 'DAY'},
    ]}
    settings = module.ReplicationSettings(sourceServerID='s-1', bandwidthThrottling=0,
                                          pitPolicy={'enabled': True, 'interval': 1, 'retentionDuration': 14, 'ruleID': 3, 'units': 'DAY'})
    settings.update_replication_settings(settings)

    pit_policy = drs.update_replication_configuration.call_args.kwargs['pitPolicy']
    assert pit_policy[0] == {'enabled': False, 'interval': 10, 'retentionDuration': 30, 'ruleID': 1, 'units': 'MINUTE'}
    assert pit_policy[1] == {'enabled': True, 'interval': 2, 'retentionDuration': 48, 'ruleID': 2, 'units': 'HOUR'}
    assert pit_policy[2]['units'] == 'DAY' and pit_policy[2]['retentionDuration'] == 14


def test_security_groups_are_split_with_or_without_spaces():
    builder = load('object_builders.replication_settings_obj_builder')
    row = [''] * 33
    row[1], row[18], row[19], row[20], row[24], row[26], row[32] = 's-1', 'True', 'True', '0', '7', '[]', '{}'
    for value in ('sg-1, sg-2', 'sg-1,sg-2', ' sg-1 ,sg-2, '):
        row[29] = value
        assert builder.replication_settings_obj_builder(row).replicationServersSecurityGroupsIDs == ['sg-1', 'sg-2']


def test_update_stops_if_csv_row_counts_differ(tmp_path, monkeypatch):
    update_settings = load('update_settings')
    edited, original = tmp_path / 'edited.csv', tmp_path / 'original.csv'
    edited.write_text('header\nrow1\nrow2\n')
    original.write_text('header\nrow1\n')
    builder = MagicMock()
    monkeypatch.setattr(update_settings, 'drs_launch_settings_obj_builder', builder)
    update_settings.rows1.clear()
    update_settings.rows2.clear()

    update_settings.update_settings(str(edited), str(original))
    builder.assert_not_called()


# --- Validation --------------------------------------------------------------

def test_instance_types_are_read_from_all_pages_once():
    validator = load('utils.settings_validator')
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {'InstanceTypeOfferings': [{'InstanceType': 't3.micro'}]},
        {'InstanceTypeOfferings': [{'InstanceType': 'm7i.large'}]},
    ]
    validator.ec2.client.get_paginator.return_value = paginator

    assert validator.get_valid_instance_types() == {'t3.micro', 'm7i.large'}
    validator.get_valid_instance_types()
    validator.ec2.client.get_paginator.assert_called_once_with('describe_instance_type_offerings')


def test_kms_alias_arn_is_validated_with_the_full_arn():
    validator = load('utils.settings_validator')
    validator._valid_instance_types = {'t3.micro'}
    alias_arn = 'arn:aws:kms:us-east-1:111122223333:alias/drs-staging'
    source = types.SimpleNamespace(sourceServerID='s-1')
    launch = types.SimpleNamespace(targetInstanceTypeRightSizingMethod='NONE', copyPrivateIp=False, copyTags=False,
                                   launchDisposition='STOPPED', launchIntoInstanceProperties={'launchIntoEC2InstanceID': ''},
                                   licensing=types.SimpleNamespace(osByol=False))
    template = types.SimpleNamespace(InstanceType='t3.micro', KeyName='', ImageId='',
                                     IamInstanceProfile=types.SimpleNamespace(Name=''))
    replication = types.SimpleNamespace(associateDefaultSecurityGroup=True, autoReplicateNewDisks=True, bandwidthThrottling=0,
                                        createPublicIP=False, dataPlaneRouting='PRIVATE_IP', defaultLargeStagingDiskType='GP3',
                                        pitPolicy={'retentionDuration': 7}, replicationServerInstanceType='t3.micro',
                                        ebsEncryption='CUSTOM', ebsEncryptionKeyArn=alias_arn,
                                        replicationServersSecurityGroupsIDs=[], stagingAreaSubnetId='', useDedicatedReplicationServer=False)

    validator.validate_settings(source, launch, template, replication)
    validator.kms.client.describe_key.assert_called_once_with(KeyId=alias_arn)


def test_negative_bandwidth_throttling_is_rejected():
    validator = load('utils.settings_validator')
    validator._valid_instance_types = {'t3.micro'}
    source = types.SimpleNamespace(sourceServerID='s-1')
    launch = types.SimpleNamespace(targetInstanceTypeRightSizingMethod='NONE', copyPrivateIp=False, copyTags=False,
                                   launchDisposition='STOPPED', launchIntoInstanceProperties={'launchIntoEC2InstanceID': ''},
                                   licensing=types.SimpleNamespace(osByol=False))
    template = types.SimpleNamespace(InstanceType='t3.micro', KeyName='', ImageId='',
                                     IamInstanceProfile=types.SimpleNamespace(Name=''))
    replication = types.SimpleNamespace(associateDefaultSecurityGroup=True, autoReplicateNewDisks=True, bandwidthThrottling=-5)
    error_log = MagicMock()
    validator.logger.error = error_log
    with pytest.raises(SystemExit):
        validator.validate_settings(source, launch, template, replication)
    assert "Invalid 'Bandwidth Throttling'" in error_log.call_args.args[0]
