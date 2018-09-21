#!/bin/bash

#  Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at
#
#      http://aws.amazon.com/asl/
#
#    or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.

#Example Invocation
#./dbconv_tablename_noquotes.sh --rds_jdbc=jdbc:mysql://dbtest.cob91vaba6fq.us-east-1.rds.amazonaws.com:3306/myrdsdb
# --rds_tbl=customer --rds_pwd=testpassword --rds_usr=admin
# --red_jdbc=jdbc:postgresql://eudb3.cvprvckckqrm.eu-west-1.redshift.amazonaws.com:5439/dbtest?tcpKeepAlive=true
# --red_usr=admin --red_pwd=test123E —red_tbl=RedTub
# —red_dist=customer_id —red_sort=create_date --red_ins=OVERWRITE_EXISTING


echo "Number of arguments: $#"
#echo "Arguments: $@"

for i in "$@"
do
case "$i" in
    --rds_jdbc=*|-a=*)
    RDSJdbc="${i#*=}"
    shift
    ;;
    -b=*|--rds_usr=*)
    RDSUsr="${i#*=}"
    shift
    ;;
    -c=*|--rds_pwd=*)
    RDSPwd="${i#*=}"
    shift
    ;;
    -d=*|--rds_tbl=*)
    RDSTbl="${i#*=}"
    shift
    ;;
    -e=*|--red_jdbc=*)
    REDJdbc="${i#*=}"
    shift
    ;;
    -f=*|--red_usr=*)
    REDUsr="${i#*=}"
    shift
    ;;
    -g=*|--red_pwd=*)
    REDPwd="${i#*=}"
    shift
    ;;
    -h=*|--red_tbl=*)
    REDTbl="${i#*=}"
    shift
    ;;
    -i=*|--red_dist=*)
    REDDist="${i#*=}"
    shift
    ;;
    -j=*|--red_sort=*)
    REDSort="${i#*=}"
    shift
    ;;
    -k=*|--red_map=*)
    REDMap="${i#*=}"
    shift
    ;;
    -l=*|--red_ins=*)
    REDIns="${i#*=}"
    shift
    ;;
    *)
    echo "unknown option"
    ;;
esac
done

echo "RDS Jdbc: $RDSJdbc"
echo "RDS Usr: $RDSUsr"
echo "RDS Tbl: $RDSTbl"

echo "REDShift Jdbc: $REDJdbc"
echo "RED Usr: $REDUsr"
echo "(Optional) REDShift Generated Tbl: $REDTbl"
echo "(Optional) REDShift Distribution Key: $REDDist"
echo "(Optional) REDShift Sort Key(s): $REDSort"
echo "(Optional) REDShift Default Translation Override Map: $REDMap"
echo "(Optional) REDShift Data Insert Mode: $REDIns"

# exit script on error
set -e

#1. Install MySQL and PSQL client including mysqldump
sudo yum install mysql postgresql93 -y


#2. Parse RDS Jdbc Connect String
RDSHost=`echo $RDSJdbc | awk -F: '{print $3}' | sed 's/\///g'`
echo "RDS Host: $RDSHost"
RDSPort=`echo $RDSJdbc | awk -F: '{print $4}' | awk -F/ '{print $1}'`
echo "RDS Port: $RDSPort"
MySQLDb=`echo $RDSJdbc | awk -F: '{print $4}' | awk -F/ '{print $2}'`
echo "RDS MySQLDB: $MySQLDb"

#3. Parse Redshift Jdbc Connect String
#"jdbc:postgresql://eudb3.cvprvckckqrm.eu-west-1.redshift.amazonaws.com:5439/dbtest?tcpKeepAlive=true"
REDHost=`echo $REDJdbc | awk -F: '{print $3}' | sed 's/\///g'`
echo "REDShift Host: $REDHost"
REDPort=`echo $REDJdbc | awk -F: '{print $4}' | awk -F/ '{print $1}'`
echo "REDShift Port: $REDPort"
REDDb=`echo $REDJdbc | awk -F: '{print $4}' | awk -F/ '{print $2}' | awk -F? '{print $1}'`
echo "REDShift DB: $REDDb"

#4. Dump MySQL Table definition
MySQLFile=rdsmy$(date +%m%d%H%M%S).sql
echo "My SQL dump file: $MySQLFile"
`mysqldump -h $RDSHost --port=$RDSPort -u $RDSUsr --password=$RDSPwd  --compatible=postgresql --default-character-set=utf8 -n -d -r $MySQLFile $MySQLDb $RDSTbl`
echo "$MySQLFile created"


#5. Download the translator python script from where you hosted it in your S3 bucket
curl -O https://s3.amazonaws.com/testbucket/scripts/mysql_to_redshift_tablename_noquotes.py


#6. Translate MySQL to Redshift
RedFile=red$(date +%m%d%H%M%S).psql
echo "created $RedFile file for writing"
echo "calling python script to generate redshift file"
python mysql_to_redshift_tablename_noquotes.py --input_file=$MySQLFile --output_file=$RedFile --table_name=$REDTbl  --dist_key=$REDDist --sort_keys=$REDSort --map_types=$REDMap --insert_mode=$REDIns
echo "Generated Redshift file: $RedFile"


#7. Import it into Redshift
export PGPASSWORD=$REDPwd
psql -h $REDHost -p $REDPort -U $REDUsr -d $REDDb -f $RedFile
