import boto3
from utils.obj_to_dict import obj_to_dict
from utils.delete_none import delete_none
from datetime import datetime
from utils.clients import ec2_client


ec2 = ec2_client()

class LaunchTemplateSettings(object):
    def __init__(self, IamInstanceProfile=None, BlockDeviceMappings=None, NetworkInterfaces=None, ImageId=None, InstanceType=None, KeyName=None, TagSpecifications=None,  SecurityGroupIds=None, SecurityGroups=None, **kwargs):
        self.IamInstanceProfile = IamInstanceProfile
        self.BlockDeviceMappings = BlockDeviceMappings
        self.NetworkInterfaces = NetworkInterfaces
        self.ImageId = ImageId
        self.InstanceType = InstanceType
        self.KeyName = KeyName
        self.TagSpecifications = TagSpecifications
        self.SecurityGroupIds = SecurityGroupIds
        self.SecurityGroups = SecurityGroups

    def __eq__(self, other):
        return (self.IamInstanceProfile.__dict__, self.BlockDeviceMappings, self.NetworkInterfaces, self.ImageId, self.InstanceType, self.KeyName, obj_to_dict(self.TagSpecifications[0]), obj_to_dict(self.TagSpecifications[1]), self. SecurityGroupIds, self.SecurityGroups) == (other.IamInstanceProfile.__dict__, other.BlockDeviceMappings, other.NetworkInterfaces, other.ImageId, other.InstanceType, other.KeyName, obj_to_dict(other.TagSpecifications[0]),obj_to_dict(other.TagSpecifications[1]), other. SecurityGroupIds, other.SecurityGroups)
    
    def __ne__(self, other):
        return (self.IamInstanceProfile.__dict__, self.BlockDeviceMappings, self.NetworkInterfaces, self.ImageId, self.InstanceType, self.KeyName, obj_to_dict(self.TagSpecifications[0]), obj_to_dict(self.TagSpecifications[1]), self. SecurityGroupIds, self.SecurityGroups) != (other.IamInstanceProfile.__dict__, other.BlockDeviceMappings, other.NetworkInterfaces, other.ImageId, other.InstanceType, other.KeyName, obj_to_dict(other.TagSpecifications[0]),obj_to_dict(other.TagSpecifications[1]), other. SecurityGroupIds, other.SecurityGroups)

    def update_launch_template(self, launch_template_id, object):
        launch_template_dict = obj_to_dict(object)
        launch_template_settings = delete_none(launch_template_dict)
        ec2.client.create_launch_template_version(
            LaunchTemplateId=launch_template_id,
            VersionDescription='DRS-Settings-Updater-' + str(datetime.now()),
            LaunchTemplateData=launch_template_settings
        )
        self.set_default_version(launch_template_id)

    def set_default_version(self, launch_template_id):
        launch_template_versions = (ec2.client.describe_launch_template_versions(LaunchTemplateId=launch_template_id))['LaunchTemplateVersions']
        latest_version = 0
        for version in launch_template_versions:
            if version['VersionNumber'] > latest_version:
                latest_version = version['VersionNumber']
        ec2.client.modify_launch_template(LaunchTemplateId=launch_template_id, DefaultVersion=str(latest_version))
    


class LaunchNetworkSettings(object):
    def __init__(self, AssociatePublicIpAddress=None, DeleteOnTermination=None, DeviceIndex=None, InterfaceType=None, PrivateIpAddresses=None, Groups=None, NetworkInterfaceId=None, SubnetId=None, **kwargs):
        self.AssociatePublicIpAddress = AssociatePublicIpAddress
        self.DeleteOnTermination = DeleteOnTermination
        self.DeviceIndex = DeviceIndex
        self.InterfaceType = InterfaceType
        self.PrivateIpAddresses = PrivateIpAddresses
        self.Groups = Groups
        self.NetworkInterfaceId = NetworkInterfaceId
        self.SubnetId = SubnetId

class IpSettings(object):
    def __init__(self, Primary=None, PrivateIpAddress=None, **kwargs):
        self.Primary = Primary
        self.PrivateIpAddress = PrivateIpAddress

class InstanceRoleSettings(object):
    def __init__(self, Name=None, **kwargs):
        self.Name = Name
        

class TargetTags(object):
    def __init__(self, ResourceType=None, Tags=None, **kwargs):
        self.ResourceType = ResourceType
        self.Tags = Tags



