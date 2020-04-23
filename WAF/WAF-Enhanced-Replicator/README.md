# WAFER - AWS WAF Enhanced Replicator

WAFER, a tool to facilitate the replication of AWS WAF global or regional configurations.

## Pre-requisites

To use WAFER, you must have:
- A valid AWS CLI configuration (at least the _credentials_ file);
- Python 3.6 or later;
- The Boto3 SDK;
- PIP (to install Boto3);
- IAM permissions to access AWS WAF resources in read-only mode.

## Installation

1. Clone the AWS Support GitHub repository and navigate to the WAF/WAFER directory;
2. Run "pip install -r requirements.txt" to install the Boto 3 SDK;
3. Optionally, give execution permission to the _wafer_ file.


## Directory Structure

One of the first steps that the tool does is creating a reference directory to hold the files. This directory name is **.wafer**. WAFER will create this directory inside the user's home directory. 

Inside the **.wafer** directory, two other directories are created:

- "logs" - stores the log files;
- "templates" - stores the Terraform template files.

## Usage

The tool runs around a Web ACL. So, you have to either choose one from the list that you be presented to you, or provide a Web ACL ID on the command line itself.

If you run WAFER with no arguments, the usage screen will show up. The same screen will be displayed in case you type a wrong command line.

```
$ wafer
WAFER - AWS WAF Enhanced Replicator - Version 1.0 | Build Date 2019-05-27

Usage:
    wafer {global | regional --region <AWS region>} [--web-acl <Web ACL ID>]

    Notes:
    1. You must choose the scope to be either global OR regional.
    2. If you choose regional, you must provide one valid AWS region.
    3. Optionally, regardless of the scope, you can directly provide the desired Web ACL ID.
```

As pointed out above, you must choose the **scope**: if you want to replicate a global or a regional Web ACL. In case you choose the regional way, you must provide the AWS region where the Web ACL is located. 

## What does the tool get?

WAFER will grab (get) the following resources, according to the provided scope (global or regional):

1. All WAF scope conditions regardless of the type (string match, regex, geolocation, ...);
2. All WAF scope rules and rule groups related to the chosen Web ACL;
3. If there is any resource associated with the chosen Web ACL;
4. The Web ACL's rules priorities and default action.

**WAFER does not get an associated resource's specific data or properties. If, for example, your regional Web ACL is associated to an Application Load Balancer (ALB), WAFER will only detect that and write the relevant blocks in the Terraform template file.**

## What does the tool not get?

WAFER does not get rules unrelated to the Web ACL you chose or provided through a CLI argument.

## What happens afterwards?

Just before end, WAFER will compress both the template and the log files inside a zip file and show you its location.
