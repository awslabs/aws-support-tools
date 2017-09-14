These Scripts are used to copy a Mysql RDS Table to a Postgresql RDS Table using Data Pipeline.


mysqlRDS-psqlRDS-copy-using-shell-definition.json is a sample pipeline definition file that shows all activities and pipeline objects for copying a Mysql RDS table to a Postgresql RDS Table. It is based on the default Data Pipeline Template used to copy a Mysql Table to Redshift Table, with changes to the Shell Script used in the ShellCommandActivity. 

-- The default template uses s3://datapipeline-us-east-1/sample-scripts/dbconv.sh. 
dbconv.sh is modified and provided here as dbconv_mysqlRDs_to_postgresqlRDS.sh. 
Please host this shell script in your S3 bucket and make it Publicly accessible.

-- RedshiftCopyActivity in the default template is replaced with two ShellCommandActivities. These ShellcommandActivities perform the psql copy of the staged S3 csv file into the target table. 


mysqlRDS-psqlRDS-copy-using-shell-definition.json calls dbconv_mysqlRDS-to-postgresqlRDS.sh in a ShellcommandActivity. This shell script in-turn downloads s3://datapipeline-us-east-1/sample-scripts/mysql_to_redshift.py. The python script translates the MySql schema to Postgresql.


Please modify the sample definition file with your Database, Ec2 details and the path of your hosted shell script in S3. 


Warning: The scripts are not exhaustively tested for all data types. Please test the scripts on a subset of your original data before using for Production. timestamp column types may require more customization.

