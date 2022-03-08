

import boto3
import botocore
from datetime import datetime

ec2_client = boto3.client('ec2')
asg_client = boto3.client('autoscaling')


def lambda_handler(event, context):
    if event["detail-type"] == "EC2 Instance-launch Lifecycle Action":
        instance_id = event["detail"]["EC2InstanceId"]
        subnet_id = get_subnet_id(instance_id)
        interface_id = create_interface(subnet_id, event, instance_id)
        attachment = attach_interface(interface_id, instance_id)
        delete = ec2_client.modify_network_interface_attribute(
            Attachment={
                'AttachmentId': attachment,
                'DeleteOnTermination': True,
            },
            NetworkInterfaceId= interface_id,
        )

        if interface_id and not attachment:
            log("Removing network interface {} after attachment failed.".format(interface_id))
            delete_interface(interface_id)

        try:
            asg_client.complete_lifecycle_action(
                LifecycleHookName=event['detail']['LifecycleHookName'],
                AutoScalingGroupName=event['detail']['AutoScalingGroupName'],
                LifecycleActionToken=event['detail']['LifecycleActionToken'],
                LifecycleActionResult='CONTINUE'
            )

            if attachment:
                log('{"Error": "0"}')
            else:
                log('{"Error": "1"}')

        except botocore.exceptions.ClientError as e:
            log("Error completing life cycle hook for instance {}: {}".format(instance_id, e.response['Error']['Code']))
            log('{"Error": "1"}')


def get_subnet_id(instance_id):
    try:
        result = ec2_client.describe_instances(InstanceIds=[instance_id])
        vpc_subnet_id = result['Reservations'][0]['Instances'][0]['SubnetId']
        instancezone= result['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
        log("Subnet id: {}".format(vpc_subnet_id))

    except botocore.exceptions.ClientError as e:
        log("Error describing the instance {}: {}".format(instance_id, e.response['Error']['Code']))
        vpc_subnet_id = None

    return vpc_subnet_id


def create_interface(subnet_id, event,instance_id):
    network_interface_id = None

    if subnet_id:
        try:
            asg_response = asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[event['detail']['AutoScalingGroupName']]
            )
            string_response= asg_response["AutoScalingGroups"][0]["VPCZoneIdentifier"]
            list_response = string_response.split(",");

            result = ec2_client.describe_instances(InstanceIds=[instance_id])
            instancezone= result['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
            AZsubnets= []
            for item in list_response:
                zones = ec2_client.describe_subnets(SubnetIds=[item])
                azones= zones["Subnets"][0]["AvailabilityZone"]
                if azones==instancezone:
                    AZsubnets.append(item)
            if AZsubnets[0]== subnet_id:
                subnet_id=AZsubnets[1]
            else:
                subnet_id=AZsubnets[0]
            network_interface = ec2_client.create_network_interface(SubnetId=subnet_id)
            network_interface_id = network_interface['NetworkInterface']['NetworkInterfaceId']
            log("Created network interface: {}".format(network_interface_id))
        except botocore.exceptions.ClientError as e:
            log("Error creating network interface: {}".format(e.response['Error']['Code']))

    return network_interface_id


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
            log("Created network attachment: {}".format(attachment))
        except botocore.exceptions.ClientError as e:
            log("Error attaching network interface: {}".format(e.response['Error']['Code']))

    return attachment


def delete_interface(network_interface_id):
    try:
        ec2_client.delete_network_interface(
            NetworkInterfaceId=network_interface_id
        )
        return True

    except botocore.exceptions.ClientError as e:
        log("Error deleting interface {}: {}".format(network_interface_id, e.response['Error']['Code']))


def log(message):
    print('{}Z {}'.format(datetime.utcnow().isoformat(), message))
