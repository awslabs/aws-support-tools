#!/usr/bin/env python

#  Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at
#
#      http://aws.amazon.com/asl/
#
#    or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.


"""
Fixes a MySQL dump made with the right format so it can be
imported to a Redshift database.

Dump using:
mysqldump --compatible=postgresql --default-character-set=utf8 -r databasename.mysql -u root databasename tablename

"""

import re
import sys
import os
import time
import getopt


def file_len(filename):
    """
    Returns the equivalent of wc - l
    :param filename: file name
    :return: number of lines in the file
    """
    with open(filename) as f:
        i = 0
        for i, l in enumerate(f):
            pass
    return i + 1


def parse(input_filename, output_filename, table_name, distribution_key, redshift_sort_keys, type_map):
    # State storage
    """
    Feed it a mysqldump file, and it'll output a redshift equivalent one.
    Optional params specified here are designed for mysqldump containing only one table definition


    :rtype : void
    :param input_filename: input mysqldump file
    :param output_filename:
    :param table_name: optional. generated table name for the first table encountered, else the same as input.
    :param distribution_key: optional. distribution key column in redshift for the first table encountered.
    :param redshift_sort_keys: optional. sort key(s) column(s) in redshift for the first table encountered.
    :param type_map: optional. override type conversion from mysql to redshift.
                     tinyint(1):smallint,char(35):varchar(70),bigint(20) unsigned:bigint
    :param insert_mode: optional. https://docs.aws.amazon.com/console/datapipeline/redshiftcopyactivity.
        Determines how to handle pre-existing data in the target table that overlaps with rows in the data to be loaded.
        "allowedValues": [ "OVERWRITE_EXISTING", "KEEP_EXISTING", "TRUNCATE"]
        if insert_mode is OVERWRITE_EXISTING and distribution_key not specified, first primary key is set as dist key.
    """
    if input_filename == "-":
        num_lines = -1
    else:
        num_lines = int(file_len(input_filename))
    tables = {}
    current_table = None
    creation_lines = []
    foreign_key_lines = []
    num_inserts = 0
    started = time.time()
    table_primary_key_not_done = True

    # Open output file and write header. Logging file handle will be std out
    # unless we're writing output to std out, in which case NO PROGRESS FOR YOU.
    if output_filename == "-":
        output = sys.stdout
        logging = open(os.devnull, "w")
    else:
        output = open(output_filename, "w")
        logging = sys.stdout

    if input_filename == "-":
        input_fh = sys.stdin
    else:
        input_fh = open(input_filename)

    output.write("-- Converted by MySql to Redshift db converter\n")
    output.write("START TRANSACTION;\n")

    for i, line in enumerate(input_fh):
        time_taken = time.time() - started
        percentage_done = (i + 1) / float(num_lines)
        secs_left = (time_taken / percentage_done) - time_taken
        logging.write("\rLine %i (of %s: %.2f%%) [%s tables] [%s inserts] [ETA: %i min %i sec]" % (
            i + 1,
            num_lines,
            ((i + 1) / float(num_lines)) * 100,
            len(tables),
            num_inserts,
            secs_left // 60,
            secs_left % 60,
        ))
        logging.flush()

        line = line.decode("utf8").strip()
        # Ignore comment lines
        if line.startswith("--") or line.startswith("/*") or line.startswith("LOCK TABLES") or line.startswith(
                "DROP TABLE") or line.startswith("UNLOCK TABLES") or not line:
            continue

        # Outside of anything handling
        if current_table is None:
            # Start of a table creation statement?
            if line.startswith("CREATE TABLE"):
                # current_table is the table name in MySQL
                current_table = line.split('"')[1]
                if table_name and not table_name.isspace():
                    logging.write("\rLine %i [Encountered table %s ] [Generated table name %s]" % (
                        i + 1, current_table, table_name))
                    current_table = table_name
                    table_name = None
                tables[current_table] = {"columns": []}
                creation_lines = []
                table_primary_key_not_done = True
            # Inserting data into a table?
            elif line.startswith("INSERT INTO"):
                output.write(line.encode("utf8").replace("'0000-00-00 00:00:00'", "NULL") + "\n")
                num_inserts += 1
            # ???
            else:
                print "\n ! Ignore. Unknown line in main body: %s" % line

        # Inside-create-statement handling
        else:
            # Is it a column?
            if line.startswith('"'):
                useless, name, definition = line.strip(",").split('"', 2)
                try:
                    sql_type, extra = definition.strip().split(" ", 1)

                    # This must be a tricky enum
                    if ')' in extra:
                        sql_type, extra = definition.strip().split(")")

                except ValueError:
                    sql_type = definition.strip()
                    extra = ""

                # check if extra contains unsigned
                unsigned = "unsigned" in extra.lower()
                # remove unsigned now
                extra = re.sub("CHARACTER SET [\w\d]+\s*", "", extra.replace("unsigned", ""))
                extra = re.sub("COLLATE [\w\d]+\s*", "", extra.replace("unsigned", ""))
                extra = extra.replace("AUTO_INCREMENT", "")
                extra = extra.replace("SERIAL", "")
                extra = extra.replace("ZEROFILL", "")
                extra = extra.replace("UNSIGNED", "")
                sql_type = sql_type.lower()

                # adding code to identify COMMENT portion in column definition and omitting the COMMENT
                # since Redshift does not support COMMENT in CREATE TABLE statement
                commentinextra = "COMMENT" in extra
                if commentinextra:
                    extra = extra.strip().split("COMMENT")[0].strip()


                if type_map is not None and sql_type in type_map:
                    red_type = type_map[sql_type]
                elif type_map is not None and unsigned and sql_type+ " unsigned" in type_map:
                    red_type = type_map[sql_type+ " unsigned"]
                elif sql_type == "tinyint(1)":
                    red_type = "boolean"
                elif sql_type.startswith("tinyint("):
                    red_type = "smallint"
                elif sql_type.startswith("smallint("):
                    if unsigned:
                        red_type = "integer"
                    else:
                        red_type = "smallint"
                elif sql_type.startswith("mediumint("):
                    red_type = "integer"
                elif sql_type.startswith("int("):
                    if unsigned:
                        red_type = "bigint"
                    else:
                        red_type = "integer"
                elif sql_type.startswith("bigint("):
                    if unsigned:
                        red_type = "varchar(80)"
                    else:
                        red_type = "bigint"
                elif sql_type.startswith("float"):
                    red_type = "real"
                elif sql_type.startswith("double"):
                    red_type = "double precision"
                elif sql_type.startswith("decimal"):
                    # same decimal
                    red_type = sql_type
                elif sql_type.startswith("char("):
                    size = int(sql_type.split("(")[1].rstrip(")"))
                    red_type = "varchar(%s)" % (size * 4)
                elif sql_type.startswith("varchar("):
                    size = int(sql_type.split("(")[1].rstrip(")"))
                    red_type = "varchar(%s)" % (size * 4)
                elif sql_type == "longtext":
                    red_type = "varchar(max)"
                elif sql_type == "mediumtext":
                    red_type = "varchar(max)"
                elif sql_type == "tinytext":
                    red_type = "text(%s)" % (255 * 4)
                elif sql_type == "text":
                    red_type = "varchar(max)"
                elif sql_type.startswith("enum(") or sql_type.startswith("set("):
                    red_type = "varchar(%s)" % (255 * 2)
                elif sql_type == "blob":
                    red_type = "varchar(max)"
                elif sql_type == "mediumblob":
                    red_type = "varchar(max)"
                elif sql_type == "longblob":
                    red_type = "varchar(max)"
                elif sql_type == "tinyblob":
                    red_type = "varchar(255)"
                elif sql_type.startswith("binary"):
                    red_type = "varchar(255)"
                elif sql_type == "date":
                    # same
                    red_type = sql_type
                elif sql_type == "time":
                    red_type = "varchar(40)"
                elif sql_type == "datetime":
                    red_type = "timestamp"
                elif sql_type == "year":
                    red_type = "varchar(16)"
                elif sql_type == "timestamp":
                    # same
                    red_type = sql_type
                    extra = extra.replace("CURRENT_TIMESTAMP", "sysdate")
                else:
                    # all else, e.g., varchar binary
                    red_type = "varchar(max)"

                # Record it
                creation_lines.append('"%s" %s %s' % (name, red_type, extra))
                tables[current_table]['columns'].append((name, red_type, extra))
            # Is it a constraint or something?
            elif line.startswith("PRIMARY KEY"):
                #composite primary key not supported in redshift
                if table_primary_key_not_done:
                    #aws datapipeline redshift copy only supports 1 primary key. remove this restriction after that is fixed
                    #creation_lines.append(line.rstrip(","))
                    first_pkey = line.rstrip(",").rstrip(")").lstrip("PRIMARY KEY").lstrip("(\"").split(",")[0].rstrip("\"")
                    pkey_line ='PRIMARY KEY("' + first_pkey + '")'
                    creation_lines.append(pkey_line)
                    if not distribution_key:
                        distribution_key = first_pkey
                    table_primary_key_not_done = False
            elif line.startswith("CONSTRAINT"):
                # Try adding foreign key in a different transaction. If it fails, no big deal.
                foreign_key_lines.append("ALTER TABLE \"%s\" ADD CONSTRAINT %s DEFERRABLE INITIALLY DEFERRED" % (
                    current_table, line.split("CONSTRAINT")[1].strip().rstrip(",")))
                # No need for index on foreign key column as Redshift does not support indexes
            elif line.startswith("UNIQUE KEY"):
                creation_lines.append("UNIQUE (%s)" % line.split("(")[1].split(")")[0])
            elif line.startswith("FULLTEXT KEY"):
                # No indexes in Redshift
                pass
            elif line.startswith("KEY"):
                pass
            # Is it the end of the table?
            elif line == ");":
                output.write("CREATE TABLE IF NOT EXISTS %s (\n" % current_table)
                for j, outline in enumerate(creation_lines):
                    output.write("    %s%s\n" % (outline, "," if j != (len(creation_lines) - 1) else ""))
                output.write(')\n')
                if distribution_key and not distribution_key.isspace():
                    output.write('distkey(%s)\n' % distribution_key)
                    distribution_key = None
                if redshift_sort_keys and not redshift_sort_keys.isspace():
                    output.write('sortkey(%s)\n' % redshift_sort_keys)
                    redshift_sort_keys = None
                output.write(';\n\n')
                current_table = None
            # ???
            else:
                print "\n ! Ignore. Unknown line inside table creation: %s" % line

    # Finish file
    output.write("COMMIT;\n")

    #output.write("START TRANSACTION;\n")
    # Write FK constraints out
    #output.write("\n-- Foreign keys --\n")
    #for line in foreign_key_lines:
    #    output.write("%s;\n" % line)
    # Finish file
    #output.write("\n")
    #output.write("COMMIT;\n")

    print ""


def usage():
    print("Usage: %s -i input -o output [-t table_name] [-d DistKey] [-s SortKey1,SortKey2...] "
          "[-m MySQL1:RedType1,MySQL2:RedType2...]" % sys.argv[0])


if __name__ == "__main__":

    input_file = ''
    output_file = ''
    gen_table_name = None
    dist_key = None
    sort_keys = None
    map_types = None
    insert_mode = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:o:t:d:s:m:n:",
                                   ["input_file=", "output_file=", "table_name=", "dist_key=", "sort_keys=",
                                    "map_types=", "insert_mode="])
    except getopt.GetoptError as e:
        print (str(e))
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-i", "--input_file"):
            input_file = arg
        elif opt in ("-o", "--output_file"):
            output_file = arg
        elif opt in ("-t", "--table_name"):
            gen_table_name = arg
        elif opt in ("-d", "--dist_key"):
            dist_key = arg
        elif opt in ("-s", "--sort_keys"):
            sort_keys = arg
        elif opt in ("-m", "--map_types"):
            map_types = arg
        elif opt in ("-n", "--insert_mode"):
            insert_mode = arg

    map_types_dict = None
    if map_types and not map_types.isspace():
        map_types_dict_temp = dict([arg.split(':') for arg in map_types.lower().lstrip().split(',')])
        #sanitize keys to strip whitespaces
        map_types_dict = dict()
        for key in map_types_dict_temp:
            map_types_dict[key.lstrip().rstrip()] = map_types_dict_temp[key]

    parse(input_file, output_file, gen_table_name, dist_key, sort_keys, map_types_dict)
    sys.exit(0)
