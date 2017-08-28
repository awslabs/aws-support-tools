These Scripts are used to copy a Mysql RDS Table to a Postgresql RDS Table using Data Pipeline. 


dbconv_mysqlRDS-to-postgresqlRDS.sh is run by a ShellcommandActivity in the pipeline. 
mysql_to_redshift.py script translates schema from Mysql to Postgresql. 


Please host  dbconv_mysqlRDS-to-postgresqlRDS.sh and mysql_to_redshift.py in your S3 bucket and make them Public. 


mysqlRDS-psqlRDS-copy-using-shell-definition.json is a sample pipeline definition file that illustrates usage of the above two scripts. 


Warning: The scripts are not exhaustively tested for all data types. Pleasse test the scripts on a subset of your original data before using for Production. timestamp column types may require more customization.