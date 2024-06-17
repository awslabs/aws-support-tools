import botocore
import boto3

class boto_client(object):
    client: botocore.client.BaseClient
    service: str
    region: str
    def __init__(self):
        self.client = boto3.client(self.service)

class drs_client(boto_client):
    service = 'drs'

class ec2_client(boto_client):
    service = 'ec2'

class iam_client(boto_client):
    service = 'iam'

class kms_client(boto_client):
    service = 'kms'
