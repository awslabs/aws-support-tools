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

    # Launch template fields that are managed through the CSV file.
    CSV_MANAGED_FIELDS = ('IamInstanceProfile', 'BlockDeviceMappings', 'NetworkInterfaces', 'ImageId', 'InstanceType', 'KeyName', 'TagSpecifications')

    # Read-only keys that describe_launch_template_versions returns but
    # create_launch_template_version rejects (ParamValidationError).
    RESPONSE_ONLY_KEYS = {
        'MetadataOptions': ('State',),
        'Operator': ('Managed', 'HiddenByDefault'),
    }

    @classmethod
    def remove_response_only_keys(cls, launch_template_data):
        for field, keys in cls.RESPONSE_ONLY_KEYS.items():
            value = launch_template_data.get(field)
            if not isinstance(value, dict):
                continue
            value = {key: item for key, item in value.items() if key not in keys}
            if value:
                launch_template_data[field] = value
            else:
                del launch_template_data[field]
        return launch_template_data

    def update_launch_template(self, launch_template_id, object):
        launch_template_settings = delete_none(obj_to_dict(object))

        # Start from the current default version so settings that are not in
        # the CSV (user data, metadata options, monitoring, placement, ...)
        # are kept. Only the CSV-managed fields are replaced; a field that was
        # cleared in the CSV is removed.
        current_version = ec2.client.describe_launch_template_versions(LaunchTemplateId=launch_template_id, Versions=['$Default'])['LaunchTemplateVersions'][0]
        launch_template_data = {key: value for key, value in current_version.get('LaunchTemplateData', {}).items() if key not in self.CSV_MANAGED_FIELDS}
        self.remove_response_only_keys(launch_template_data)
        for key in self.CSV_MANAGED_FIELDS:
            if launch_template_settings.get(key) not in (None, {}, []):
                launch_template_data[key] = launch_template_settings[key]

        response = ec2.client.create_launch_template_version(
            LaunchTemplateId=launch_template_id,
            VersionDescription='DRS-Settings-Updater-' + str(datetime.now()),
            LaunchTemplateData=launch_template_data
        )
        self.set_default_version(launch_template_id, response['LaunchTemplateVersion']['VersionNumber'])

    def set_default_version(self, launch_template_id, version_number):
        # Use the version number returned by create_launch_template_version
        # instead of listing (paginated) versions to find the newest one.
        ec2.client.modify_launch_template(LaunchTemplateId=launch_template_id, DefaultVersion=str(version_number))
    


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



