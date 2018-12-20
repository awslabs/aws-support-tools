prerequisite:

-For RHEL based Distros, please install aws cli if it’s not already installed following the below Doc:
https://docs.aws.amazon.com/cli/latest/userguide/install-linux.html



- You can use this script measure the Aggregate EBS throughput of your EC2 instance.

- The script will install sysstat package as main tool for gathering the required statistics.

- The script will show the aggreagte throughput for Disk IOPS you are doing on your linux instance.

- The script will also push the aggregated throughput as CloudWatch metric and you have full control on the granularity of the Clodwatch metric up to 1 second.


- The script is only compatible with Amazon Linux, Redhat, and CentOS Instances but can be easily customized to do the same job on other Linux distributions. 

- The script accepts only numerical argument which identify the frequency for running the loop that's gathering the data & pushing metrics to Cloudwatch.

------- Running the script -------

Place the script on your instance and make it executable


The below IAM policy has to be attached to the instance via IAM role for being able to push the CloudWatch metrics.
 
 
 
    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "cloudwatch:ListMetrics",
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:PutMetricData",
                "autoscaling:DescribeAutoScalingInstances"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
    }
    



$chmod +x ebs-stats.sh

Run the script as a "root" user or "sudo" otherwise it may fail.
<sleep interval>:is the amount of seconds between each data point.
$sudo ./ebs-stats.sh <sleep interval>

