
# MWAA Log Retrieval Script

## Overview

This Python script automates MWAA's log retrieval process from CloudWatch. It extracts logs within a specified time range and uploads consolidated results to S3. This eliminates manual collection efforts and reduces the need for repeated intervention to fetch logs, enabling quick gathering of diagnostic information in a standardized, shareable format for faster resolution.

## Prerequisites

- Python 3.6 or higher installed on your system
- AWS CLI configured with valid credentials, or AWS credentials available via environment variables or IAM role
- Boto3 library (AWS SDK for Python)
- Appropriate IAM permissions (see IAM Permissions section below)
- Network access to AWS CloudWatch Logs and S3 services

## Running the Script

Download the script to your local machine.

**Basic Syntax:**

```bash
python mwaa_log_retrieval.py -n <ENVIRONMENT_NAME> -s <START_TIME> -e <END_TIME> -b <BUCKET_NAME>
```

**Example:**

```bash
python mwaa_log_retrieval.py -n "MyAirflowEnvironment" \
    -s "2024-07-08 13:00:00" \
    -e "2024-07-08 14:00:00" \
    -b "amzn-s3-demo-mwaa-logs"
```

## Parameters

| Parameter | Flag | Description | Optional? |
|-----------|------|-------------|-----------|
| MWAA Environment Name | `-n` / `--env-name` | MWAA environment name (auto-constructs log group names) | No (or use `-l`) |
| Start Time | `-s` / `--start` | Start time in UTC (format: YYYY-MM-DD HH:MM:SS) | No |
| End Time | `-e` / `--end` | End time in UTC (format: YYYY-MM-DD HH:MM:SS) | No |
| S3 Bucket | `-b` / `--bucket` | S3 bucket name (just the name, not the full URI) | No |
| Log Types | `-t` / `--log-types` | Specific log types to fetch (default: all 5). Choices: DAGProcessing, Scheduler, Task, WebServer, Worker | Yes |
| S3 Prefix | `-p` / `--prefix` | S3 prefix/folder path | Yes |
| AWS Region | `-r` / `--region` | AWS region (uses default if not specified) | Yes |
| Keep Local | `--keep-local` | Keep local log files after S3 upload (default: files are deleted after upload) | Yes |
| Log Group (legacy) | `-l` / `--log-group` | Direct log group name (legacy mode, use instead of `-n`) | Yes |

**Note:** `-n` and `-l` are mutually exclusive. Use `-n` for auto log-group naming (recommended) or `-l` for direct log group specification (legacy).

## Examples

**Fetch all log types for an environment (recommended):**

```bash
python mwaa_log_retrieval.py -n "MyAirflowEnvironment" \
    -s "2024-07-08 13:00:00" -e "2024-07-08 14:00:00" \
    -b "amzn-s3-demo-mwaa-logs" -p "output_logs"
```

This auto-constructs and fetches logs from:
- `airflow-MyAirflowEnvironment-DAGProcessing`
- `airflow-MyAirflowEnvironment-Scheduler`
- `airflow-MyAirflowEnvironment-Task`
- `airflow-MyAirflowEnvironment-WebServer`
- `airflow-MyAirflowEnvironment-Worker`

**Fetch only specific log types:**

```bash
python mwaa_log_retrieval.py -n "MyAirflowEnvironment" -t Task Scheduler \
    -s "2024-07-08 13:00:00" -e "2024-07-08 14:00:00" \
    -b "amzn-s3-demo-mwaa-logs" -p "output_logs"
```

**Keep local files after upload:**

```bash
python mwaa_log_retrieval.py -n "MyAirflowEnvironment" \
    -s "2024-07-08 13:00:00" -e "2024-07-08 14:00:00" \
    -b "amzn-s3-demo-mwaa-logs" --keep-local
```

**Legacy mode (direct log group specification):**

```bash
python mwaa_log_retrieval.py -l "airflow-MyAirflowEnvironment-Task" \
    -s "2024-07-08 13:00:00" -e "2024-07-08 14:00:00" \
    -b "amzn-s3-demo-mwaa-logs"
```

## Output

The script generates two outputs per log group:

1. **S3 upload:** Log file is uploaded to `s3://<bucket_name>/<prefix>/<filename>`
2. **Local text file (optional):** `<log_group_name>_<timestamp>.txt` (retained only if `--keep-local` is used)

**Sample output logs:**

```
Log Group: airflow-MyAirflowEnvironment-Task
Time Range: 2024-07-08 13:00:00 UTC to 2024-07-08 14:00:00 UTC
================================================================================
Timestamp: 2024-07-08 13:00:04.511000 UTC
Stream: dag_id=cds_decimal/run_id=scheduled__2024-07-08T07_20_00+00_00/task_id=task_cds_decimal/attempt=1.log
Message:
[2024-07-08T07:30:04.511+0000] {{taskinstance.py:1956}} INFO - Dependencies all met for dep_context=non-requeueable deps ti=<TaskInstance: cds_decimal.task_cds_decimal scheduled__2024-07-08T07:20:00+00:00 [queued]>
--------------------------------------------------------------------------------
Timestamp: 2024-07-08 13:00:04.529000 UTC
Stream: dag_id=cds_decimal/run_id=scheduled__2024-07-08T07_20_00+00_00/task_id=task_cds_decimal/attempt=1.log
Message:
[2024-07-08T07:30:04.529+0000] {{taskinstance.py:1956}} INFO - Dependencies all met for dep_context=requeueable deps ti=<TaskInstance: cds_decimal.task_cds_decimal scheduled__2024-07-08T07:20:00+00:00 [queued]>
--------------------------------------------------------------------------------
```

**Sample summary (when fetching all log types):**

```
============================================================
SUMMARY
============================================================
  ✓ airflow-MyAirflowEnvironment-DAGProcessing
  ✓ airflow-MyAirflowEnvironment-Scheduler
  ✓ airflow-MyAirflowEnvironment-Task
  ✓ airflow-MyAirflowEnvironment-WebServer
  ✓ airflow-MyAirflowEnvironment-Worker

Completed: 5/5 log groups processed successfully.
============================================================
```

## IAM Permissions Required

The AWS credentials used must have the following permissions:

**CloudWatch Logs Permissions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:FilterLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:airflow-*",
        "arn:aws:logs:*:*:log-group:airflow-*:log-stream:*"
      ]
    }
  ]
}
```

**S3 Permissions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::<your-bucket-name>/*"
    }
  ]
}
```

## Important Notes

- **All times are in UTC.** CloudWatch stores logs in UTC, so provide your start and end times in UTC.
- **Log type names are case-sensitive.** Use exactly: DAGProcessing, Scheduler, Task, WebServer, Worker.
- **Bucket name only.** For the `-b` flag, provide just the bucket name (e.g., `amzn-s3-demo-mwaa-logs`), not the full S3 URI. Use `-p` for the prefix/folder path.
- **Large time ranges** will result in more events and longer execution times. For troubleshooting, start with a 1-2 hour window.
- **MWAA logging must be enabled** in the MWAA console for the log groups to exist. If you get a "log group not found" error, verify logging is enabled for that log type.
- **Local file cleanup:** By default, local log files are deleted after successful S3 upload. Use `--keep-local` to retain them.
- **Health-check filtering:** The script applies a server-side filter to exclude ELB health-check entries (`GET /health` and `ELB-HealthChecker`). These entries only appear in WebServer logs, the filter is harmless for other log types but reduces noise when fetching WebServer logs.
