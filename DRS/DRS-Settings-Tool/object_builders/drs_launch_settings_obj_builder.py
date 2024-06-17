from classes.basic_launch_settings import BasicLaunchSettings
from classes.basic_launch_settings import LaunchIntoInstance
from classes.basic_launch_settings import ByolSetting
from utils.str2bool import str2bool


def basic_launch_settings_obj_builder_for_csv(info):
    info.pop('ResponseMetadata')
    basic_launch_settings_obj = BasicLaunchSettings(**info)
    return basic_launch_settings_obj
    
def byol_settings_obj_builder_for_csv(info):
    byol_setting_obj = ByolSetting(**info)
    return byol_setting_obj




def drs_launch_settings_obj_builder(row):

    drs_launch_settings_obj = BasicLaunchSettings()
    launch_into_instance_obj = LaunchIntoInstance()
    byol_obj = ByolSetting()


    drs_launch_settings_obj.sourceServerID = row[1]
    drs_launch_settings_obj.ec2LaunchTemplateID = row[2]
    drs_launch_settings_obj.targetInstanceTypeRightSizingMethod = row[3].upper()
    drs_launch_settings_obj.copyPrivateIp = str2bool(row[4])
    drs_launch_settings_obj.copyTags = str2bool(row[5])
    drs_launch_settings_obj.launchDisposition = row[6].upper()
    drs_launch_settings_obj.launchIntoInstanceProperties = {'launchIntoEC2InstanceID': ''}
    if row[7] != "":
        launch_into_instance_obj.launchIntoEC2InstanceID = row[7]
        drs_launch_settings_obj.launchIntoInstanceProperties = launch_into_instance_obj.__dict__
    byol_obj.osByol = str2bool(row[8])
    drs_launch_settings_obj.licensing = byol_obj

    return drs_launch_settings_obj
