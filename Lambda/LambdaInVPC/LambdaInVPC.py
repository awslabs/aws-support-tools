import sys
import datetime
import os
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

variables = os.environ

#memcached
def connect_to_memcached():
    logger.info("=========================================")
    logger.info("Info: now testing memcached")
    if "memcached" in variables:
        memcached_host = variables['memcached']
    else:
        logger.error("ERROR: no memcached environment variable set. You must set the variable for testing")
        return

    import elasticache_auto_discovery
    from pymemcache.client.hash import HashClient
    try:
        elasticache_config_endpoint = memcached_host + ":11211" 
        logger.info("Info: Conncting to memcached %s" %(elasticache_config_endpoint))
        nodes = elasticache_auto_discovery.discover(elasticache_config_endpoint)
        nodes = map(lambda x: (x[1], int(x[2])), nodes)
        memcache_client = HashClient(nodes)
        memcached_value = "memcached-" + str(datetime.datetime.now())
        memcache_client.set('memcached_key', memcached_value)
        memcached_value_obtained = memcache_client.get('memcached_key')
        logger.info("Info: set value %s for key memcached_key successfully" %(memcached_value_obtained))
    except:
        logger.error("ERROR: Unexpected error: Could not connect to redis." + elasticache_config_endpoint)


#redis
def connect_to_redis():
    logger.info("=========================================")
    logger.info("Info: now testing redis")
    if "redishost" in variables:
        redis_host = variables['redishost']
    else:
        logger.error("ERROR: no redishost environment variable set. You must set the variable for testing")
        return
    redis_port = variables.get("redisport", 6379)
    import redis
    try:
        logger.info("Info: Conncting to redis %s over port %s" %(redis_host, redis_port))
        redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
        redis_value= "redis-" + str(datetime.datetime.now())
        redis_client.set('redis_key', redis_value)
        redis_value_obtained = redis_client.get("redis_key")
        logger.info("Info: Setting Redis value %s with key redis_key successfully" %(redis_value_obtained))
    except:
        logger.error("ERROR: Unexpected error: Could not connect to redis.")

#RDS
def connect_to_rdsmysql():
    logger.info("=========================================")
    logger.info("Info: now testing RDS MySQL")
    if "rdshost" in variables:
        rds_host = variables['rdshost']
    else:
        logger.error("ERROR: no rdshost environment variable set. You must set the variable for testing")
        return
    dbusername = variables.get("rdsusername", "root")
    dbpassword = variables.get("rdspassword", "password")
    db_name = variables.get("rdsdbname", "testdb")
    db_port = variables.get("rdsport", 3306)
    import pymysql
    item_count = 0
    try:
        conn = pymysql.connect(rds_host, user=dbusername, passwd=dbpassword, db=db_name, port=db_port, connect_timeout=5)
        logger.info("Info: Connection to RDS mysql instance succeeded")
        item_count = 0
        with conn.cursor() as cur:
            cur.execute("drop table if exists sample")
            cur.execute("create table sample (ID  int NOT NULL, Name varchar(255) NOT NULL, PRIMARY KEY (ID))")
            cur.execute('insert into sample (ID, Name) values(1, "Joe")')
            cur.execute('insert into sample (ID, Name) values(2, "Bob")')
            cur.execute('insert into sample (ID, Name) values(3, "Mary")')
            conn.commit()
            cur.execute("select * from sample")
            for row in cur:
                item_count += 1
            logger.info("Info: successfully insert %d rows into table sample into RDS" %item_count)
            conn.close()
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

# DNS query
def dns_query():
    logger.info("=========================================")
    logger.info("Info: now DNS query")
    import socket
    dns_host = variables.get("dnshost", "www.amazon.com")
    try:
        ip = socket.gethostbyname(dns_host)
        logger.info("Info: successfully get the DNS resolution of %s - IP: %s " %(dns_host, ip))
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")


# Internet access
def Internet_http_get():
    logger.info("=========================================")
    logger.info("Info: now testing GET HTTP request to external website")
    import requests
    url = variables.get("url", "https://www.amazon.com")
    try:
        requests.get(url)
        logger.info("Info: successfully did a GET HTTP request to %s" %(url))  
    except:
        logger.error("ERROR: Unexpected error: Could not do a GET HTTP request to %s" %(url))  


def handler(event, context):
    """
    This function puts into data into redis/mencached/rds/DynamoDB
    """
    connect_to_memcached()
    connect_to_redis()
    connect_to_rdsmysql()
    dns_query()
    Internet_http_get()
    return "Lambda Testing finished. Please check the execution logs output for result"


