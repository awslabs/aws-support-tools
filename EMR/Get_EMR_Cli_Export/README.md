# Get EMR Cli Export #

EMR provides AWS CLI export using the console.

You will then get a single line of AWS CLI to create a cluster with the same settings.

However, there is no API for command line tool.

This source code works parsing the parameters from “describe-cluster” at first, and make strings to fit “create-cluster” of aws-cli.

## How to run

`python get_emr_cli_export.py j-2ABCABCABC`
