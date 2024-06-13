import botocore
import csv
import os
from object_builders.drs_launch_settings_obj_builder import basic_launch_settings_obj_builder_for_csv
from object_builders.source_server_info_obj_builder import source_server_info_obj_builder_for_csv
from object_builders.drs_launch_settings_obj_builder import byol_settings_obj_builder_for_csv
from object_builders.launch_template_obj_builder import launch_template_obj_builder_for_csv
from object_builders.launch_template_obj_builder import instance_role_obj_builder_for_csv
from object_builders.launch_template_obj_builder import tag_obj_builder_for_csv
from object_builders.replication_settings_obj_builder import replication_settings_obj_builder_for_csv
from object_builders.replication_settings_obj_builder import pit_policy_obj_builder_for_csv
from utils.logger import get_logger
from utils.clients import drs_client,ec2_client
from utils.logger import path

drs = drs_client()
ec2 = ec2_client()

all_settings = []

logger = get_logger('COLLECT')
def get_settings():

    

    try:
        source_server_info = []
        sourceInfo = drs.client.describe_source_servers()
        for item in sourceInfo['items']:
            source_server_info.append(item)
        while 'nextToken' in sourceInfo:
            sourceInfo = drs.client.describe_source_servers(nextToken=sourceInfo['nextToken'])
            for item in sourceInfo['items']:
                source_server_info.append(item)


        for server in source_server_info:

            #Skip disconnected servers
            if server['dataReplicationInfo']['dataReplicationState'] == 'DISCONNECTED':
                continue

            #Create object with necessary source server info
            source_server_info_obj = source_server_info_obj_builder_for_csv(server)

            #Get API data to build objects with
            basic_launch_settings_info = drs.client.get_launch_configuration(sourceServerID=source_server_info_obj.sourceServerID)

            #Create object with necessary basic launch settings
            basic_launch_settings_obj = basic_launch_settings_obj_builder_for_csv(basic_launch_settings_info)
            byol_setting_obj = byol_settings_obj_builder_for_csv(basic_launch_settings_obj.licensing)

            #Create object with necessary launch template settings
            launch_template_settings_info = ec2.client.describe_launch_template_versions(LaunchTemplateId=basic_launch_settings_obj.ec2LaunchTemplateID, Versions=['$Default'])
            launch_template_settings_obj = launch_template_obj_builder_for_csv(launch_template_settings_info)
            instance_role_settings_obj = instance_role_obj_builder_for_csv(launch_template_settings_obj.IamInstanceProfile)
            target_tags_obj = tag_obj_builder_for_csv(launch_template_settings_obj.TagSpecifications)
            target_instance_tags_obj = target_tags_obj[0]
            target_volume_tags_obj = target_tags_obj[1]

            #Create object with necessary replication settings
            replication_settings_info = drs.client.get_replication_configuration(sourceServerID=source_server_info_obj.sourceServerID)
            replication_settings_obj = replication_settings_obj_builder_for_csv(replication_settings_info)
            pit_policy_obj = pit_policy_obj_builder_for_csv(replication_settings_obj.pitPolicy)

            ## Set all variables to go into CSV

            hostname = source_server_info_obj.sourceProperties['identificationHints']['hostname']
            server_id = source_server_info_obj.sourceServerID
            recommended_instance_type = source_server_info_obj.sourceProperties['recommendedInstanceType']

            #basic launch info
            launch_template_id = basic_launch_settings_obj.ec2LaunchTemplateID
            right_sizing = basic_launch_settings_obj.targetInstanceTypeRightSizingMethod
            copy_private_ip = basic_launch_settings_obj.copyPrivateIp
            copy_tags = basic_launch_settings_obj.copyTags
            launch_disposition = basic_launch_settings_obj.launchDisposition
            if basic_launch_settings_obj.launchIntoInstanceProperties in ({}, None):
                launch_into_instance = ""
            else:
                launch_into_instance = basic_launch_settings_obj.launchIntoInstanceProperties['launchIntoEC2InstanceID']
            byol_setting = byol_setting_obj.osByol


            #launch template info
            target_instance_type = launch_template_settings_obj.InstanceType
            target_ami_id = launch_template_settings_obj.ImageId
            target_network_settings = launch_template_settings_obj.NetworkInterfaces
            target_disk = launch_template_settings_obj.BlockDeviceMappings
            target_instance_profile_role = instance_role_settings_obj.Name
            target_instance_tags = target_instance_tags_obj.Tags
            target_volume_tags = target_volume_tags_obj.Tags
            target_key_pair = launch_template_settings_obj.KeyName

            #replication settings info
            replication_server_default_sg = replication_settings_obj.associateDefaultSecurityGroup
            auto_replicate_new_disks = replication_settings_obj.autoReplicateNewDisks
            bandwidth_throttling = replication_settings_obj.bandwidthThrottling
            create_public_ip_replication_server = replication_settings_obj.createPublicIP
            use_private_ip_for_replication = replication_settings_obj.dataPlaneRouting
            default_large_staging_disk_type = replication_settings_obj.defaultLargeStagingDiskType
            staging_disk_encryption = replication_settings_obj.ebsEncryption
            staging_disk_encryption_key = replication_settings_obj.ebsEncryptionKeyArn
            pit_policy = pit_policy_obj.retentionDuration
            staging_disk_settings = replication_settings_obj.replicatedDisks
            replication_instance_type = replication_settings_obj.replicationServerInstanceType
            replication_server_security_groups = ', '.join(replication_settings_obj.replicationServersSecurityGroupsIDs)
            replication_subnet = replication_settings_obj.stagingAreaSubnetId
            use_dedicated_replicator = replication_settings_obj.useDedicatedReplicationServer
            replication_tags = replication_settings_obj.stagingAreaTags

            all_settings.append([hostname, server_id, launch_template_id, right_sizing, copy_private_ip, copy_tags, launch_disposition, launch_into_instance, byol_setting, recommended_instance_type, target_instance_type, target_key_pair, target_ami_id, target_network_settings, target_disk, target_instance_profile_role, target_instance_tags, target_volume_tags, replication_server_default_sg, auto_replicate_new_disks, bandwidth_throttling, create_public_ip_replication_server, use_private_ip_for_replication, default_large_staging_disk_type, pit_policy, replication_instance_type, staging_disk_settings, staging_disk_encryption, staging_disk_encryption_key, replication_server_security_groups, replication_subnet, use_dedicated_replicator, replication_tags])
    except botocore.exceptions.ClientError as error:
        logger.error(error)
    return all_settings



def generate_settings_csv():

    #Max length of 12500 will allow for a ~15MB CSV file size to ensure file does not take up a lot of disk space.
    max_source_servers = 12500

    logger.info("[COLLECT] Gathering settings from all Active DRS Source Servers...")
    all_settings = get_settings()
    file_name = path + "\\DRS_Settings.csv"
    file_name2 = path + "\\DRS_Settings-DO_NOT_EDIT.csv"
    if len(all_settings) > max_source_servers:
        print("Max source servers limit reached (12,500). If you have more than 12,500 source servers, please adjust the max_length variable in the get_settings.py file.")
        quit()
    with open(file_name, 'w', newline='') as file:
        os.chmod(file_name, 0o644)
        writer = csv.writer(file, delimiter=',')
        fields = ['Hostname', 'Server ID', 'Launch Template ID', 'Right Sizing', 'Copy Private IP', 'Copy Tags', 'Launch Disposition', 'Launch Into Instance', 'BYOL', 'Recommended Instance Type', 'Target Instance Type', 'Target Key Pair', 'Target AMI ID', 'Target Network Settings', 'Target Disk Settings', 'Target Instance Profile Role', 'Target Instance Tags', 'Target Volume Tags', 'Use Default Replication Security Group', 'Auto Replicate New Disks', 'Bandwidth Throttling', 'Create Public IP for Replication Server', 'Use Private IP for Data Replication', 'Default Large Staging Disk Type', 'PIT Retention Setting(Days)', 'Replication Server Instance Type', 'Staging Disk Settings', 'Staging Disk Encryption', 'Staging Disk Encryption Key Arn', 'Replication Server Security Groups', 'Staging Subnet', 'Use Dedicated Replicator', 'Replication Tags']
        writer.writerow(fields)
        for item in all_settings:
            writer.writerow(item)
    with open(file_name2, 'w', newline='') as file:
        os.chmod(file_name2, 0o644)
        writer = csv.writer(file, delimiter=',')
        fields = ['Hostname', 'Server ID', 'Launch Template ID', 'Right Sizing', 'Copy Private IP', 'Copy Tags', 'Launch Disposition', 'Launch Into Instance', 'BYOL', 'Recommended Instance Type', 'Target Key Pair', 'Target Instance Type', 'Target AMI ID', 'Target Network Settings', 'Target Disk Settings', 'Target Instance Profile Role', 'Target Instance Tags', 'Target Volume Tags', 'Use Default Replication Security Group', 'Auto Replicate New Disks', 'Bandwidth Throttling', 'Create Public IP for Replication Server', 'Use Private IP for Data Replication', 'Default Large Staging Disk Type', 'PIT Retention Setting(Days)', 'Replication Server Instance Type', 'Staging Disk Settings', 'Staging Disk Encryption', 'Staging Disk Encryption Key Arn', 'Replication Server Security Groups', 'Staging Subnet', 'Use Dedicated Replicator', 'Replication Tags']
        writer.writerow(fields)
        for item in all_settings:
            writer.writerow(item)
    logger.info("[COLLECT] Completed creating the CSV files with the latest settings from AWS DRS")
generate_settings_csv()
