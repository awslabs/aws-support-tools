# Build and Deploy

Source code layout:
```
src
└── com
    └── henoc
        └── presto
            ├── MyConcat.java
            └── MyConcatPlugin.java
```

For Presto 0.194 on EMR 5.13.0, I needed the following dependencies:
https://mvnrepository.com/artifact/com.facebook.presto/presto-spi/0.194
https://mvnrepository.com/artifact/io.airlift/slice/0.10
https://mvnrepository.com/artifact/com.google.guava/guava/21.0

## Building the jar:

```
[~]$ mkdir lib build
[~]$ cd lib 
[~]$ wget http://central.maven.org/maven2/com/facebook/presto/presto-spi/0.194/presto-spi-0.194.jar
[~]$ wget http://central.maven.org/maven2/io/airlift/slice/0.10/slice-0.10.jar
[~]$ wget http://central.maven.org/maven2/com/google/guava/guava/21.0/guava-21.0.jar

[~]$ cd ../
[~]$ javac -classpath .:lib/*  -sourcepath src/ -d build src/com/henoc/presto/*.java
[~]$ jar cf myconcat.jar -C build/ .
```
There is another requirement to have a resource file named com.facebook.presto.spi.Plugin in the META-INF/services directory. The content of this file is a single line listing the name of the plugin class (com.henoc.presto.MyConcatPlugin, in my case):
```
[~]$ mkdir META-INF/services -p
[~]$ echo com.henoc.presto.MyConcatPlugin > META-INF/services/com.facebook.presto.spi.Plugin
[~]$ jar uf myconcat.jar META-INF/services/com.facebook.presto.spi.Plugin
```
The content of the jar is:
```
[~]$ jar tf myconcat.jar 
META-INF/
META-INF/MANIFEST.MF
com/
com/henoc/
com/henoc/presto/
com/henoc/presto/MyConcat.class
com/henoc/presto/MyConcatPlugin.class
META-INF/services/com.facebook.presto.spi.Plugin
```
## Deploying the jar:

The plugin and all its necessary jars need to be deployed to a directory under plugin.config-dir (/usr/lib/presto/plugin/ on EMR) on all nodes of the cluster
```
[~]$ mkdir myconcat-plugin
[~]$ ln myconcat.jar  myconcat-plugin/
[~]$ ln lib/guava-21.0.jar myconcat-plugin/
```
The directory myconcat-plugin contains all the jars necessary for the newly created myconcat function.
We need to have it copied in /usr/lib/presto/plugin on all the nodes of the cluster. We can run the following script to copy it to all nodes of the cluster and set the right permissions:
```
#!/usr/bine/env bash

set -e -x

# copy files to plugin dir on master node and set required permissions
sudo cp myconcat-plugin -r /usr/lib/presto/plugin/
sudo chown presto:presto /usr/lib/presto/plugin/myconcat-plugin/ -R

# do the same on all other nodes
for anode in $(yarn node -list|sed -n "s/^\(ip[^:]*\):.*/\1/p");
do
	scp -o StrictHostKeyChecking=no -r myconcat-plugin hadoop@${anode}:/home/hadoop/
	ssh hadoop@${anode} -t sudo cp -r myconcat-plugin /usr/lib/presto/plugin/ 
	ssh hadoop@${anode} -t sudo chown presto:presto -R /usr/lib/presto/plugin/myconcat-plugin
done

# restart presto-server
sudo initctl stop presto-server && sleep 2 && sudo initctl start presto-server
```


We can check if the plugin and functions were successffully loaded:
```
[hadoop@ip-172-31-47-75 ~]$ grep  -i myconcat /var/log/presto/server.log 
2018-05-28T10:38:28.409Z	INFO	main	com.facebook.presto.server.PluginManager	-- Loading plugin /usr/lib/presto/plugin/myconcat-plugin --
2018-05-28T10:38:28.411Z	INFO	main	com.facebook.presto.server.PluginManager	Installing com.henoc.presto.MyConcatPlugin
2018-05-28T10:38:28.422Z	INFO	main	com.facebook.presto.server.PluginManager	Registering functions from com.henoc.presto.MyConcat
2018-05-28T10:38:28.425Z	INFO	main	com.facebook.presto.server.PluginManager	-- Finished loading plugin /usr/lib/presto/plugin/myconcat-plugin --

[hadoop@ip-172-31-47-75 ~]$ grep  -i myconcat /var/log/presto/launcher.log 
[Loaded com.henoc.presto.MyConcatPlugin from file:/usr/lib/presto/plugin/myconcat-plugin/myconcat.jar]
...
[Loaded com.henoc.presto.MyConcat from file:/usr/lib/presto/plugin/myconcat-plugin/myconcat.jar]
...

[hadoop@ip-172-31-47-75 ~]$ presto-cli --execute "show functions;" | grep -i myconcat
"myconcat","varchar","varchar, varchar","scalar","true","concatenates two strings"

[hadoop@ip-172-31-47-75 ~]$ presto-cli 
presto> SELECT myconcat('hello',' world!');
    _col0     
--------------
 hello world! 
(1 row)

Query 20180528_112619_00001_e2zfr, FINISHED, 1 node
Splits: 17 total, 17 done (100.00%)
0:00 [0 rows, 0B] [0 rows/s, 0B/s]
```