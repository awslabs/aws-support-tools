# Export DynamoDB data as CSV to S3 using Data Pipeline
## Data Pipeline templates for ETL jobs

When you use AWS Data Pipeline to export data from DynamoDB to S3, Data Pipeline will launch a back up job on EMR cluster. But, the format that it is exported in a specific type that looks like JSON format but it cannot be parsed as a generic JSON file using available libraries. You can implement custom solutions by writing your own parser. There are few attempts of this as well which are available on GitHub. But the current solutions don’t offer scalability nor the automation.

Hence we need a different solution to export data from DynamoDB to CSV (or any other format) which can be readily consumed by other applications using native libraries without much hassle.

A better way to handle this is by using Apache Hive. The idea is very simple. You can create Hive external table on DynamoDB using EMR. Then you can create another Hive external table on S3. Then move data from on table to another table. The advantage of doing with Hive is the external table format. Hive offer to save the external table in various format such as TXT, CSV, AVRO, Parquet etc. So the external table created on S3 can be stored as CSV. Hive will take care of reading the writing part. We just have to make sure that the table columns have been properly mapped.

Hive on EMR can handle the scalability. Now for automation we can use Data Pipeline. We can create a Data Pipeline that will launch EMR cluster and implement the above mentioned steps. The DDBtoCSV Data Pipeline template, can be used to do the exact same thing. In the template DynamoDB table is called as 'Features'. You can also create the same DynamoDB table using the data located here.


The data pipeline template is made with following Assumptions/Prerequisites:
1. Default VPC exists.
2. EMR cluster is able to launch properly in a subnet.
3. Subnet has route to the reach internet. Mainly EC2 instances launched in the subnet  must be able to reach S3 endpoint and Data pipeline endpoint.

The following steps to use the pipeline definition:
1. Go to the Data pipeline page and click on create new pipeline.
2. Provide a name for the pipeline. For ‘Source’ select Load from local file and select the pipeline definition.
3. Under schedule, for ‘Run’ select on pipeline activation
4. Then select enable logging and provide a s3 bucket path to store logs.
5. You can leave default for IAM roles.
6. Then click ‘Edit in Architect’.
7. Once you click ‘Edit in Architect’, you’ll see the following page as shown in the screenshot img1.
8. On the right hand side click on the activities to expand it.
9. For the activity ‘DDB_Hive_external_table’ the create table script is:

```
CREATE EXTERNAL TABLE ddb_features
 (Id BIGINT, Class String, Latitude DOUBLE, Longitude DOUBLE, Name String, State String, Elevation DOUBLE)
STORED BY 'org.apache.hadoop.hive.dynamodb.DynamoDBStorageHandler' 
TBLPROPERTIES (
 "dynamodb.table.name" = "Features", 
 "dynamodb.column.mapping" = "Id:Id,Class:Class,Latitude:Latitude,Longitude:Longitude,Name:Name,State:State,Elevation:Elevation"
);
```

Change the row column names and datatypes to match the column names of you DynamoDB table. Also change the table name.
— dynamodb.table.name: the name of the DynamoDB table.
— dynamodb.column.mapping: pairs of column names in the Hive table and their corresponding attributes in the DynamoDB table. Each pair is of the form hive_column_name:dynamodb_attribute_name, and the pairs are separated by commas. Please make sure to change it too. In the example I provided:

```
"dynamodb.column.mapping" = "Id:Id,Class:Class,Latitude:Latitude,Longitude:Longitude,Name:Name,State:State,Elevation:Elevation"
```
10. And For the activity ‘CSV_Hive_external_table’ the script is:

```
CREATE EXTERNAL TABLE csv_features 
 (Id BIGINT, Class String, Latitude DOUBLE, Longitude DOUBLE, Name String, State String, Elevation DOUBLE)
ROW FORMAT DELIMITED FIELDS terminated by ','
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3n://bhargav-ddbexport/csv-features/';
```
Change the row columns names to the columns that you provided in Step 9. In location provide s3 bucket path where you want the csv file to be created. In the example csv file will be create in s3://bhargav-ddbexport/csv-features/ location.

11. Once you do the above click on the ‘Resources’ to expand it. Make sure the region value is the same region as your DynamoDB table exists.
12. Now Click ‘Save’ on the top of the page. After the pipeline is saved a pop-up will appear. Click on activate. Now the pipeline will be activated and will start executing.

After the execution finished the CSV file is located on S3 path and the default file name will be 000000_0. When ever you want to extract the data from DynamoDB in CSV format you can Activate this pipeline and the data will be written in CSV format.
