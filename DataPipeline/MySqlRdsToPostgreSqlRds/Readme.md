These Scripts are used to copy a Mysql RDS Table to a Postgresql RDS Table using Data Pipeline.


mysqlRDS-psqlRDS-copy-using-shell-definition.json is a sample pipeline definition file that shows all activities and pipeline objects for copying a Mysql RDS table to a Postgresql RDS Table. It is based on the default Data Pipeline Template used to copy a Mysql Table to Redshift Table, with changes to the Shell Script used in the ShellCommandActivity. 


The default template uses s3://datapipeline-us-east-1/sample-scripts/dbconv.sh. 
dbconv.sh is modified and provided here as dbconv_mysqlRDs_to_postgresqlRDS.sh. 
Please host this shell script in your S3 bucket and make it Publicly accessible.


An overview of the sequence of activities in the pipeline:

[1] RDSToS3CopyActivity - CopyActivity to copy from RDS table to staging S3 path. CopyActivity stages the entire RDS table to the EC2 resource running the activity. Hence, please choose a bigger instance type to fit your entire RDS table.

[2] SyncS3CsvToEc2 - ShellCommandActivity that syncs the S3 CSV file to the local directory of EC2 resource. This is because, Postgresql RDs does not support copying from S3 yet.

[3] JdbcTableCreateActivity - ShellCommandActivity that creates the target Table in Posgresql RDS and also writes the table data synced on the local EC2 to target Postgresql Table. This activity runs the dbconv_mysqlRDS-to-postgresqlRDS.sh that you need to host in your S3. This shell script in-turn downloads s3://datapipeline-us-east-1/sample-scripts/mysql_to_redshift.py. The python script translates the MySql schema to Postgresql.

[4] S3StagingCleanupActivity - ShellCommandActivity to clean up the intermediate S3 CSV file



Please modify the sample definition file with your Database, Ec2 details and the path of your hosted shell script in S3. 


Warning: The scripts are not exhaustively tested for all data types. Please test the scripts on a subset of your original data before using for Production. timestamp column types may require more customization.

