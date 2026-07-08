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
import json
import os
import time
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError, ProfileNotFound
from aws_clients import AWSClients
from report_writer import ReportWriter
from utils import get_account_id, get_inline_policies

class AirflowVerifier:
    def __init__(self, clients: AWSClients, report: ReportWriter, env, region, env_name):
        self.mwaa = clients.mwaa
        self.s3 = clients.s3
        self.iam = clients.iam
        self.report = report
        self.env = env
        self.region = region
        self.env_name = env_name

    def check_airflow_rest_api_iam(self):
        ''' Check which airflow roles (Admin, Op, User, etc.) have access to call REST API using IAM simulation to check policy permissions'''
        account_id = get_account_id(self.env)
        airflow_roles = {"Admin":"", "Op":"", "User":"", "Viewer":"", "Public":""}
        policies = self.iam.list_attached_role_policies(
            RoleName=self.env["ExecutionRoleArn"].split("/")[-1]
        )["AttachedPolicies"]
        policy_list = []
        for policy in policies:
            policy_arn = policy["PolicyArn"]
            policy_version = self.iam.get_policy(PolicyArn=policy_arn)['Policy']['DefaultVersionId']
            policy_doc = self.iam.get_policy_version(PolicyArn=policy_arn,
                                                    VersionId=policy_version)['PolicyVersion']['Document']
            policy_list.append(json.dumps(policy_doc))
        policy_list.extend(get_inline_policies(self.iam, self.env['ExecutionRoleArn'].split("/")[-1]))
        for role in airflow_roles.keys():
            results = self.iam.simulate_custom_policy(
                    PolicyInputList=policy_list,
                    ActionNames=[
                        "airflow:InvokeRestApi"
                    ],
                    ResourceArns=[
                        "arn:aws:airflow:" + self.region + ":" + account_id + ":role/" + self.env_name + "/" + role
                    ]
                )["EvaluationResults"]
        
            for result in results:
                airflow_roles[result["EvalResourceName"].split("/")[-1]] = result["EvalDecision"]

        if "allowed" in airflow_roles.values():
            self.report.write_all_locations("🔐 The following Airflow roles have IAM permissions to access the Airflow REST API: ")
            for role in airflow_roles.keys():
                if airflow_roles[role] == "allowed":
                    self.report.write_all_locations(role, end=" ")
            self.report.write_all_locations("\n")

        if list(airflow_roles.values()).count("allowed") < len(airflow_roles.values()):
            self.report.write_all_locations("🔒 The following Airflow roles do not have IAM permissions to access the Airflow REST API: ")
            for role in airflow_roles.keys():
                if airflow_roles[role] != "allowed":
                    self.report.write_all_locations(role, end=" ")
            self.report.write_all_locations("\n")
        return airflow_roles


    def check_airflow_rest_api_health(self):
        '''
        Check if Airflow REST API invocation to GET /health endpoint succeeds,
        output the API response that includes status and heartbeat of Airflow components.
        '''
        request_params = {
            "Name": self.env["Name"],
            "Path": "/monitor/health" if int(self.env["AirflowVersion"].split(".")[0]) >= 3 else "/health",
            "Method": "GET"
            }

        self.report.write_all_locations("Airflow REST API /health endpoint is invoked.")

        try:
            response = self.mwaa.invoke_rest_api(
                **request_params
            )
        except ClientError as client_error:
            self.report.write_all_locations("🚫 Airflow REST API invocation failed with the following error:\n", client_error)
            return

        self.report.write_all_locations("✅ Airflow REST API invocation succeeded.")

        for component, info in response['RestApiResponse'].items():
            status = info['status']
            emoji = '✅' if status == 'healthy' else '🚫'
            self.report.write_all_locations(f"{emoji} {component.replace('_', ' ').title()}: {status}")
            
            # Find heartbeat key
            heartbeat_key = next((k for k in info.keys() if 'heartbeat' in k), None)
            if heartbeat_key:
                heartbeat = info[heartbeat_key].split('T')[0] + ' ' + info[heartbeat_key].split('T')[1][:8]
                self.report.write_full_report(f"   Last heartbeat: {heartbeat}")
            else:
                self.report.write_full_report(f"   This resource does not publish a heartbeat")

    def check_airflow_rest_api(self):
        ''' Perform REST API IAM access check, ask user permission to invoke API, perform health entpoint invocation check'''
        self.report.write_all_locations("### Airflow REST API")

        roles_rest_api_allowed_status = self.check_airflow_rest_api_iam()

        if "allowed" in roles_rest_api_allowed_status.values():
            print("Do you allow the following tests to trigger Airflow REST API and access inside your Airflow environment?\n" +
                "The gathered information will be saved on your device. It will not be shared with AWS.")
            if input("(Y/n):").lower().strip() in ["y", "yes", ""]:
                print()
                self.check_airflow_rest_api_health()
            else:
                self.report.write_all_locations("Skipping Airflow REST API test because user did not allow test to access REST API")
        else:
            self.report.write_all_locations("Skipping Airflow REST API test because no role have IAM permissions to access REST API.")
            self.report.write_all_locations("If you would like to allow REST API access: https://docs.aws.amazon.com/mwaa/latest/userguide/access-mwaa-apache-airflow-rest-api.html#granting-access-MWAA-Enhanced-REST-API")

    def check_airflowignore(self):
        common_ignores = [".ipynb_checkpoints", ".git", "__pycache__"]
        self.report.write_all_locations("### Check `.airflowignore`")
        
        print("Do you allow the following test to use the S3 API to read your dags folder structure including subfolders and filenames?")
        if input("(Y/n):").lower().strip() not in ["y", "yes", ""]:
            self.report.write_all_locations("Skipping Airflow ignore test because user did not allow test to read dags folder structure.")
            return
        
        print()
        
        bucket_name = self.env['SourceBucketArn'].split(':')[-1]
        dags_prefix = self.env['DagS3Path']
        
        files_and_folders = []

        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=dags_prefix)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files_and_folders.append(obj['Key'])
        except Exception as e:
            self.report.write_all_locations(f"Error reading S3 folder structure: {e}")
        
        found_paths_in_dags = []
        found_names_in_dags = []
        for path in files_and_folders:
            for ignore in common_ignores:
                if ignore in path:
                    found_paths_in_dags.append(path)
                    found_names_in_dags.append(ignore)
        
        if not found_paths_in_dags:
            self.report.write_all_locations("✅ The dags folder does not include any folder names that are knwon to be commonly included by mistake.")
            return
        
        self.report.write_full_report("The dags folder includes the following folders / files that might be included by mistake:")
        for path in found_paths_in_dags:
            self.report.write_full_report("   ", path)

        if (dags_prefix + ".airflowignore") not in files_and_folders:
            self.report.write_all_locations("⚠️ The dags folder does not include a .airflowignore file but includes the following folders / files that might be included by mistake:")
            for path in found_paths_in_dags:
                self.report.write_all_locations("   ", path)
            self.report.write_all_locations("Consider adding a .airflowignore file to your dags folder to exclude these folders / files.")
            return

        self.report.write_all_locations("✅ The dags folder includes a .airflowignore file.")
        print("Do you allow the test to read the .airflowignore file?")
        if input("(Y/n):").lower().strip() not in ["y", "yes", ""]:
            self.report.write_all_locations("Skipping reading .airflowignore file because user did not allow read.")
            return

        airflowignore_content = None
        try:
            response = self.s3.get_object(Bucket=bucket_name, Key=dags_prefix + ".airflowignore")
            airflowignore_content = response['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.report.write_all_locations("⚠️ .airflowignore file not found at location:", dags_prefix + ".airflowignore")
            else:
                self.report.write_all_locations(f"Error reading .airflowignore file: {e}")

        all_ignores_found = True
        for ignore in found_names_in_dags:
            if ignore not in airflowignore_content:
                self.report.write_all_locations("⚠️ The .airflowignore file does not include", ignore, "but it is present in your dags folder. Please consider if this is intentional or by mistake.")
                all_ignores_found = False
            else:
                self.report.write_full_report("✅ Found", ignore, "in .airflowignore file on lines:\n\n```")
                self.report.write_full_report("\n".join([line for line in airflowignore_content.splitlines() if ignore in line]),"\n```")

        if all_ignores_found:
            self.report.write_all_locations("✅ No immediate issue found with .airflowignore. Note that this check does not cover all potential issues with .airflowignore")

    def check_full_dag_run(self):
        """
        Test a full DAG run using the MWAA REST API to trigger and monitor a simple test DAG
        """
        self.report.write_all_locations("### Full DAG Run Test")
        
        print("Do you allow the following test to:")
        print("    1. Use Airflow REST API to check if MWAA_TEST_DAG.py is already uploaded.")
        print("    2. Upload MWAA_TEST_DAG.py if not found.")
        print("    3. Use Airflow REST API to invoke the dag run")
        print("The gathered information will be saved on your device. It will not be shared with AWS.")
        if input("(Y/n):").lower().strip() not in ["y", "yes", ""]:
            self.report.write_all_locations("Skipping full DAG run test because user did not give permission.")
            return
        print()
        
        dag_id = "mwaa_test_dag"
        
        # First, check if the DAG exists
        dag_request_params = {
            "Name": self.env["Name"],
            "Path": f"/dags/{dag_id}",
            "Method": "GET"
        }
        
        status_code = 400
        dag_response = None
        try:
            dag_response =  self.mwaa.invoke_rest_api(**dag_request_params)
        except ClientError as client_error:
            dag_response = client_error.response
        status_code = dag_response.get('RestApiStatusCode')

        if status_code == 200:
            self.report.write_all_locations(f"✅ Test DAG '{dag_id}' is found in the environment.") 
        elif status_code == 404:
            self.report.write_all_locations(f"Test DAG '{dag_id}' not found in the environment. Uploading...")
            self.upload_file_to_dags_folder(self.env, os.path.join(os.path.dirname(os.path.realpath(__file__)), "MWAA_TEST_DAG.py"), self.s3)

            print("Waiting for DAG to be uploaded and recognized by Airflow. This can take up to 10 minutes.")

            dag_found = False
            for i in range(30):
                try:
                    dag_response =  self.mwaa.invoke_rest_api(**dag_request_params)
                except ClientError as client_error:
                    dag_response = client_error.response
                status_code = dag_response.get('RestApiStatusCode')
                if status_code == 200:
                    dag_found = True
                    break
                elif status_code != 404:
                    self.report.write_all_locations(f"🚫 Error checking if upload is successful:", dag_response.get('RestApiResponse', {}))
                    return
                print(f"DAG is not recognized by Airflow yet. Waiting... (elapsed {(i+1)*20}s)")
                time.sleep(20)

            if not dag_found:
                self.report.write_all_locations("🚫 Automatic upload failed.")
                self.report.write_all_locations("Please upload MWAA_TEST_DAG.py to your DAGs folder.")
                return
            
            self.report.write_all_locations(f"✅ Test DAG '{dag_id}' is uploaded.")
        else:
            self.report.write_all_locations(f"🚫 Failed to check if test DAG '{dag_id}' exists:", dag_response.get('RestApiResponse', {}))
            return
        
        self.perform_dag_run(dag_id)

        print("Do you want to delete the dag used for the test?")
        if input("(y/N):").lower().strip() in ["y", "yes"]:
            self.delete_file_from_dags_folder(self.env, os.path.join(os.path.dirname(os.path.realpath(__file__)), "MWAA_TEST_DAG.py"), self.s3)
            self.report.write_all_locations(f"✅ Test DAG '{dag_id}' is deleted.")
        else:
            self.report.write_all_locations(f"✅ The user selected to keep the test DAG '{dag_id}'.")

    def perform_dag_run(self, dag_id):
        '''
        Given the ID of a DAG already available in your environment, 
        1. unpause the DAG, 
        2. trigger a dag run, 
        3. monitor the dag run until it is done. 
        '''
        # Unpause and trigger the DAG run
        try:
            unpause_request_params = {
                "Name": self.env["Name"],
                "Path": f"/dags/{dag_id}",
                "Method": "PATCH",
                "Body": {"is_paused": False}
            }
            unpause_response = self.mwaa.invoke_rest_api(**unpause_request_params)
            
            if unpause_response.get('RestApiStatusCode') not in [200, 201]:
                self.report.write_all_locations("🚫 Failed to unpause DAG:", unpause_response.get('RestApiResponse', {}))
                return
                
        except ClientError as client_error:
            self.report.write_all_locations("🚫 Failed to unpause DAG:", client_error.response)
            return
        
        self.report.write_all_locations(f"✅ DAG '{dag_id}' unpaused successfully")

        try:
            dag_run_id = f"test_run_{int(time.time())}"
            trigger_request_params = {
                "Name": self.env["Name"],
                "Path": f"/dags/{dag_id}/dagRuns",
                "Method": "POST",
                "Body": {
                    "dag_run_id": dag_run_id,
                    "logical_date": datetime.now(timezone.utc).isoformat(),
                    "conf": {}
                }
            }
            trigger_response = self.mwaa.invoke_rest_api(**trigger_request_params)
            
            if trigger_response.get('RestApiStatusCode') not in [200, 201]:
                self.report.write_all_locations("🚫 Failed to trigger DAG run:", trigger_response.get('RestApiResponse', {}))
                return
                
        except ClientError as client_error:
            self.report.write_all_locations("🚫 Failed to trigger DAG run:", client_error.response)
            return
        
        self.report.write_all_locations(f"✅ Successfully triggered DAG run with ID: {dag_run_id}")

        # Monitor the DAG run status
        print("Monitoring DAG run progress...")
        
        max_wait_time = 300  # 5 minutes
        check_interval = 10  # 10 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                status_request_params = {
                    "Name": self.env["Name"],
                    "Path": f"/dags/{dag_id}/dagRuns/{dag_run_id}",
                    "Method": "GET"
                }
                
                status_response = self.mwaa.invoke_rest_api(**status_request_params)
                dag_run_info = status_response.get('RestApiResponse', {})
                
                state = dag_run_info.get('state', 'unknown')
                
                if state == 'success':
                    self.report.write_all_locations(f"✅ DAG run completed successfully!")
                    self.report.write_all_locations(f"   Start time: {dag_run_info.get('start_date', 'N/A')}")
                    self.report.write_all_locations(f"   End time: {dag_run_info.get('end_date', 'N/A')}")
                    
                    # Get task instances to show detailed results
                    try:
                        tasks_request_params = {
                            "Name": self.env["Name"],
                            "Path": f"/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances",
                            "Method": "GET"
                        }
                        
                        tasks_response = self.mwaa.invoke_rest_api(**tasks_request_params)
                        task_instances = tasks_response.get('RestApiResponse', {}).get('task_instances', [])
                        
                        self.report.write_all_locations("Task execution results:")
                        for task in task_instances:
                            task_state = task.get('state', 'unknown')
                            task_emoji = '✅' if task_state == 'success' else '🚫'
                            self.report.write_all_locations(f"   {task_emoji} {task.get('task_id', 'unknown')}: {task_state}")
                            
                    except ClientError:
                        self.report.write_full_report("Could not retrieve detailed task information")
                    
                    return
                    
                elif state == 'failed':
                    self.report.write_all_locations(f"🚫 DAG run failed!")
                    self.report.write_all_locations(f"   Start time: {dag_run_info.get('start_date', 'N/A')}")
                    self.report.write_all_locations(f"   End time: {dag_run_info.get('end_date', 'N/A')}")
                    return
                    
                elif state in ['running', 'queued']:
                    print(f"DAG run status: {state} (elapsed: {elapsed_time}s)")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
                else:
                    self.report.write_all_locations(f"⚠️ DAG run in unexpected state: {state}")
                    return
                    
            except ClientError as client_error:
                self.report.write_all_locations("🚫 Failed to check DAG run status:", client_error.response['Error']['Message'])
                return
        
        # If we reach here, the DAG run timed out
        self.report.write_all_locations(f"⚠️ DAG run monitoring timed out after {max_wait_time} seconds.")
        self.report.write_all_locations("The DAG may still be running. Check the Airflow UI for current status.")


    @staticmethod
    def upload_file_to_dags_folder(env, file_path, s3_client):
        """
        Upload a file to the environment's DAGs folder in S3
        
        Args:
            env: MWAA environment dict containing SourceBucketArn and DagS3Path
            file_path: Local path to file to upload
            s3_client: Boto3 S3 client
        """
        # Get bucket name from ARN
        bucket_name = env['SourceBucketArn'].split(':')[-1]
        # Get file name from path
        file_name = file_path.split('/')[-1]
        s3_key = env['DagS3Path'] + file_name
        
        try:
            s3_client.upload_file(file_path, bucket_name, s3_key)
            return True
            
        except ClientError as e:
            print(f"Error uploading file to S3: {e}")
            return False

    @staticmethod
    def delete_file_from_dags_folder(env, file_path, s3_client):
        """
        Delete a file from the environment's DAGs folder in S3
        
        Args:
            env: MWAA environment dict containing SourceBucketArn and DagS3Path 
            file_path: Local path to file to delete
            s3_client: Boto3 S3 client
        """
        # Get bucket name from ARN
        bucket_name = env['SourceBucketArn'].split(':')[-1]
        # Get file name from path 
        file_name = file_path.split('/')[-1]
        s3_key = env['DagS3Path'] + file_name
        
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            return True
            
        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False

    def check_airflow_config(self):
        self.report.write_all_locations("### Airflow Configuration")
        config = self.env["AirflowConfigurationOptions"]

        config_test_passed = True
        if "celery.worker_concurrency" in config.keys():
            self.report.write_all_locations("🚫 MWAA ignores / overrides values specified for celery.worker_concurrency option.")
            self.report.write_all_locations("For more info: https://docs.aws.amazon.com/mwaa/latest/userguide/best-practices-tuning.html#best-practices-tuning-tasks-params")
            config_test_passed = False

        plugins_path = self.env.get("PluginsS3Path", None)
        if (plugins_path != None) and (config.get("core.lazy_load_plugins", "True") == "True"):
            self.report.write_all_locations("If you're using custom plugins in Apache Airflow v2, you must add `core.lazy_load_plugins : False` \n" \
                                        "as an Apache Airflow configuration option to load plugins at the start of each Airflow process to \n" \
                                        "override the default setting.")
            config_test_passed = False

        if config_test_passed:
            self.report.write_all_locations("✅ No immediate issue found with Airflow configuration. Note that this check does not cover all potential issues with Airflow configurations.")
        else:
            self.report.write_all_locations("⚠️ Please consider the messages above for potential Airflow configuration issues.")
