These scripts are used to copy a Postgresql RDS Table to a Redshift Table using Data Pipeline. 


postgresqlRDS-to-Redshift-definition.json is a sample pipeline definition file that shows all activities and pipeline objects for copying a Postgresql RDS table to a Redshift Table. It is based on the default Data Pipeline Template used to copy a Mysql Table to Redshift Table, with changes to the Shell Script used in the ShellCommandActivity. 


The default template uses s3://datapipeline-us-east-1/sample-scripts/dbconv.sh. 
dbconv.sh is modified and provided here as dbconv_psqlRDStoRedshift.sh. 
Please host this shell script in your S3 bucket and make it Publicly accessible.


An overview of the sequence of activities in the pipeline:

[1] RDSToS3CopyActivity - CopyActivity to copy from RDS table to staging S3 path. CopyActivity stages the entire RDS table to the EC2 resource running the activity. Hence, please choose a bigger instance type to fit your entire RDS table.

[2] RedshiftTableCreateActivity - ShellCommandActivity that creates the target Redshift Table. This activity runs the dbconv_psqlRDStoRedshift.sh that you need to host in your S3.

[3] S3ToRedshiftCopyActivity - RedshiftCopyActivity that uses Redhsift's COPY command to copy the S3 CSV file to target Redshift table.

[4] S3StagingCleanupActivity - ShellCommandActivity to clean up the intermediate S3 CSV file


Note: The target Redshift Table's Primary Keys should be provided in the definition of RedshiftDataNode.


Warning: The scripts are not exhaustively tested for all data types. Please test the scripts on a subset of your original data before using for Production. 

