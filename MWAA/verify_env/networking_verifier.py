# This Python file uses the following encoding: utf-8
'''
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
import socket
import time
from botocore.exceptions import ClientError
from aws_clients import AWSClients
from report_writer import ReportWriter
from utils import get_account_id

class NetworkingVerifier:
    def __init__(self, clients: AWSClients, report: ReportWriter, env, region, partition, top_level_domain):
        self.ec2 = clients.ec2
        self.s3 = clients.s3
        self.s3control = clients.s3control
        self.ssm = clients.ssm
        self.report = report
        self.env = env
        self.region = region
        self.partition = partition
        self.top_level_domain = top_level_domain

    def check_nacl(self, input_subnets, input_subnet_ids):
        '''
        check to see if the nacls for the subnets have port 5432 if they're even listing any specific ports
        '''
        nacls = self.ec2.describe_network_acls(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [input_subnets[0]['VpcId']]
                },
                {
                    'Name': 'association.subnet-id',
                    'Values': input_subnet_ids
                }
            ]
        )['NetworkAcls']
        self.report.write_all_locations("### Verify nACLs on subnets")
        nacl_issue_detected = False
        for nacl in nacls:
            egress_acls = [acl for acl in nacl['Entries'] if acl['Egress']]
            ingress_acls = [acl for acl in nacl['Entries'] if not acl['Egress']]
            src_egress_check_pass = self._check_egress_acls(egress_acls, 5432)
            src_ingress_check_pass = self._check_ingress_acls(ingress_acls, 5432, 5432)
            if src_egress_check_pass:
                self.report.write_full_report("✅ nacl:", nacl['NetworkAclId'], "allows port 5432 on egress")
            else:
                self.report.write_all_locations("🚫 nacl:", nacl['NetworkAclId'], "denied port 5432 on egress")
            if src_ingress_check_pass:
                self.report.write_full_report("✅ nacl:", nacl['NetworkAclId'], "allows port 5432 on ingress")
            else:
                self.report.write_all_locations("🚫 nacl:", nacl['NetworkAclId'], "denied port 5432 on ingress")

        if nacl_issue_detected:
            self.report.write_all_locations("⚠️", "Please investigate the nacl issue.")
        else:
            self.report.write_all_locations("✅", "All nacls are as expected.")

    @staticmethod
    def _check_egress_acls(acls, dst_port):
        '''
        method to check egress rules and if they allow port 5432. We don't know the destination IP so we ignore cider group
        taken from
        https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-awssupport-connectivitytroubleshooter.html
        '''
        for acl in acls:
            # check ipv4 acl rule only
            if acl.get('CidrBlock'):
                # Check Port
                if ((acl.get('Protocol') == '-1') or
                (dst_port in range(acl['PortRange']['From'], acl['PortRange']['To'] + 1))):
                    # Check Action
                    return acl['RuleAction'] == 'allow'
        return ""

    @staticmethod
    def _check_ingress_acls(acls, src_port_from, src_port_to):
        '''
        same as check_egress_acls but for ingress
        '''
        for acl in acls:
            # check ipv4 acl rule only
            if acl.get('CidrBlock'):
                # Check Port
                test_range = range(src_port_from, src_port_to)
                set_test_range = set(test_range)
                if ((acl.get('Protocol') == '-1') or
                set_test_range.issubset(range(acl['PortRange']['From'], acl['PortRange']['To'] + 1))):
                    # Check Action
                    return acl['RuleAction'] == 'allow'
        return ""

    def check_routes(self, input_subnets, input_subnet_ids):
        '''
        method to check and make sure routes have access to the internet if public and subnets are private
        '''
        # vpc should be the same so I just took the first one
        routes = self.ec2.describe_route_tables(Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [input_subnets[0]['VpcId']]
                },
                {
                    'Name': 'association.subnet-id',
                    'Values': input_subnet_ids
                }
        ])
        # check subnets are private
        self.report.write_all_locations("### Verify route table validity")
        route_issue_detected = False
        for route_table in routes['RouteTables']:
            has_nat = False
            for route in route_table['Routes']:
                if route['State'] == "blackhole":
                    self.report.write_all_locations("🚫 Route:", route_table['RouteTableId'], 'has a state of blackhole.')
                    route_issue_detected = True
                if 'GatewayId' in route and route['GatewayId'].startswith('igw'):
                    self.report.write_all_locations('🚫 Route:', route_table['RouteTableId'],
                        'has a route to IGW making the subnet public. Needs to be private.')
                    self.report.write_all_locations('please review ',
                        'https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html#vpc-create-required')
                    route_issue_detected = True
                if 'NatGatewayId' in route:
                    has_nat = True
            if has_nat:
                self.report.write_full_report('✅ Route Table', route_table['RouteTableId'], 'does have a route to a NAT Gateway.')
            if not has_nat:
                self.report.write_full_report('Route Table:', route_table['RouteTableId'], 'does not have a route to a NAT Gateway')
                self.report.write_full_report('Checking for VPC endpoints to airflow, s3, sqs, kms, ecr, and monitoring...')
                endpoint_issue_detected = self.check_service_vpc_endpoints(input_subnets)
                if endpoint_issue_detected:
                    route_issue_detected = True
        if route_issue_detected:
            self.report.write_all_locations("⚠️", "Please investigate the route issue.")
        else:
            self.report.write_all_locations("✅", "All routes are as expected.")

    def check_service_vpc_endpoints(self, subnets):
        '''
        should be used if the environment does not have internet access through NAT Gateway
        '''
        top_level_domain = ".".join(reversed(self.top_level_domain.split(".")))
        service_endpoints = [
            top_level_domain +  self.region + '.airflow.api',
            top_level_domain +  self.region + '.airflow.env',
            top_level_domain +  self.region + '.sqs',
            top_level_domain +  self.region + '.ecr.api',
            top_level_domain +  self.region + '.ecr.dkr',
            top_level_domain +  self.region + '.kms',
            top_level_domain +  self.region + '.s3',
            top_level_domain +  self.region + '.monitoring',
            top_level_domain +  self.region + '.logs'
        ]
        if  self.partition == "aws":
            service_endpoints.append(
            top_level_domain +  self.region + '.airflow.ops', 
            )
        vpc_endpoints = self.ec2.describe_vpc_endpoints(Filters=[
            {
                'Name': 'service-name',
                'Values': service_endpoints
            },
            {
                'Name': 'vpc-id',
                'Values': [
                    subnets[0]['VpcId']
                ]
            }
        ])['VpcEndpoints']
        # filter by subnet ids here, if the vpc endpoints include the env's subnet ids then check those
        s_ids = [subnet['SubnetId'] for subnet in subnets]
        vpc_endpoints = [endpoint for endpoint in vpc_endpoints if all(subnet in endpoint['SubnetIds'] for subnet in s_ids)]
        if len(vpc_endpoints) != 9:
            self.report.write_full_report("The route for the subnets do not have a NAT gateway." +
                                    "This suggests vpc endpoints are needed to connect to:")
            self.report.write_full_report('s3, ecr, kms, sqs, monitoring, airflow.api, airflow.env.')
            self.report.write_full_report("The environment's subnets currently have these endpoints: ")
            for endpoint in vpc_endpoints:
                self.report.write_full_report(endpoint['ServiceName'])
            self.report.write_all_locations("🚫 The environment's subnets do not have these required endpoints: ")
            vpc_service_endpoints = [e['ServiceName'] for e in vpc_endpoints]
            for i, service_endpoint in enumerate(service_endpoints):
                if service_endpoint not in vpc_service_endpoints:
                    self.report.write_all_locations(service_endpoint)
            self.check_vpc_endpoint_private_dns_enabled(vpc_endpoints)
            return True
        else:
            self.report.write_full_report("✅ The route for the subnets do not have a NAT Gateway. However, there are sufficient VPC endpoints")
            return False

    def check_vpc_endpoint_private_dns_enabled(self, vpc_endpnts):
        '''short method to check if the interface's private dns option is set to true'''
        for vpc_endpnt in vpc_endpnts:
            if not vpc_endpnt['PrivateDnsEnabled'] and vpc_endpnt['VpcEndpointType'] == 'Interface':
                self.report.write_all_locations('🚫 VPC endpoint', vpc_endpnt['VpcEndpointId'], "does not have private dns enabled.")
                self.report.write_all_locations('This means that the public dns name for the service will resolve to its public IP and not')
                self.report.write_all_locations('the vpc endpoint private ip. You should enable this for use with MWAA')
            else:
                self.report.write_full_report('✅ VPC endpoint', vpc_endpnt['VpcEndpointId'], "has private dns enabled.")

    def check_security_groups(self):
        '''
        check MWAA environment's security groups for:
            - have at least 1 rule
            - checks ingress to see if sg allows itself
            - egress is checked by SSM document for 443 and 5432
        '''
        security_groups = self.env['NetworkConfiguration']['SecurityGroupIds']
        groups = self.ec2.describe_security_groups(
            GroupIds=security_groups
        )['SecurityGroups']
        # have a sanity check on ingress and egress to make sure it allows something
        self.report.write_all_locations('### Trying to verify ingress on security groups...')
        ingress_self_allowed = True
        for security_group in groups:
            ingress = security_group['IpPermissions']
            egress = security_group['IpPermissionsEgress']
            if not ingress:
                self.report.write_all_locations('🚫 Ingress for security group: ', security_group['GroupId'], ' requires at least one rule')
                ingress_self_allowed = False
                break
            if not egress:
                self.report.write_all_locations('🚫 Egress for security group: ', security_group['GroupId'], ' requires at least one rule')
                break
            # check security groups to ensure port at least the same security group or everything is allowed ingress
            for rule in ingress:
                if rule['IpProtocol'] == "-1":
                    if rule['UserIdGroupPairs'] and not (
                        any(x['GroupId'] == security_group['GroupId'] for x in rule['UserIdGroupPairs'])
                    ):
                        ingress_self_allowed = False
                        break
        if ingress_self_allowed:
            self.report.write_all_locations("✅ Ingress for security groups have at least 1 rule to allow itself.")
        else:
            self.report.write_all_locations("🚫 Ingress for security groups do not have at least 1 rule to allow itself.")

    def check_s3_block_public_access(self):
        '''check s3 bucket or account and make sure "block public access" is enabled'''
        self.report.write_all_locations("### Verifying 'block public access' is enabled on the s3 bucket or account")
        account_id = get_account_id(self.env)
        bucket_arn = self.env['SourceBucketArn']
        bucket_name = bucket_arn.split(':')[-1]

        if any([self._check_access_blocked('bucket', self.s3, Bucket=bucket_name),
                self._check_access_blocked('account', self.s3control, AccountId=account_id)]):
            self.report.write_all_locations(f'✅ s3 bucket, {bucket_arn}, or account blocks public access.')
        else:
            self.report.write_all_locations(f'🚫 s3 bucket, {bucket_arn}, or account does NOT block public access.')

    def _check_access_blocked(self, block_config_type, client, **request_kwargs):
        '''
        Checks whether public access is blocked for <block_config_type> (either
        bucket or account) using the client and args passed in.
        '''
        self.report.write_all_locations('Checking if public access is blocked at the {config_type} level'.format(config_type=block_config_type))
        try:
            public_access_block = client.get_public_access_block(**request_kwargs)
        except ClientError as client_error:
            # The same client error is thrown for both account level and bucket level configs
            self.report.write_all_locations('The {config_type} level access block config is not set'.format(config_type=block_config_type))
            if client_error.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                # If the config isn't set then act as if it's public
                return False
            # if it's any other exception scenario, the user is notified of the exception
            self.report.write_all_locations('⚠️ Unexpected error while checking public access block config:', client_error.response)
            return False

        # If we successfully got a config, public access is only fully blocked
        # when all four Block Public Access settings are enabled
        config = public_access_block['PublicAccessBlockConfiguration']
        return all(config.get(setting, False) for setting in (
            'BlockPublicAcls',
            'IgnorePublicAcls',
            'BlockPublicPolicy',
            'RestrictPublicBuckets',
        ))

    def get_mwaa_utilized_services(self, vpc):
        '''return an array objects for the services checking for ecr.dks and if it exists add it to the array'''
        mwaa_utilized_services = [{"service": 'sqs.' + self.region + self.top_level_domain, "port": "443"},
                                {"service": 'api.ecr.' + self.region + self.top_level_domain, "port": "443"},
                                {"service": 'monitoring.' + self.region + self.top_level_domain, "port": "443"},
                                {"service": 'kms.' + self.region + self.top_level_domain, "port": "443"},
                                {"service": 's3.' + self.region + self.top_level_domain, "port": "443"},
                                {"service": 'env.airflow.' + self.region + self.top_level_domain, "port": "443"},
                                {"service": 'env.airflow.' + self.region + self.top_level_domain, "port": "5432"},
                                {"service": 'api.airflow.' + self.region + self.top_level_domain, "port": "443"},
                                {"service": 'logs.' + self.region + self.top_level_domain, "port": "443"}]
        if self.partition == 'aws':
            mwaa_utilized_services.append(
                                {"service": 'ops.airflow.' + self.region + self.top_level_domain, "port": "443"}
            )
        ecr_dks_endpoint = self.ec2.describe_vpc_endpoints(Filters=[
            {
                'Name': 'service-name',
                'Values': ['com.amazonaws.us-east-1.ecr.dkr']
            },
            {
                'Name': 'vpc-id',
                'Values': [vpc]
            },
            {
                'Name': 'vpc-endpoint-type',
                'Values': ['Interface']
            }
        ])['VpcEndpoints']
        if ecr_dks_endpoint:
            mwaa_utilized_services.append({"service": 'dkr.ecr.' + self.region + self.top_level_domain, "port": "443"})
        return mwaa_utilized_services


    def check_connectivity_to_dep_services(self, input_subnets, subnet_ids):
        '''
        uses ssm document AWSSupport-ConnectivityTroubleshooter to check connectivity between MWAA's enis
        and a list of services. More information on this document can be found here
        https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-awssupport-connectivitytroubleshooter.html
        '''
        vpc = input_subnets[0]['VpcId']
        mwaa_utilized_services = self.get_mwaa_utilized_services(vpc)

        self.report.write_all_locations("### Connectivity Check via ENIs\nPlease see the full report for results if no error in output.")
        self.report.write_full_report("Testing connectivity to the following service endpoints from MWAA enis...")
        security_groups = self.env['NetworkConfiguration']['SecurityGroupIds']
        for service in mwaa_utilized_services:
            # retry 5 times for just one of the enis the service uses
            for i in range(0, 5):
                try:
                    # get ENIs used by MWAA
                    enis = self._get_enis(subnet_ids, vpc, security_groups)
                    if not enis:
                        self.report.write_all_locations("🚫 no enis found for MWAA, exiting test for ", service['service'])
                        self.report.write_all_locations("please try accessing the airflow UI and then try running this script again")
                        break
                    eni = list(enis.values())[0]
                    interface_ip = self.ec2.describe_network_interfaces(
                        NetworkInterfaceIds=[eni]
                    )['NetworkInterfaces'][0]['PrivateIpAddress']
                    ssm_execution_id = ''
                    ssm_execution_id = self.ssm.start_automation_execution(
                        DocumentName='AWSSupport-ConnectivityTroubleshooter',
                        DocumentVersion='$DEFAULT',
                        Parameters={
                            'SourceIP': [interface_ip],
                            'DestinationIP': [self.get_ip_address(service['service'], input_subnets[0]['VpcId'])],
                            'DestinationPort': [service['port']],
                            'SourceVpc': [vpc],
                            'DestinationVpc': [vpc],
                            'SourcePortRange': ["0-65535"]
                        }
                    )['AutomationExecutionId']
                    self._wait_for_ssm_step_one_to_finish(ssm_execution_id)
                    execution = self.ssm.get_automation_execution(
                        AutomationExecutionId=ssm_execution_id
                    )['AutomationExecution']
                    # check if the failure is due to not finding the eni. If it is, retry testing the service again
                    if execution['StepExecutions'][0]['StepStatus'] != 'Failed':
                        self.report.write_full_report('Testing connectivity between eni', eni, "with private ip of",
                            interface_ip, "and", service['service'], "on port", service['port'])
                        self.report.write_full_report("Please follow this link to view the results of the test:")
                        self.report.write_full_report("https://console.aws.amazon.com/systems-manager/automation/execution/" + ssm_execution_id +
                            "?self.region=" + self.region + "\n")
                        break
                except ClientError as client_error:
                    self.report.write_all_locations('🚫 Attempt', i, 'encountered error', client_error.response['Error']['Message'], ' retrying...')

    def _wait_for_ssm_step_one_to_finish(self, ssm_execution_id):
        '''
        check if the first step finished because that will do the test on the IP to get the eni.
        The eni changes to quickly that sometimes this fails so I retry till it works
        '''
        execution = self.ssm.get_automation_execution(
            AutomationExecutionId=ssm_execution_id
        )['AutomationExecution']['StepExecutions'][0]['StepStatus']
        while True:
            if execution in ['Success', 'TimedOut', 'Cancelled', 'Failed']:
                break
            time.sleep(5)
            execution = self.ssm.get_automation_execution(
                AutomationExecutionId=ssm_execution_id
            )['AutomationExecution']['StepExecutions'][0]['StepStatus']

    def _get_enis(self, input_subnet_ids, vpc, security_groups):
        '''
        method which returns the ENIs used by MWAA based on security groups assigned to the environment
        '''
        enis = {}
        for subnet_id in input_subnet_ids:
            interfaces = self.ec2.describe_network_interfaces(
                Filters=[
                    {
                        'Name': 'subnet-id',
                        'Values': [subnet_id]
                    },
                    {
                        'Name': 'vpc-id',
                        'Values': [vpc]
                    },
                    {
                        'Name': 'group-id',
                        'Values': security_groups
                    }
                ]
            )['NetworkInterfaces']
            for interface in interfaces:
                enis[subnet_id] = interface['NetworkInterfaceId']
        return enis

    def get_ip_address(self, hostname, vpc):
        '''
        method to get the hostname's IP address. This will first check to see if there is a VPC endpoint.
        If so, it will use that VPC endpoint's private IP. Sometimes hostnames don't resolve for various DNS reasons.
        This method retries 10 times and sleeps 1 second in between
        '''
        endpoint = self.ec2.describe_vpc_endpoints(Filters=[
            {
                'Name': 'service-name',
                'Values': [
                    '.'.join(hostname.split('.')[::-1])
                ]
            },
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc
                ]
            },
            {
                'Name': 'vpc-endpoint-type',
                'Values': [
                    'Interface'
                ]
            }
        ])['VpcEndpoints']
        if endpoint:
            hostname = endpoint[0]['DnsEntries'][0]['DnsName']
        for i in range(0, 10):
            try:
                return socket.gethostbyname(hostname)
            except socket.error:
                print("attempt", i, "failed to resolve hostname: ", hostname, " retrying...")
                time.sleep(1)


