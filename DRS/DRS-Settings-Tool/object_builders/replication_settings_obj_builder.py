from classes.replication_settings import ReplicationSettings
from classes.replication_settings import PitPolicy
from utils.str2bool import str2bool
from utils.obj_to_dict import obj_to_dict
import ast

def replication_settings_obj_builder_for_csv(info):
    info.pop('ResponseMetadata')
    replication_settings_obj = ReplicationSettings(**info)
    return replication_settings_obj

def pit_policy_obj_builder_for_csv(info):
    for policy in info:
        if policy['units'] == 'DAY':
            pit_policy_obj = PitPolicy(**policy)
    return pit_policy_obj



def replication_settings_obj_builder(row):
    replication_settings_obj = ReplicationSettings()
    pit_settings_obj = PitPolicy(enabled=True, interval=1, ruleID=3, units='DAY')

    replication_settings_obj.associateDefaultSecurityGroup = str2bool(row[18])
    replication_settings_obj.autoReplicateNewDisks = None
    if row[19].upper != "":
        replication_settings_obj.autoReplicateNewDisks = str2bool(row[19])
    replication_settings_obj.bandwidthThrottling = ast.literal_eval(row[20])
    replication_settings_obj.createPublicIP = str2bool(row[21])
    replication_settings_obj.dataPlaneRouting = row[22].upper()
    replication_settings_obj.defaultLargeStagingDiskType = row[23].upper()
    pit_settings_obj.retentionDuration = ast.literal_eval(row[24])
    replication_settings_obj.pitPolicy = obj_to_dict(pit_settings_obj)
    replication_settings_obj.replicationServerInstanceType = row[25].lower()
    replication_settings_obj.replicatedDisks = ast.literal_eval(row[26])
    replication_settings_obj.ebsEncryption = row[27]
    replication_settings_obj.ebsEncryptionKeyArn = row[28]
    if row[29] != "":
        replication_settings_obj.replicationServersSecurityGroupsIDs = row[29].split(', ')
    replication_settings_obj.stagingAreaSubnetId = row[30]
    replication_settings_obj.useDedicatedReplicationServer = str2bool(row[31])
    replication_settings_obj.stagingAreaTags = ast.literal_eval(row[32])
    replication_settings_obj.sourceServerID = row[1]

    return replication_settings_obj
