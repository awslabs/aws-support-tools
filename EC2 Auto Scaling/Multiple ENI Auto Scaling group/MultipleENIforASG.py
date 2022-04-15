

import boto3
import botocore
import sys
from datetime import datetime

ec2_client = boto3.client('ec2')
asg_client = boto3.client('autoscaling')


def lambda_handler(event, context):
    global LifecycleHookName, AutoScalingGroupName, LifecycleActionToken, instance_id
    instance_id = event["detail"]["EC2InstanceId"]
    LifecycleHookName = event['detail']['LifecycleHookName']
    AutoScalingGroupName = event['detail']['AutoScalingGroupName']
    LifecycleActionToken = event['detail']['LifecycleActionToken']
    instance_result = ec2_client.describe_instances(InstanceIds=[instance_id])
    asg_response = asg_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[event['detail']['AutoScalingGroupName']])
    
    if event["detail"]["Destination"] == "AutoScalingGroup":

        #This function will check if the instance already has multiple ENIs attached.  If a warm pool is configured in the auto scaling group and --instance-reuse-policy ’{“ReuseOnScaleIn”: true} was configured while configuring the warm pool, a second ENI will already be attached to the instance that scaled in to the warm pool
        if check_number_of_interfaces(instance_result) > 1:
            log("The instance {} already has more than one interface attached.".format(instance_id))
            

        # If the instance is launched for the first time into the auto scaling group or from the warm pool(not scaled into warm pool instances), the following step will be executed
        else:

            subnet_id = get_subnet_id(instance_result)
            interface_id = create_interface(asg_response, instance_result, subnet_id)
            attachment = attach_interface(interface_id, instance_id)


            #Will check for error with network interface attachment. If there is any error, complete lifecycle call is run to terminate the instance        
            if interface_id and not attachment:
                log("Removing network interface {} after attachment failed.".format(interface_id))
                log('{"Error": "1"}')
                delete_interface(interface_id)
                abandon_lifecycle_action(LifecycleHookName, AutoScalingGroupName, instance_id, LifecycleActionToken)
                return

            #Modifying network interface attribute to set DeleteOnTermination as True. This ensures the interface is deleted when the instance is terminated, to prevent hitting EC2 quotas
            set_delete_true = ec2_client.modify_network_interface_attribute(
                Attachment={
                    'AttachmentId': attachment,
                    'DeleteOnTermination': True,
                },
                NetworkInterfaceId= interface_id,
            )

            log('{"Exit": "0"}')

    #Attaching of second interface is skipped if the instance is launched into the warm pool to avoid hitting network interfaces limit while the instance is not being used and is in warm pool.
    #This section is run when the instance is launched into a warm pool.
    else:
        log("Instance {} launching in warm pool. No action taken".format(instance_id))
        
    continue_lifecycle_action(LifecycleHookName, AutoScalingGroupName, instance_id, LifecycleActionToken)   
    


# check_number_of_interfaces function checks the number of interfaces attached to the instances
def check_number_of_interfaces(instance_result):
    interfaces = instance_result['Reservations'][0]['Instances'][0]['NetworkInterfaces']
    return len(interfaces)

# get_subnet_id function checks the subnet id of the instance's first ENI
def get_subnet_id(instance_result):
    try:
        vpc_subnet_id = instance_result['Reservations'][0]['Instances'][0]['SubnetId']
        log("Subnet id: {} for Instance {}".format(vpc_subnet_id,instance_id))

    except botocore.exceptions.ClientError as e:
        log("Error describing the instance {}: {}".format(instance_id, e.response['Error']['Code']))
        vpc_subnet_id = None
        abandon_lifecycle_action(LifecycleHookName, AutoScalingGroupName, instance_id, LifecycleActionToken)

    return vpc_subnet_id

# create_interface will create a new interface in the subnet that is not the subnet of the instance's first ENI
def create_interface(asg_response,instance_result,subnet_id):
    network_interface_id = None    
    try:
        string_response= asg_response["AutoScalingGroups"][0]["VPCZoneIdentifier"]
        list_response = string_response.split(",");
        instancezone= instance_result['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
        AZsubnets= []
        for item in list_response:
            zones = ec2_client.describe_subnets(SubnetIds=[item])
            azones= zones["Subnets"][0]["AvailabilityZone"]
            if azones==instancezone:
                AZsubnets.append(item)

        #checks if the AZs that the auto scaling group is enabled in has 2 subnets in each AZ
        if AZsubnets[0]== subnet_id:
            if len(AZsubnets)==1:
                log("The AZ {} has only one subnet in the auto scaling group".format(azones))
                abandon_lifecycle_action(LifecycleHookName, AutoScalingGroupName, instance_id, LifecycleActionToken)

            else:
                subnet_id=AZsubnets[1]
        else:
            subnet_id=AZsubnets[0]
        network_interface = ec2_client.create_network_interface(SubnetId=subnet_id)
        network_interface_id = network_interface['NetworkInterface']['NetworkInterfaceId']
        log("Created network interface: {} for Instance {}".format(network_interface_id,instance_id))

    except botocore.exceptions.ClientError as e:
        log("Error creating network interface: {} for Instance {}".format(e.response['Error']['Code'],instance_id))
        abandon_lifecycle_action(LifecycleHookName, AutoScalingGroupName, instance_id, LifecycleActionToken)
    return network_interface_id

#attach_interface will attach the newly created interface as the second interface
def attach_interface(network_interface_id, instance_id):
    attachment = None

    if network_interface_id and instance_id:
        try:
            attach_interface = ec2_client.attach_network_interface(
                NetworkInterfaceId=network_interface_id,
                InstanceId=instance_id,
                DeviceIndex=1
            )
            attachment = attach_interface['AttachmentId']
            log("Created network attachment: {} for Instance {}".format(attachment,instance_id))
        except botocore.exceptions.ClientError as e:
            log("Error attaching network interface: {} for Instance {}".format(e.response['Error']['Code'],instance_id))
            abandon_lifecycle_action(LifecycleHookName, AutoScalingGroupName, instance_id, LifecycleActionToken)
    return attachment

#delete_interface is run when there might be an error while attaching the secondary interface
def delete_interface(network_interface_id):
    try:
        ec2_client.delete_network_interface(
            NetworkInterfaceId=network_interface_id
        )
        return True

    except botocore.exceptions.ClientError as e:
        log("Error deleting interface {}: {}".format(network_interface_id, e.response['Error']['Code']))


#Run complete-lifecycle-action call to continue bringing the instance InService        
def continue_lifecycle_action(hookname, groupname, instance_id, tokenname):
    try:
        asg_client.complete_lifecycle_action(
        LifecycleHookName=hookname,
        AutoScalingGroupName=groupname,
        InstanceId=instance_id,
        LifecycleActionToken=tokenname,
        LifecycleActionResult='CONTINUE'
        ) 
        log("Completing Lifecycle hook for instance {} with Result:CONTINUE".format(instance_id))

    except botocore.exceptions.ClientError as e:
        log("Error completing life cycle hook for instance {}: {}".format(instance_id, e.response['Error']['Code']))
        log('{"Error": "1"}')
    return

#Run complete-lifecycle-action call to terminate the instance due to an error
def abandon_lifecycle_action(hookname,groupname,instance_id,tokenname):
    try:
        asg_client.complete_lifecycle_action(
        LifecycleHookName=hookname,
        AutoScalingGroupName=groupname,
        InstanceId=instance_id,
        LifecycleActionToken=tokenname,
        LifecycleActionResult='ABANDON'
        ) 
        log("Completing Lifecycle hook for instance {} with Result:ABANDON".format(instance_id))   
    except botocore.exceptions.ClientError as e:
        log("Error completing life cycle hook for instance {}: {}".format(instance_id, e.response['Error']['Code']))
        log('{"Error": "1"}')
    return

def log(message):
    print('{}Z {}'.format(datetime.utcnow().isoformat(), message))
