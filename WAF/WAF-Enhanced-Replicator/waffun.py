#!/usr/bin/env python3

# Modules Importing
from __future__ import print_function
from datetime import datetime
import sys, os, uuid
import boto3

# Constants Section
versionNumber = "1.0"
versionBuild = "Build Date 2019-05-27"
accountLength = 12

if os.environ.get('LC_CTYPE', '') == 'UTF-8':
    os.environ['LC_CTYPE'] = 'en_US.UTF-8'

def getVersion():
    '''
    Prints the composite of current version and build date.
    '''
    return (versionNumber + " | " + versionBuild)

def header():
    '''
    Prints Utility's Header.
    '''
    headerMessage = "WAFER - AWS WAF Enhanced Replicator - Version " + getVersion() + "\n" \
                    "This utility works with WAF v1 (classical) only.\n"
    print(headerMessage)

def usage():
    '''
    Prints the correct utility usage.
    '''
    usageMessage = "Usage:\n" \
                   "    wafer {global | regional --region <AWS region>} [--web-acl <Web ACL ID>]\n\n" \
                   "    Notes:\n" \
                   "    1. You must choose the scope to be either global OR regional.\n" \
                   "    2. If you choose regional, you must provide one valid AWS region.\n" \
                   "    3. Optionally, regardless of the scope, you can directly provide the desired Web ACL ID.\n"
    
    print(usageMessage)
    return(-1)

def isValidRegion(checkRegion):
    '''
    Verifies if the provided region is an existing AWS region.
    '''
    client = boto3.client('ec2')
    regions = [region['RegionName'] for region in client.describe_regions()['Regions']]

    return(checkRegion in regions)

def validateArguments():
    '''
    Checks the command line parameters and returns an output code.
    '''
    # Lowering the case of the command line parameters
    parameters = [par.lower() for par in sys.argv]

    if len(parameters) == 1:
        return([usage(), "", ""])

    if ("global" in parameters) and ("regional" in parameters):
        return([usage(), "", ""])

    if (not "global" in parameters) and (not "regional" in parameters):
        return([usage(), "", ""])
    
    webAcl = ""
    if '--web-acl' in parameters:
        webacl_idx = parameters.index('--web-acl') + 1
        webAcl = parameters[webacl_idx]
    
    if "global" in parameters:
        return([1, "", webAcl])

    region = ""
    if "regional" in parameters:
        if not "--region" in parameters:
            return([usage(), "", ""])
        region_idx = parameters.index('--region') + 1
        region = parameters[region_idx]
        if not isValidRegion(region):
            print("*** Invalid AWS Region! ***\n", file=sys.stderr)
            return([usage(), "", ""])
        return([2, region, webAcl])

def getHomeConfig():
    '''
    Checks operating system, the existence of home directory.
    In case it does not exist, creates it and also returns the corresponding UUID 
    to be considered during logging and template creation.
    '''
    home = os.path.expanduser('~')
    if ("linux" in sys.platform) or ("darwin" in sys.platform):
        separator = "/"
    elif ("win32" in sys.platform) or ("win64" in sys.platform):
        separator = "\\"
    home = home + separator + ".wafer"

    if not os.path.exists(home):
        try:
            os.mkdir(home)
        except:
            print("Unable to create configuration directory! Check permissions or disk usage on " + home + ".\n", file=sys.stderr)
            sys.exit (-1)
    
    templatesDir = home + separator + "templates"
    if not os.path.exists(templatesDir):
        try:
            os.mkdir(templatesDir)
        except:
            print("Unable to create templates directory " + templatesDir + "! Check permissions or disk usage.\n", file=sys.stderr)
            sys.exit (-1)
    
    logsDir = home + separator + "logs"
    if not os.path.exists(logsDir):
        try:        
            os.mkdir(logsDir)
        except:
            print("Unable to create logs directory " + logsDir + "! Check permissions or disk usage.\n", file=sys.stderr)
            sys.exit (-1)
    
    uniqueId = str(uuid.uuid4())
    uniqueLogName = logsDir + separator + "wafer-log-" + uniqueId + ".log"

    if os.path.exists(uniqueLogName):
        while os.path.exists(uniqueLogName):
            uniqueId = str(uuid.uuid4())
            uniqueLogName = logsDir + separator + "wafer-log-" + uniqueId + ".log"
    uniqueTemplateName = templatesDir + separator + "wafer-tf-" + uniqueId + ".tf"
    uniqueZipFile = home + separator + "wafer-pkg-" + uniqueId + ".zip"
    
    return ([uniqueLogName, uniqueTemplateName, uniqueZipFile])

def getFormattedDateTime():
    '''
    Builds a formatted date and time to be used in logging.
    '''
    return (datetime.utcnow().strftime("%Y-%m-%d - %H:%M:%S UTC: "))

def abortMission(logFile, templateFile, apiCall):
    '''
    Closes the log and template files, throws an error message and exits with -1.
    '''
    if len(apiCall) > 0:
        print("*** Failure on making API call: {}! ***".format(apiCall), file=sys.stderr)
        logFile.write(getFormattedDateTime() + "*** Failure on making API call: " + apiCall + "! ***\n")
    print("*** Aborting program execution. ***\n", file=sys.stderr)
    logFile.write(getFormattedDateTime() + "End of Log.")
    logFile.close()
    templateFile.close()
    sys.exit(-1)
