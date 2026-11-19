import boto3
from utils.obj_to_dict import obj_to_dict 
from utils.delete_none import delete_none
from utils.clients import drs_client

drs = drs_client()

class ReplicationSettings(object):
    def __init__(self, associateDefaultSecurityGroup=None, autoReplicateNewDisks=None, bandwidthThrottling=None, createPublicIP=None, dataPlaneRouting=None, defaultLargeStagingDiskType=None, ebsEncryption=None, ebsEncryptionKeyArn=None, pitPolicy=None, replicatedDisks=None, replicationServerInstanceType=None, replicationServersSecurityGroupsIDs=None, stagingAreaSubnetId=None, stagingAreaTags=None, useDedicatedReplicationServer=None, sourceServerID=None, **kwargs):
        self.associateDefaultSecurityGroup = associateDefaultSecurityGroup
        self.autoReplicateNewDisks = autoReplicateNewDisks
        self.bandwidthThrottling = bandwidthThrottling
        self.createPublicIP = createPublicIP
        self.dataPlaneRouting = dataPlaneRouting
        self.defaultLargeStagingDiskType = defaultLargeStagingDiskType
        self.ebsEncryption = ebsEncryption
        self.ebsEncryptionKeyArn = ebsEncryptionKeyArn
        self.pitPolicy = pitPolicy
        self.replicatedDisks = replicatedDisks
        self.replicationServerInstanceType = replicationServerInstanceType
        self.replicationServersSecurityGroupsIDs = replicationServersSecurityGroupsIDs if replicationServersSecurityGroupsIDs is not None else []
        self.stagingAreaSubnetId = stagingAreaSubnetId
        self.stagingAreaTags = stagingAreaTags
        self.useDedicatedReplicationServer = useDedicatedReplicationServer
        self.sourceServerID = sourceServerID

    def __eq__(self, other):
        return (self.associateDefaultSecurityGroup, self.autoReplicateNewDisks, self.bandwidthThrottling, self.createPublicIP, self.dataPlaneRouting, self.defaultLargeStagingDiskType, self.ebsEncryption, self.ebsEncryptionKeyArn, self.pitPolicy, self.replicatedDisks, self.replicationServerInstanceType, self.replicationServersSecurityGroupsIDs, self.stagingAreaSubnetId, self.stagingAreaTags, self.useDedicatedReplicationServer, self.sourceServerID) == (other.associateDefaultSecurityGroup, other.autoReplicateNewDisks, other.bandwidthThrottling, other.createPublicIP, other.dataPlaneRouting, other.defaultLargeStagingDiskType, other.ebsEncryption, other.ebsEncryptionKeyArn, other.pitPolicy, other.replicatedDisks, other.replicationServerInstanceType, other.replicationServersSecurityGroupsIDs, other.stagingAreaSubnetId, other.stagingAreaTags, other.useDedicatedReplicationServer, other.sourceServerID)
    
    def __ne__(self, other):
        return (self.associateDefaultSecurityGroup, self.autoReplicateNewDisks, self.bandwidthThrottling, self.createPublicIP, self.dataPlaneRouting, self.defaultLargeStagingDiskType, self.ebsEncryption, self.ebsEncryptionKeyArn, self.pitPolicy, self.replicatedDisks, self.replicationServerInstanceType, self.replicationServersSecurityGroupsIDs, self.stagingAreaSubnetId, self.stagingAreaTags, self.useDedicatedReplicationServer, self.sourceServerID) != (other.associateDefaultSecurityGroup, other.autoReplicateNewDisks, other.bandwidthThrottling, other.createPublicIP, other.dataPlaneRouting, other.defaultLargeStagingDiskType, other.ebsEncryption, other.ebsEncryptionKeyArn, other.pitPolicy, other.replicatedDisks, other.replicationServerInstanceType, other.replicationServersSecurityGroupsIDs, other.stagingAreaSubnetId, other.stagingAreaTags, other.useDedicatedReplicationServer, other.sourceServerID)


    def update_replication_settings(self, object):
        replication_settings_dict = obj_to_dict(object)
        replication_settings = delete_none(replication_settings_dict)
        replication_settings['pitPolicy'] = self.build_pit_policy(replication_settings['sourceServerID'], replication_settings['pitPolicy'])
        drs.client.update_replication_configuration(**replication_settings)



    def build_pit_policy(self, source_server_id, day_rule):
        # The CSV only edits the retention of the daily (DAY) rule. Keep the
        # server's other point-in-time rules (MINUTE, HOUR) exactly as they
        # are instead of overwriting them with hard-coded defaults.
        current_rules = drs.client.get_replication_configuration(sourceServerID=source_server_id).get('pitPolicy', [])
        pit_policy = [rule for rule in current_rules if rule.get('units') != 'DAY']
        current_day_rule = next((rule for rule in current_rules if rule.get('units') == 'DAY'), None)
        if current_day_rule:
            day_rule = dict(current_day_rule, retentionDuration=day_rule['retentionDuration'])
        pit_policy.append(day_rule)
        return pit_policy



class PitPolicy(object):
    def __init__(self, enabled=None, interval=None, retentionDuration=None, ruleID=None, units=None, **kwargs):
        self.enabled = enabled
        self.interval = interval
        self.retentionDuration = retentionDuration
        self.ruleID = ruleID
        self.units = units


