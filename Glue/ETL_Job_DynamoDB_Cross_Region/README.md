# Access a cross-region DynamoDB table in a Glue Job? #

Problem
When using the Glue ETL API, we cannot currently (2019.Q2) create DynamicFrames from DynamoDB tables in a different region using Glue Connections or Glue Data Catalog. The Glue Data Catalog can only add metadata tables for DynamoDB tables using a crawler (manual tables can only be added for S3 data stores), and these Crawlers can only crawl DynamoDB tables in the same region as the Glue job. Creating DynamicFrames from Glue connections can also only be done from DynamoDB tables in the same region.



Solution
Since the environment in which our driver program is running has the AWS SDK installed, we can import it into our program and use it to pull data from the DynamoDB table in another region.  Once we have this data in a collection, we can create an RDD from it.

Spark's RDDs are the core data structures used to store data so that we can operate on them in parallel. Spark DataFrames and Glue DynamicFrames can be created from RDDs. So if we can get the DynamoDB table data from another region into an RDD, we can create a DataFrame or DynamicFrame from it and and transform the data using these familiar structured APIs.

There are two ways to create RDDs:

Parallelizing existing collections
Referencing a dataset in an external storage system.
Since DynamoDB is not a Hadoop supported storage system, we will have to use the parallelizing approach.

If we have a collection in our driver program, we can parallelize it into an RDD by using SparkContext's parallelize method. 

Once we have the RDD, we can use the GlueContext's create_dynamic_frame_from_rdd method to create a DynamicFrame from an RDD.

(Internally, GlueContext first calls it's parent class' (SQLContext) createDataFrame method to convert the RDD to a DataFrame, then creates a DynamicFrame from the DataFrame using DynamicFrame's fromDF method. See related items)

We now have a DynamicFrame that we can transform and write out using the familiar Glue ETL API.

What does this script do:

- Uses boto3 to scan a DynamoDB table and puts the items returned into a list
- Creates an RDD by parallelizing the list of items
- Creates a DynamicFrame from the RDD
- Writes the DynamicFrame to S3
