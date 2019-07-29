# Get EMR CLI Export #

EMR provides AWS CLI export using the console. You will then get a single line of AWS CLI to create a cluster with the same settings. However, there is no API for command line tool. I implemented a sample code making AWS CLI for create-cluster.

What does this script do:

- It works parsing the parameters from “describe-cluster” at first.
- And make strings to fit “create-cluster” of aws-cli.
