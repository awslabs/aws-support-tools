
import botocore
import sys
from utils.logger import get_logger
from utils.clients import ec2_client, kms_client, iam_client

ec2 = ec2_client()
kms = kms_client()
iam = iam_client()


logger = get_logger('VALIDATE')

_valid_instance_types = None


def get_valid_instance_types():
    # Instance type offerings are paginated, and are the same for every
    # server, so collect all pages once and reuse the result.
    global _valid_instance_types
    if _valid_instance_types is None:
        _valid_instance_types = set()
        paginator = ec2.client.get_paginator('describe_instance_type_offerings')
        for page in paginator.paginate():
            for offering in page['InstanceTypeOfferings']:
                _valid_instance_types.add(offering['InstanceType'])
    return _valid_instance_types

def validate_settings(source_server_info_obj, drs_launch_settings_obj, launch_template_obj, replication_settings_obj):




    try:
        logger.info("[VALIDATE] Validating settings for Server ID: " + source_server_info_obj.sourceServerID + "...")
            
        #Create a variable with valid options for each of the settings, so we can compare customers settings vs valid options.
        valid_right_sizing = ['NONE', 'BASIC', 'IN_AWS']
        true_or_false = [True, False]
        valid_launch_disposition = ['STOPPED', 'STARTED']
        valid_use_private_ip_for_replication = ['PRIVATE_IP', 'PUBLIC_IP']
        valid_default_staging_disk_type = ['GP2', 'GP3', 'ST1', 'AUTO']
        valid_staging_disk_encryption = ['DEFAULT', 'CUSTOM', 'NONE']

        valid_instance_types = get_valid_instance_types()



        if drs_launch_settings_obj.targetInstanceTypeRightSizingMethod not in valid_right_sizing:
            logger.error("[ERROR] Invalid Right Sizing setting for " + source_server_info_obj.sourceServerID + ". Valid options are NONE, BASIC, or IN_AWS.")
            sys.exit()
        
        if drs_launch_settings_obj.copyPrivateIp not in true_or_false:
            logger.error("[ERROR] Invalid 'Copy Private IP' setting for " + source_server_info_obj.sourceServerID + ". Valid options are TRUE or FALSE.")
            sys.exit()

        if drs_launch_settings_obj.copyTags not in true_or_false:
            logger.error("[ERROR] Invalid 'Copy Tags' setting for " + source_server_info_obj.sourceServerID + ". Valid options are TRUE or FALSE.")
            sys.exit()

        if drs_launch_settings_obj.launchDisposition not in valid_launch_disposition:
            logger.error("[ERROR] Invalid 'Launch Disposition' setting for " + source_server_info_obj.sourceServerID + ". Valid options are STOPPED or STARTED.")
            sys.exit()

        if drs_launch_settings_obj.launchIntoInstanceProperties['launchIntoEC2InstanceID'] not in (None, ''):
            try:
                ec2.client.describe_instances(InstanceIds=[drs_launch_settings_obj.launchIntoInstanceProperties['launchIntoEC2InstanceID']])
            except botocore.exceptions.ClientError as error:
                logger.error('[ERROR] Could not validate Launch Into Instance ID: ' + str(error))
                sys.exit()

        if drs_launch_settings_obj.licensing.__dict__['osByol'] not in true_or_false:
            logger.error("[ERROR] Invalid 'BYOL' setting for " + source_server_info_obj.sourceServerID + ". Valid options are TRUE or FALSE.")
            sys.exit()

        if launch_template_obj.InstanceType not in valid_instance_types:
            logger.error("[ERROR] Invalid 'Instance Type' setting for " + source_server_info_obj.sourceServerID + ". Please review the available instance types for your region and update as necessary.")
            sys.exit()

        if launch_template_obj.KeyName not in (None, ''):
            try:
                ec2.client.describe_key_pairs(KeyNames=[launch_template_obj.KeyName])
            except botocore.exceptions.ClientError as error:
                logger.error('[ERROR] Could not validate Key Pair: ' + str(error))
                sys.exit()

        if launch_template_obj.ImageId not in (None, ''):
            try:
                ec2.client.describe_images(ImageIds=[launch_template_obj.ImageId])
            except botocore.exceptions.ClientError as error:
                logger.error('[ERROR] Could not validate AMI ID: ' + str(error))
                sys.exit()
            
        if launch_template_obj.IamInstanceProfile.__dict__['Name'] not in (None, ''):
            try:
                iam.client.get_instance_profile(InstanceProfileName=launch_template_obj.IamInstanceProfile.__dict__['Name'])
            except botocore.exceptions.ClientError as error:
                logger.error('[ERROR] Could not validate IAM Instance Profile: ' + str(error))
                sys.exit()

        if replication_settings_obj.associateDefaultSecurityGroup not in true_or_false:
            logger.error("[ERROR] Invalid 'Use Default Replication Security Group' setting for " + source_server_info_obj.sourceServerID + ". Valid options are TRUE or FALSE.")
            sys.exit()

        if replication_settings_obj.autoReplicateNewDisks not in true_or_false:
            logger.error("[ERROR] Invalid 'Auto Replicate New Disks' setting for " + source_server_info_obj.sourceServerID + ". Valid options are TRUE or FALSE.")
            sys.exit()

        if not 0 <= replication_settings_obj.bandwidthThrottling <= 10000:
            logger.error("[ERROR] Invalid 'Bandwidth Throttling' setting for " + source_server_info_obj.sourceServerID + ". Valid setting is a number between 0 and 10000 (0 is to disable Bandwidth Throttling)")
            sys.exit()

        if replication_settings_obj.createPublicIP not in true_or_false:
            logger.error("[ERROR] Invalid 'Create Public IP for Replication Server' setting for " + source_server_info_obj.sourceServerID + ". Valid options are TRUE or FALSE.")
            sys.exit()

        if replication_settings_obj.dataPlaneRouting not in valid_use_private_ip_for_replication:
            logger.error("[ERROR] Invalid 'Use Private IP for Data Replication' setting for " + source_server_info_obj.sourceServerID + ". Valid options are PRIVATE_IP or PUBLIC_IP.")
            sys.exit()

        if replication_settings_obj.defaultLargeStagingDiskType not in valid_default_staging_disk_type:
            logger.error("[ERROR] Invalid 'Default Large Staging Disk Type' setting for " + source_server_info_obj.sourceServerID + ". Valid options are GP2, GP3, ST1, or AUTO.")
            sys.exit()

        if replication_settings_obj.pitPolicy['retentionDuration'] < 1 or replication_settings_obj.pitPolicy['retentionDuration'] > 365:
            logger.error("[ERROR] Invalid 'PIT Retention Setting(Days)' setting for " + source_server_info_obj.sourceServerID + ". Valid setting is a number between 1 and 365.")
            sys.exit()

        if replication_settings_obj.replicationServerInstanceType not in valid_instance_types:
            logger.error("[ERROR] Invalid 'Replication Server Instance Type' setting for " + source_server_info_obj.sourceServerID + ". Please review the available instance types for your region and update as necessary.")
            sys.exit()


        if replication_settings_obj.ebsEncryption not in valid_staging_disk_encryption:
            logger.error("[ERROR] Invalid 'Staging Disk Encryption' setting for " + source_server_info_obj.sourceServerID + ". Valid options are DEFAULT, CUSTOM, or NONE.")
            sys.exit()

        if replication_settings_obj.ebsEncryptionKeyArn not in (None, ''):
            try:
                # describe_key accepts the full key or alias ARN directly.
                kms.client.describe_key(KeyId=replication_settings_obj.ebsEncryptionKeyArn)
            except botocore.exceptions.ClientError as error:
                logger.error('[ERROR] Could not validate KMS ID: ' + str(error))
                sys.exit()


        if replication_settings_obj.replicationServersSecurityGroupsIDs:
            try:
                ec2.client.describe_security_groups(GroupIds=replication_settings_obj.replicationServersSecurityGroupsIDs)
            except botocore.exceptions.ClientError as error:
                logger.error('[ERROR] Could not validate Replication Server Security Groups: ' + str(error))
                sys.exit()

        if replication_settings_obj.stagingAreaSubnetId not in (None, ''):
            try:
                ec2.client.describe_subnets(SubnetIds=[replication_settings_obj.stagingAreaSubnetId])
            except botocore.exceptions.ClientError as error:
                logger.error('[ERROR] Could not validate Staging Subnet ID: ' + str(error))
                sys.exit()

        if replication_settings_obj.useDedicatedReplicationServer not in true_or_false:
            logger.error("[ERROR] Invalid 'Use Dedicated Replicator' setting for " + source_server_info_obj.sourceServerID + ". Valid options are TRUE or FALSE.")
            sys.exit()

    except botocore.exceptions.ClientError as error:
        logger.error(error)

    logger.info("[VALIDATE] Settings have been validated.")
            



