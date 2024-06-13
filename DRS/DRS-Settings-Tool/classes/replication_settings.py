import boto3
from utils.obj_to_dict import obj_to_dict 
from utils.delete_none import delete_none
from utils.clients import drs_client

drs = drs_client()

class ReplicationSettings(object):
    def __init__(self, associateDefaultSecurityGroup=None, autoReplicateNewDisks=None, bandwidthThrottling=None, createPublicIP=None, dataPlaneRouting=None, defaultLargeStagingDiskType=None, ebsEncryption=None, ebsEncryptionKeyArn=None, pitPolicy=None, replicatedDisks=None, replicationServerInstanceType=None, replicationServersSecurityGroupsIDs=[], stagingAreaSubnetId=None, stagingAreaTags=None, useDedicatedReplicationServer=None, sourceServerID=None, **kwargs):
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
        self.replicationServersSecurityGroupsIDs = replicationServersSecurityGroupsIDs
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
        pit_policy = [{'enabled': True, 'interval': 10, 'retentionDuration': 60, 'ruleID': 1, 'units': 'MINUTE'}, {'enabled': True, 'interval': 1, 'retentionDuration': 24, 'ruleID': 2, 'units': 'HOUR'}]
        pit_policy.append(replication_settings['pitPolicy'])
        replication_settings['pitPolicy'] = pit_policy
        drs.client.update_replication_configuration(**replication_settings)



class PitPolicy(object):
    def __init__(self, enabled=None, interval=None, retentionDuration=None, ruleID=None, units=None, **kwargs):
        self.enabled = enabled
        self.interval = interval
        self.retentionDuration = retentionDuration
        self.ruleID = ruleID
        self.units = units


