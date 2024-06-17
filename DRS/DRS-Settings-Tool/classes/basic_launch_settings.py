import boto3
from utils.obj_to_dict import obj_to_dict
from utils.delete_none import delete_none
from utils.clients import drs_client
drs = drs_client()

class BasicLaunchSettings(object):
    def __init__(self, copyPrivateIp=None, copyTags=None, ec2LaunchTemplateID=None, launchDisposition=None, launchIntoInstanceProperties=None, licensing=None, sourceServerID=None, targetInstanceTypeRightSizingMethod=None, **kwargs):
        self.copyPrivateIp = copyPrivateIp
        self.copyTags = copyTags
        self.ec2LaunchTemplateID = ec2LaunchTemplateID
        self.launchDisposition = launchDisposition
        self.launchIntoInstanceProperties = launchIntoInstanceProperties
        self.licensing = licensing
        self.sourceServerID = sourceServerID
        self.targetInstanceTypeRightSizingMethod = targetInstanceTypeRightSizingMethod

    def update_basic_launch_settings(self, object):
        launch_settings_dict = obj_to_dict(object)
        launch_settings = delete_none(launch_settings_dict)
        del launch_settings['ec2LaunchTemplateID']
        drs.client.update_launch_configuration(**launch_settings)

    def __eq__(self, other):
        return (self.copyPrivateIp, self.copyTags, self.ec2LaunchTemplateID, self.launchDisposition, self.launchIntoInstanceProperties, self.licensing.__dict__, self.sourceServerID, self.targetInstanceTypeRightSizingMethod) == (other.copyPrivateIp, other.copyTags, other.ec2LaunchTemplateID, other.launchDisposition, other.launchIntoInstanceProperties, other.licensing.__dict__, other.sourceServerID, other.targetInstanceTypeRightSizingMethod)
    
    def __ne__(self, other):
        return (self.copyPrivateIp, self.copyTags, self.ec2LaunchTemplateID, self.launchDisposition, self.launchIntoInstanceProperties, self.licensing.__dict__, self.sourceServerID, self.targetInstanceTypeRightSizingMethod) != (other.copyPrivateIp, other.copyTags, other.ec2LaunchTemplateID, other.launchDisposition, other.launchIntoInstanceProperties, other.licensing.__dict__, other.sourceServerID, other.targetInstanceTypeRightSizingMethod)




class ByolSetting(object):
    def __init__(self, osByol=None, **kwargs):
        self.osByol = osByol

class LaunchIntoInstance(object):
    def __init__(self, launchIntoEC2InstanceID=None):
        self.launchIntoEC2InstanceID = launchIntoEC2InstanceID
