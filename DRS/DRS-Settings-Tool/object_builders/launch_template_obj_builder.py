from classes.launch_template_settings import LaunchTemplateSettings
from classes.launch_template_settings import LaunchNetworkSettings
from classes.launch_template_settings import InstanceRoleSettings
from classes.launch_template_settings import TargetTags
import ast



def launch_template_obj_builder_for_csv(info):
    info = info['LaunchTemplateVersions'][0]['LaunchTemplateData']
    launch_template_settings_obj = LaunchTemplateSettings(**info)
    return launch_template_settings_obj

def instance_role_obj_builder_for_csv(info):
    if info == None:
        instance_role_settings_obj = InstanceRoleSettings()
    else:     
        instance_role_settings_obj = InstanceRoleSettings(**info)
    return instance_role_settings_obj

def tag_obj_builder_for_csv(info):
    for tags in info:
        if tags['ResourceType'] == 'instance':
            target_instance_tags_obj = TargetTags(**tags)
        elif tags['ResourceType'] == 'volume':
            target_volume_tags_obj = TargetTags(**tags)
    return target_instance_tags_obj, target_volume_tags_obj


def launch_template_obj_builder(row):

    launch_template_obj = LaunchTemplateSettings()
    launch_template_network_obj = LaunchNetworkSettings()
    launch_template_instace_tags_obj = TargetTags(ResourceType='instance')
    launch_template_volume_tags_obj = TargetTags(ResourceType='volume')
    launch_template_instance_role_obj = InstanceRoleSettings()

    launch_template_obj.InstanceType = row[10].lower()
    launch_template_obj.KeyName = row[11]
    launch_template_obj.ImageId = row[12]
    launch_template_network_obj = ast.literal_eval(row[13])
    launch_template_obj.NetworkInterfaces = launch_template_network_obj
    launch_template_disk_obj = ast.literal_eval(row[14])
    launch_template_obj.BlockDeviceMappings = launch_template_disk_obj
    launch_template_instance_role_obj.Name = row[15]
    launch_template_obj.IamInstanceProfile = launch_template_instance_role_obj

    launch_template_obj.TagSpecifications = []
    launch_template_instace_tags_obj.Tags = ast.literal_eval(row[16])
    launch_template_volume_tags_obj.Tags = ast.literal_eval(row[17])
    launch_template_obj.TagSpecifications.append(launch_template_instace_tags_obj)
    launch_template_obj.TagSpecifications.append(launch_template_volume_tags_obj)

    return launch_template_obj
