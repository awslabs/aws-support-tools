These Scripts are used to copy a Postgresql RDS Table to a Redshift Table using Data Pipeline. 


dbconv_psqlRDStoRedshift.sh is run by a ShellcommandActivity in the pipeline. It dumps the schema of your Postgresql RDS table and creates the corresponding Redshift Table. Please host  dbconv_psqlRDStoRedshift.sh in your S3 bucket and give it access to Data Pipeline Resource role that you use for your pipeline jobs. Default Data Pipeline Resource IAM role is DataPipelineDefaultResourceRole. 


Since Redshift is already Postgresql based, we do not need a schema translation script for Redshift Table creation.


postgresqlRDS-to-Redshift-definition.json is a sample pipeline definition file that illustrates usage of the above script. The target Redshift Table's Primary Keys should be provided in the definition of RedshiftDataNode.


Warning: The scripts are not exhaustively tested for all data types. Please test the scripts on a subset of your original data before using for Production. 

