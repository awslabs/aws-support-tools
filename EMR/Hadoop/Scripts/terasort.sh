#!/bin/bash

# A script that runs Terasort MapReduce application to stress test a Hadoop cluster
# By default, this script runs Terasort job 50 times on with each iteration on 10TB of data. You can optionally provide the number of runs as a parameter to the script. 
# Reference - http://hadoop.apache.org/docs/r2.7.3/api/org/apache/hadoop/examples/terasort/package-summary.html

runs=$1

if [ -z $runs ]; then
    runs=50
fi

# remove input directory if any
hadoop fs -rmr /mnt/var/terasort/10t/input

# for teragen
time -p hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar teragen 100000000000 /mnt/var/terasort/10t/input

# for terasort
count=0
while [ $count -lt $runs ]; do
    nohup time -p hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar terasort /mnt/var/terasort/10t/input /mnt/var/terasort/10t/output
    let count=count+1
done