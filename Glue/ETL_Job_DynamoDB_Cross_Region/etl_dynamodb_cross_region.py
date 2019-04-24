#Copyright 2017-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file 
#except in compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/apache2.0/
#
#or in the "license" file accompanying this file. This file is distributed on an "AS IS" 
#BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the 
#License for the specific language governing permissions and limitations under the License.

import sys
import boto3
from awsglue.transforms import *
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job

sc = SparkContext.getOrCreate()
gc = GlueContext(sc)
job = Job(gc)

#create dynamodb resource client to omit data type descriptors from returned collections when using low-level client
ddb = boto3.resource('dynamodb', region_name='eu-west-1')

#get table resource in another AWS region
test_table = ddb.Table('test-table')

# get table items from scan, pull items list from dictionary
table_items = test_table.scan()['Items']

# convert to RDD so we can use it in spark
ddbRDD =  sc.parallelize(table_items)

# if you only want a DataFrame, create DataFrame from RDD using SQLContext (GlueContext can only create DynamicFrames from RDDs, not DataFrames)
#ddbDataFrame = gc.createDataFrame(ddbRDD)

#create DynamicFrame from RDD using GlueContext
ddbDynamicFrame = gc.create_dynamic_frame_from_rdd(ddbRDD, "ddbDFrame")

#write to S3
datasink = gc.write_dynamic_frame.from_options(frame = ddbDynamicFrame, connection_type = "s3",connection_options = { "path":  "s3://your-glue-target-bucket"}, format="json")

job.commit()  
