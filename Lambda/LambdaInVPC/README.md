# Lambda In VPC testing: 
** Important notice: We suggest you testing against non-production caching/db resources. ** 

When Lambda is put into VPC, there are some major differences we need to consider: 

 - VPC subnet, 
 - security group, 
 - Internet Accessing, 
 - DNS resolution ablitiy. 
 
This sample program is to test against the below activiest: 

 1. accessing an internal ElasticCache memcached
 2. accessing an intenral ElasticCache Redis
 3. accessing an intenral RDS MySQL
 4. accessing an internal ELB resource
 5. accessing an external DNS for name resoluation
 6. accessing an external HTTP endpoint

## How to use it.
 
  - Set up your testing aim
  - Set up the test resource
  You need to setup your test resources eg - memcached or DynamoDB in your VPC environment. As this is not the aim of this tutorial, Please refer to "Setup Test Resources.md" in the repo. For testing aim: 6/7, you don't need to do any extra steps.
  - Package the test deployment.
  	In this tutorial, we will use Python/virtualenv as our test step. 
  	- create the testing virtual env 
  	
  	~~~
  	virtualenv LambdaVPCTesting
  	source source LambdaVPCTesting/bin/activate
  	cd LambdaVPCTesting
  	~~~
  	
  	- install packages according to your testing purpose:
  	** choose the your testing related packages**
  	
  	~~~
  	pip install elasticache_auto_discovery
  	pip install redis
  	pip install pymemcache
  	pip install pymysql
  	pip install requests
  	~~~
  	
  - Create test Lambda function
  - Setup your Lambda VPC setting (VPC, Subnet, security group)
  - Run the testing and check the logs in Lambda console

## Testing case:
  
  You can choose to comment out the unneeded functions in the main function.
  
  - test accessing to internal ElasticCache memcached 
   *possible fail reason:*
  	1. You Lambda doesn't have correct routing to memcached instance(eg. totally lambda in an isolated VPC, subnet)
  	2. You memcached security group blocks the accessing from Lambda

  - test accessing to internal ElasticCache redis
   *possible fail reason:* 
  	1. You Lambda doesn't have correct routing to redis instance(eg. totally lambda in an isolated VPC, in correct subnet routing table)
  	2. You redis security group blocks the accessing from Lambda
  	  	
  - test accessing to internal RDS MySQL
   *possible fail reason:*
   	1. You Lambda doesn't have correct routing to RDS/MySQL instance(eg. totally lambda in an isolated VPC, in correct subnet routing table)
  	2. You RDS/MySQL security group blocks the accessing from Lambda
  	3. You testing MySQL instances' credential are not correct

  - test external DNS query:
   *possible fail reason:*
  	1. You Lambda doesn't have correct routing to redis instance(eg. totally lambda in an isolated VPC, subnet)
  	2. You redis security group blocks the accessing from Lambda

  - test external HTTP Requests:
   *possible fail reason:*
  	1. DNS failure
  	2. HTTP/HTTPS outbound not required   

 *Note this tutorial has been tested on Lambda 2.7*
 
 *If you just want to test the Lambda TCP connection, you can use the simpleTCPTesting.py within inline editor*
 
 *for Non-Python 2.7 environment, you can use the code and runtime to verify your Lambda network configuration and switch to your runtime after testing* 


