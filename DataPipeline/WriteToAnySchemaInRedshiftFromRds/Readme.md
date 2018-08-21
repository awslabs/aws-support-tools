Data Pipeline has RedshiftCopyActivity which is used by many of its default templates to write from S3 into a target Redshift Table. The default RDS to Redshift Copy template has a chain of activities that also uses a schema translation script to convert the Mysql RDS schema into a Redshift compatible schema.


The default templates and the associated scripts for 'RDS to Redshift Copy' will allow writing ONLY to the Public schema in Redshift. The default scripts and templates are modified and shared here  to copy an RDS table into a Redshift table in a schema other than Public. 


-- 
[1] mysql_to_redshift_tablename_noquotes.py --  Code changes done to Ignore COMMENT portion from Column definition of RDS since Redshift does not support COMMENT in create table statement. Host this file in your S3 bucket and give it Public Access.


[2] dbconv_tablename_noquotes.sh -- Edit line 125 to point to your S3 location of [1].  Host this file also in your S3 bucket and give it Public Access. 


[3] RDStoRedshift-AnySchema.json is a data pipeline definition file example. It illustrates the usage of the scripts in [1] and [2] for copying a table in RDS to a table in any schema of Redshift. Update this json to refer your RDS table, Redshift table, S3 and Ec2Resource details, as well as make the RedshiftTableCreateActivity point to your S3 path where you had hosted [2].  

