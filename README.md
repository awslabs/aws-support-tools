# aws-support-tools

A curated collection of diagnostic and troubleshooting tools for AWS services. Each tool lives in its own folder, organized by the AWS service it targets. Most are scripts (Python, Bash, PowerShell) that help you investigate, fix, or automate something specific.

## Available tools

### API Gateway

| Tool | Description |
|------|-------------|
| [Tools](APIGateway/Tools/) | Utilities for working with API Gateway |

### CloudFormation

| Tool | Description |
|------|-------------|
| [CloudFormer](CloudFormation/CloudFormer/) | Launch the CloudFormer solution into an existing VPC (replaces VPCSelection with VpcId/SubnetId parameters) |

### Amazon Cognito

| Tool | Description |
|------|-------------|
| [decode-verify-jwt](Cognito/decode-verify-jwt/) | Decode and verify Amazon Cognito JWT tokens |
| [identity-pool-integrator-onelogin](Cognito/identity-pool-integrator-onelogin/) | Test Cognito Identity Pool integration with OneLogin SAML authentication |

### Amazon Connect

| Tool | Description |
|------|-------------|
| [DynamicOutboundCallerID](Connect/DynamicOutboundCallerID/) | Lambda function for country-based dynamic outbound caller ID in Connect instances |

### AWS Device Farm

| Tool | Description |
|------|-------------|
| [TestOutputDownloader](DeviceFarm/TestOutputDownloader/) | Download test output (logs, videos, artifacts) from a Device Farm console URL for sharing with AWS Support |

### AWS DRS (Elastic Disaster Recovery)

| Tool | Description |
|------|-------------|
| [DRS-Settings-Tool](DRS/DRS-Settings-Tool/) | Bulk-edit source server settings across multiple DRS source servers |

See also: [MGNDRS tools](#aws-mgn--drs-cross-service) for scripts that work across both MGN and DRS.

### Amazon EBS

| Tool | Description |
|------|-------------|
| [VolumeLimitCalculator](EBS/VolumeLimitCalculator/) | Calculate maximum available IOPS and throughput for a given EBS volume |

### Amazon EC2

| Tool | Description |
|------|-------------|
| [AutomateDnsmasq](EC2/AutomateDnsmasq/) | Automate Dnsmasq installation and configuration on Amazon Linux 1 and 2 |
| [EC2EBSThroughput](EC2/EC2EBSThroughput/) | Measure and report EC2-to-EBS throughput |
| [EnableIPv6](EC2/EnableIPv6/) | Enable IPv6 on EC2 instances |
| [NitroInstanceChecks](EC2/NitroInstanceChecks/) | Pre-requisite checks before migrating an instance to a Nitro instance type (NVMe module, ENA driver, etc.) |
| [QuickInstanceEC2](EC2/QuickInstanceEC2/) | Launch, deploy applications, and terminate EC2 instances using CloudFormation |

### EC2 Auto Scaling

| Tool | Description |
|------|-------------|
| [Multiple ENI Auto Scaling group](EC2%20Auto%20Scaling/) | Support tools for Auto Scaling groups with multiple ENIs |

### Amazon EKS (Elastic Kubernetes Service)

| Tool | Description |
|------|-------------|
| [subnet-fragmentation](EKS/subnet-fragmentation/) | Diagnose /28 block fragmentation in VPC subnets used for EKS prefix delegation. Identifies why a subnet with free IPs still fails prefix allocation with InsufficientCidrBlocks |

### Amazon EMR

| Tool | Description |
|------|-------------|
| [Assign_Private_IP](EMR/Assign_Private_IP/) | Attach a static private IP to the master node of an EMR cluster (usable as bootstrap action or step) |
| [Get_EMR_CLI_Export](EMR/Get_EMR_CLI_Export/) | Export EMR cluster configuration as AWS CLI commands |

### Amazon FSx for NetApp ONTAP

| Tool | Description |
|------|-------------|
| [Diagnostic Data Collection Tool](FSxNetAppONTAP/) | Collect diagnostic data from FSx for NetApp ONTAP file systems (Linux only) |

### AWS Lambda

| Tool | Description |
|------|-------------|
| [BuildLambdaLayers](Lambda/BuildLambdaLayers/) | Automate building Lambda Layers (download libraries, optionally upload and associate with a function) |
| [CheckFunctionConcurrency](Lambda/CheckFunctionConcurrency/) | Check concurrency configuration for Lambda functions in a region |
| [DeploymentPackages](Lambda/DeploymentPackages/) | Guidance for creating deployment packages with native binaries compiled for the Lambda execution environment |
| [FindEniMappings](Lambda/FindEniMappings/) | Find which Lambda functions are using a specific ENI |

### AWS MGN (Application Migration Service)

| Tool | Description |
|------|-------------|
| [MGN Toolkit (Windows)](MGN/Windows/) | **Moved.** The MGN Toolkit now lives at [awslabs/mgn-toolkit](https://github.com/awslabs/mgn-toolkit/tree/main) |

### AWS MGN + DRS (cross-service)

| Tool | Description |
|------|-------------|
| [MGNDRS-Linux-System-Details-Tool](MGNDRS/MGNDRS-Linux-System-Details-Tool/) | Gather Linux system details for troubleshooting MGN/DRS agent installation, replication, or target launch issues |

### Amazon MWAA (Managed Workflows for Apache Airflow)

| Tool | Description |
|------|-------------|
| [verify_env](MWAA/verify_env/) | Diagnose why an MWAA environment failed to create |

### AWS OpsWorks

| Tool | Description |
|------|-------------|
| [sample-cookbooks](OpsWorks/sample-cookbooks/) | Sample Chef cookbooks (e.g. cpulimit-ruby) |

### Amazon RDS

| Tool | Description |
|------|-------------|
| [MSSQL_RDS_Clone_Login](RDS/MSSQL/) | Clone SQL Server logins on RDS for SQL Server |

### Amazon S3

| Tool | Description |
|------|-------------|
| [S3_Transfer_Acceleration](S3/S3_Transfer_Acceleration/) | Support tools for S3 Transfer Acceleration |
| [Setup_Replication](S3/Setup_Replication/) | Set up S3 cross-region replication |

### Amazon SES (Simple Email Service)

| Tool | Description |
|------|-------------|
| [CheckSESQuota](SES/CheckSESQuota/) | Check SES daily sending quota usage and notify via SNS when usage exceeds 80% |
| [SESMailer](SES/SESMailer/) | Demonstrates sending email using SES without a backend |
| [SESReports](SES/SESReports/) | Lambda function that generates bounce and complaint reports, saved as searchable dashboards on S3 |

### Amazon SNS (Simple Notification Service)

| Tool | Description |
|------|-------------|
| [APNSSampleApp](SNS/APNSSampleApp/) | iOS APNs push notification test project with SNS integration |
| [FCMSampleApp](SNS/FCMSampleApp/) | Android Firebase Cloud Messaging push notification test project with SNS integration |
| [GCMSampleApp](SNS/GCMSampleApp/) | Android GCM push notification test project with SNS integration |
| [SNSFastPublish](SNS/SNSFastPublish/) | Lambda function for fast-publishing to SNS |
| [SNSReflect](SNS/SNSReflect/) | Lambda that reflects SNS notifications to another topic (useful for SMS in regions without SMS support) |

### AWS Systems Manager

| Tool | Description |
|------|-------------|
| [SSMAGENT-TOOLKIT-LINUX](Systems%20Manager/SSMAGENT-TOOLKIT-LINUX/) | Checks to diagnose why a Linux EC2 instance isn't appearing in Systems Manager |
| [SSMAgent-Toolkit-Windows](Systems%20Manager/SSMAgent-Toolkit-Windows/) | PowerShell checks to diagnose why a Windows EC2 instance isn't appearing in Managed Instances or Fleet Manager. **Note:** integrated into [ssm-cli](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-cli.html) as of SSM Agent 3.1.501.0 |

### AWS WAF

| Tool | Description |
|------|-------------|
| [WAFER](WAF/WAF-Enhanced-Replicator/) | AWS WAF Enhanced Replicator. Replicate WAF global or regional configurations |

### Amazon OpenSearch Service (formerly Elasticsearch Service)

| Tool | Description |
|------|-------------|
| [DeleteIndices](Elasticsearch%20Service/DeleteIndices/) | List and delete indices older than a specified age from an OpenSearch/Elasticsearch cluster |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to submit a new tool, fix an existing one, or report an issue.

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
