# Copyright 2024-2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

import boto3
import time
import argparse
from datetime import datetime, timezone

# MWAA log types as per AWS documentation
# Reference: https://docs.aws.amazon.com/mwaa/latest/userguide/monitoring-airflow.html
MWAA_LOG_TYPES = ['DAGProcessing', 'Scheduler', 'Task', 'WebServer', 'Worker']

def validate_datetime(date_str):
    """Validate datetime string format"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

def to_utc_timestamp_ms(date_str):
    """
    Convert datetime string to UTC Unix timestamp in milliseconds.
    Input is always treated as UTC regardless of local system timezone.
    """
    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

def filter_health_checks(event):
    """Filter out health check logs and other unwanted entries"""
    message = event['message']
    return not ('GET /health HTTP/1.1' in message or 
                'ELB-HealthChecker' in message)

def construct_log_group_names(environment_name):
    """
    Auto-construct CloudWatch log group names from MWAA environment name.
    Format: airflow-{EnvironmentName}-{LogType}
    Reference: https://docs.aws.amazon.com/mwaa/latest/userguide/monitoring-airflow.html
    """
    return [f"airflow-{environment_name}-{log_type}" for log_type in MWAA_LOG_TYPES]

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Fetch MWAA CloudWatch logs and upload to S3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Auto-construct log groups from environment name (fetches all log types):
  python mwaa_log_retrieval.py -n "MyAirflowEnvironment" -s "2024-07-08 13:00:00" -e "2024-07-08 14:00:00" -b "amzn-s3-demo-mwaa-logs"

  # Auto-construct but fetch only specific log types:
  python mwaa_log_retrieval.py -n "MyAirflowEnvironment" -t Task Worker -s "2024-07-08 13:00:00" -e "2024-07-08 14:00:00" -b "amzn-s3-demo-mwaa-logs"

  # Legacy: Specify log group directly (backward compatible):
  python mwaa_log_retrieval.py -l "airflow-MyAirflowEnvironment-Task" -s "2024-07-08 13:00:00" -e "2024-07-08 14:00:00" -b "amzn-s3-demo-mwaa-logs"

Note: All times are interpreted as UTC.
        '''
    )
    
    # Log group specification - either environment name OR direct log group
    log_group = parser.add_mutually_exclusive_group(required=True)
    log_group.add_argument(
        '-n', '--env-name',
        help='MWAA Environment name (auto-constructs log group names)'
    )
    log_group.add_argument(
        '-l', '--log-group',
        help='CloudWatch Log Group name (direct specification, legacy mode)'
    )
    
    parser.add_argument(
        '-t', '--log-types',
        nargs='+',
        choices=MWAA_LOG_TYPES,
        default=None,
        help=f'Log types to fetch when using -n/--env-name (default: all). Choices: {", ".join(MWAA_LOG_TYPES)}'
    )
    parser.add_argument(
        '-s', '--start',
        required=True,
        help='Start time in UTC (format: YYYY-MM-DD HH:MM:SS)'
    )
    parser.add_argument(
        '-e', '--end',
        required=True,
        help='End time in UTC (format: YYYY-MM-DD HH:MM:SS)'
    )
    parser.add_argument(
        '-b', '--bucket',
        required=True,
        help='S3 bucket name for upload'
    )
    parser.add_argument(
        '-p', '--prefix',
        default='',
        help='S3 prefix/folder (optional)'
    )
    parser.add_argument(
        '-r', '--region',
        default=None,
        help='AWS region (optional, uses default if not specified)'
    )
    
    return parser.parse_args()

def get_logs_and_upload_to_s3(log_group_name, start_time_str, end_time_str, bucket_name, s3_prefix='', region=None):
    try:
        # Initialize AWS clients
        if region:
            cloudwatch_logs = boto3.client('logs', region_name=region)
            s3_client = boto3.client('s3', region_name=region)
        else:
            cloudwatch_logs = boto3.client('logs')
            s3_client = boto3.client('s3')

        # Validate datetime inputs
        if not validate_datetime(start_time_str):
            print(f"Error: Invalid start time format: {start_time_str}")
            print("Expected format: YYYY-MM-DD HH:MM:SS")
            return False
            
        if not validate_datetime(end_time_str):
            print(f"Error: Invalid end time format: {end_time_str}")
            print("Expected format: YYYY-MM-DD HH:MM:SS")
            return False

        # Print the values being used
        print(f"\n{'='*60}")
        print(f"Configuration:")
        print(f"{'='*60}")
        print(f"Log Group    : {log_group_name}")
        print(f"Start Time   : {start_time_str} UTC")
        print(f"End Time     : {end_time_str} UTC")
        print(f"S3 Bucket    : {bucket_name}")
        print(f"S3 Prefix    : {s3_prefix if s3_prefix else 'None'}")
        print(f"AWS Region   : {region if region else 'Default'}")
        print(f"{'='*60}\n")

        # Convert datetime strings to UTC Unix timestamp (milliseconds)
        start_time = to_utc_timestamp_ms(start_time_str)
        end_time = to_utc_timestamp_ms(end_time_str)
        
        print("Fetching logs...")
        
        try:
            all_events = []
            next_token = None

            while True:
                params = {
                    'logGroupName': log_group_name,
                    'startTime': start_time,
                    'endTime': end_time,
                    'filterPattern': '-"GET /health HTTP/1.1" -"ELB-HealthChecker"'
                }
                
                if next_token:
                    params['nextToken'] = next_token
                
                response = cloudwatch_logs.filter_log_events(**params)
                
                events = response.get('events', [])
                if events:
                    all_events.extend(events)
                    print(f"Retrieved {len(all_events)} events so far...")
                
                next_token = response.get('nextToken')
                if not next_token:
                    break

            if not all_events:
                print(f"No logs found in '{log_group_name}' for the specified time range.")
                return False

            # Sort events by timestamp
            all_events.sort(key=lambda x: x['timestamp'])

            # Create a file name with timestamp
            file_name = f"{log_group_name.replace('/', '_')}_{int(time.time())}.txt"
            
            # Write logs to a local file
            with open(file_name, 'w') as f:
                f.write(f"Log Group: {log_group_name}\n")
                f.write(f"Time Range: {start_time_str} UTC to {end_time_str} UTC\n")
                f.write("=" * 80 + "\n\n")
                
                for event in all_events:
                    # Convert timestamp to UTC datetime for display
                    timestamp = datetime.fromtimestamp(
                        event['timestamp']/1000, tz=timezone.utc
                    ).strftime('%Y-%m-%d %H:%M:%S.%f UTC')
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Stream: {event['logStreamName']}\n")
                    f.write("Message:\n{}\n".format(event['message']))
                    f.write("-" * 80 + "\n\n")
            
            print(f"Logs have been written to local file: {file_name}")
            
            # Upload file to S3
            s3_key = f"{s3_prefix}/{file_name}" if s3_prefix else file_name
            print(f"Uploading logs to S3...")
            s3_client.upload_file(file_name, bucket_name, s3_key)
            print(f"✓ Logs successfully uploaded to: s3://{bucket_name}/{s3_key}")
            print(f"✓ Total log events retrieved: {len(all_events)}")
            return True

        except cloudwatch_logs.exceptions.ResourceNotFoundException:
            print(f"Error: Log group '{log_group_name}' not found.")
            print("Hint: Verify the environment name and ensure logging is enabled in the MWAA console.")
            return False
        except Exception as e:
            print(f"Error during log retrieval and upload: {str(e)}")
            return False
        
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        args = parse_arguments()
        
        # Determine log groups to process
        if args.env_name:
            # Auto-construct log group names from environment name
            if args.log_types:
                log_groups = [f"airflow-{args.env_name}-{lt}" for lt in args.log_types]
            else:
                log_groups = construct_log_group_names(args.env_name)
            
            print(f"\n{'='*60}")
            print(f"MWAA Environment: {args.env_name}")
            print(f"Log groups to fetch ({len(log_groups)}):")
            for lg in log_groups:
                print(f"  - {lg}")
            print(f"{'='*60}")
        else:
            # Legacy mode: direct log group specification
            log_groups = [args.log_group]
        
        # Process each log group
        results = {}
        for log_group in log_groups:
            print(f"\n{'*'*60}")
            print(f"Processing: {log_group}")
            print(f"{'*'*60}")
            success = get_logs_and_upload_to_s3(
                log_group_name=log_group,
                start_time_str=args.start,
                end_time_str=args.end,
                bucket_name=args.bucket,
                s3_prefix=args.prefix,
                region=args.region
            )
            results[log_group] = success
        
        # Print summary
        print(f"\n\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        for lg, status in results.items():
            status_icon = "✓" if status else "✗"
            print(f"  {status_icon} {lg}")
        
        successful = sum(1 for s in results.values() if s)
        total = len(results)
        print(f"\nCompleted: {successful}/{total} log groups processed successfully.")
        print(f"{'='*60}")
        
        exit(0 if any(results.values()) else 1)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        exit(1)

