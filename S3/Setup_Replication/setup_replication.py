#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import boto3
import json
import sys
import time

def main():
    parser = argparse.ArgumentParser(description='Setup S3 replication')
    parser.add_argument('--source-bucket', required=True)
    parser.add_argument('--source-region', default='me-central-1')
    parser.add_argument('--destination-bucket', required=True)
    parser.add_argument('--destination-region', required=True)
    parser.add_argument('--role-arn', required=False)
    args = parser.parse_args()

    source_region = args.source_region

    s3_src = boto3.client('s3', region_name=source_region)
    s3_dest = boto3.client('s3', region_name=args.destination_region)
    sts_src = boto3.client('sts', region_name=source_region)
    iam = boto3.client('iam')
    
    # Verify source bucket exists
    try:
        s3_src.head_bucket(Bucket=args.source_bucket)
    except:
        print(f"Source bucket {args.source_bucket} does not exist")
        sys.exit(1)
    
    # Check/create destination bucket
    try:
        s3_dest.head_bucket(Bucket=args.destination_bucket)
    except Exception:
        # us-east-1 does not accept a LocationConstraint ("US" is rejected with
        # InvalidLocationConstraint); the bucket must be created without one.
        if args.destination_region == 'us-east-1':
            s3_dest.create_bucket(Bucket=args.destination_bucket)
        else:
            s3_dest.create_bucket(Bucket=args.destination_bucket,
                                  CreateBucketConfiguration={'LocationConstraint': args.destination_region})

    # Replication requires versioning on the destination too, including when the
    # destination bucket already existed.
    s3_dest.put_bucket_versioning(Bucket=args.destination_bucket, VersioningConfiguration={'Status': 'Enabled'})

    # Enable versioning on source
    s3_src.put_bucket_versioning(Bucket=args.source_bucket, VersioningConfiguration={'Status': 'Enabled'})
    
    # Create or use IAM role
    role_arn = args.role_arn
    if not role_arn:
        role_name = f"s3-replication-{source_region}-{args.source_bucket}"
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": ["s3.amazonaws.com", "batchoperations.s3.amazonaws.com"]}, "Action": "sts:AssumeRole"}]
        }
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetReplicationConfiguration",
                        "s3:PutInventoryConfiguration",
                        "s3:ListBucket"
                    ],
                    "Resource": f"arn:aws:s3:::{args.source_bucket}"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObjectVersionForReplication",
                        "s3:GetObjectVersionAcl",
                        "s3:GetObjectVersionTagging",
                        "s3:InitiateReplication",
                        "s3:GetObject",
                        "s3:GetObjectVersion"
                    ],
                    "Resource": f"arn:aws:s3:::{args.source_bucket}/*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:ReplicateObject",
                        "s3:ReplicateDelete",
                        "s3:ReplicateTags",
                        "s3:ObjectOwnerOverrideToBucketOwner"
                    ],
                    "Resource": f"arn:aws:s3:::{args.destination_bucket}/*"
                }
            ]
        }
        try:
            role = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy))
            role_arn = role['Role']['Arn']
            print("Waiting 30 seconds for IAM role to propagate...")
            time.sleep(30)
        except iam.exceptions.EntityAlreadyExistsException:
            role_arn = f"arn:aws:iam::{sts_src.get_caller_identity()['Account']}:role/{role_name}"
            print(f"Role {role_name} already exists, updating policy...")
        iam.put_role_policy(RoleName=role_name, PolicyName='S3ReplicationPolicy', PolicyDocument=json.dumps(policy))
    
    # Setup replication
    replication_config = {
        'Role': role_arn,
        'Rules': [{
            'ID': 'ReplicationRule',
            'Priority': 1,
            'Status': 'Enabled',
            'Filter': {},
            'DeleteMarkerReplication': {'Status': 'Disabled'},
            'Destination': {'Bucket': f"arn:aws:s3:::{args.destination_bucket}"}
        }]
    }
    s3_src.put_bucket_replication(Bucket=args.source_bucket, ReplicationConfiguration=replication_config)
    print(f"Replication configured from {args.source_bucket} to {args.destination_bucket}")

    # Start batch replication job
    account_id = sts_src.get_caller_identity()['Account']
    s3control = boto3.client('s3control', region_name=source_region)
    
    job = s3control.create_job(
        AccountId=account_id,
        ConfirmationRequired=False,
        Operation={'S3ReplicateObject': {}},
        Report={'Enabled': False},
        ManifestGenerator={'S3JobManifestGenerator': {'SourceBucket': f'arn:aws:s3:::{args.source_bucket}', 'EnableManifestOutput': False, 'Filter': {'EligibleForReplication': True}}},
        Priority=1,
        RoleArn=role_arn
    )
    job_id = job['JobId']
    print(f"Batch replication job started: {job_id}")

    # Get job status
    job_status = s3control.describe_job(AccountId=account_id, JobId=job_id)
    print(f"Job Status: {job_status['Job']['Status']}")
    print(f"Progress: {job_status['Job'].get('ProgressSummary', {})}")


if __name__ == '__main__':
    main()
