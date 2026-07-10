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
import boto3

class AWSClients:
    def __init__(self, region, profile=None):
        if profile:
            boto3.setup_default_session(profile_name=profile)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.s3control = boto3.client('s3control', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.kms = boto3.client('kms', region_name=region)
        self.cloudtrail = boto3.client('cloudtrail', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.mwaa = boto3.client('mwaa', region_name=region)
        self.cw = boto3.client('cloudwatch', region_name=region)
