These scripts are used to copy a Postgresql RDS Table to a Redshift Table using Data Pipeline. 


postgresqlRDS-to-Redshift-definition.json is a sample pipeline definition file that shows all activities and pipeline objects for copying a Postgresql RDS table to a Redshift Table. It is based on the default Data Pipeline Template used to copy a Mysql Table to Redshift Table, with changes to the Shell Script used in the ShellCommandActivity. 

-- The default template uses s3://datapipeline-us-east-1/sample-scripts/dbconv.sh. 
dbconv.sh is modified and provided here as dbconv_psqlRDStoRedshift.sh. 
Please host this shell script in your S3 bucket and make it Publicly accessible.


-- dbconv_psqlRDStoRedshift.sh is run by a ShellcommandActivity in the pipeline. It dumps the schema of your Postgresql RDS table and creates the corresponding Redshift Table. 

-- Since Redshift is already Postgresql based, we do not need the schema translation script s3://datapipeline-us-east-1/sample-scripts/mysql_to_redshift.py for Redshift Table creation.

-- The target Redshift Table's Primary Keys should be provided in the definition of RedshiftDataNode.


Warning: The scripts are not exhaustively tested for all data types. Please test the scripts on a subset of your original data before using for Production. 

