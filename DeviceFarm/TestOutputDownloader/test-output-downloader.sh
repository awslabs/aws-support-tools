#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

AWSDFCMD="aws devicefarm --region us-west-2 --output text"
DOWNLDROOT="."
DLFOLDER="."

declare PRJECT_ID=""
RUN_ID=""
JOB_ID=""
SUITE_ID=""
TEST_ID=""
declare URL_TYPE=1 # 1:RUN, 2:JOB, 3:SUITE, 4:TEST;
declare RUN_TYPE=1 # 1:Mobile 2. Browser

verify_input() {
    if [ -z "$1" ]; then
        echo "This script downloads AWS Device Farm logs for troubleshooting."
        echo
        echo "Usage: "
        echo "  $0 <AWS devicefarm console URL>"
        echo
        exit 1
    fi

    servicename="$(echo $1 | cut -d? -f1)"
    if ! [ "$servicename" = "https://us-west-2.console.aws.amazon.com/devicefarm/home" ]; then
        echo "!ERROR: only accept valid console URLs from Device Farm runs, jobs, suites, test."
        echo "        Please check the URL or copy it again from the browser then rerun the tool."
        echo
        exit 1
    fi
}

parse_input_url_app() {
    echo
    echo 'Details retrieved from URL:'
    PRJECT_ID="$(echo $1 | cut -d/ -f7)"
    echo ' 1. ProjectID: ' $PRJECT_ID

    # Read and parse the URL, decide the URL type
    RUN_ID="$(echo $1 | cut -d/ -f9)"
    if ! [ $RUN_ID ]; then
        echo " No valid ID of runs, jobs, suites or test found in the URL."
        echo
        echo "!ERROR: Cannot find valid ID of runs, jobs, suites or test in the URL."
        echo
        exit 1
    fi
    echo ' 2. Run ID: ' $RUN_ID

    JOB_ID="$(echo $1 | cut -d/ -f11)"
    if ! [ $JOB_ID ]; then
        echo
        echo "A test run URL is provided."
        URL_TYPE=1
        return 0
    fi
    echo ' 3. Job ID: ' $JOB_ID

    SUITE_ID="$(echo $1 | cut -d/ -f13)"
    if ! [ $SUITE_ID ]; then
        echo
        echo "A test job URL is provided."
        URL_TYPE=2
        return 0
    fi
    echo ' 4. Suite ID:' $SUITE_ID

    TEST_ID="$(echo $1 | cut -d/ -f15)"
    if ! [ $TEST_ID ]; then
        echo
        echo "A test suite URL is provided."
        URL_TYPE=3
        return 0
    fi
    echo ' 5. Test ID:' $TEST_ID
    echo
    echo "A specific test URL is provided."
    URL_TYPE=4
    return 0
}

check_awscli_cred() {
    if [ -z $(which aws) ]; then
        echo
        echo "!ERROR: need to install AWSCLI tool to use this script."
        echo
        exit 1
    fi
    TRY_GETPROJ=$($AWSDFCMD list-projects)
    if ! [ $? -eq 0 ]; then
        echo "!ERROR: cannot run device farm AWSCLI using default profile, please correct the profile configuration then try again."
        echo
        exit 1
    fi

    ARN_PART1="$(echo $TRY_GETPROJ | cut -d" " -f2 | sed 's/:project.*$//g')"
}

get_test_artifacts() {
    if ! [ $URL_TYPE -eq 4 ]; then
        TEST_ARN="$1"
        TEST_ID="$(echo $TEST_ARN | cut -d/ -f5)"
        SUITE_ID="$(echo $TEST_ARN | cut -d/ -f4)"
    else TEST_ARN="$ARN_PART1:test:$PRJECT_ID/$RUN_ID/$JOB_ID/$SUITE_ID/$TEST_ID"; fi
    declare -a ARTI_TYPE=("LOG" "FILE" "SCREENSHOT")

    # Create subfolder for the test-id
    DLFOLDER=$DOWNLDROOT/$PRJECT_ID/$RUN_ID/$JOB_ID/$SUITE_ID/$TEST_ID
    mkdir -p $DLFOLDER
    if ! [ $? -eq 0 ]; then
        echo "!ERROR: Failed to create folder to save files, exiting..."
        exit 1
    fi
    echo "---> Save to folder: $DLFOLDER"

    # Loop through the ARTI_TYPE for all artifacts
    for DN_TYPE in "${ARTI_TYPE[@]}"; do
        # List all test artifacts in one type
        CMDOUTPUT=$($AWSDFCMD list-artifacts --arn $TEST_ARN --type $DN_TYPE)
        if ! [ "$CMDOUTPUT" ]; then
            echo
            echo "---> No artifact found in type: $DN_TYPE"
            echo
            continue
        fi

        echo
        echo "---> Downloading artifact type: $DN_TYPE"

        ARTILIST="$(echo -e $CMDOUTPUT | sed 's/ ARTIFACTS/\\n/g')"
        ARTICOUNT="$(echo -e $ARTILIST | wc -l)"
        echo "---> Found" $ARTICOUNT "artifacts:"

        ARTICNTER=1
        while [ $ARTICNTER -le $ARTICOUNT ]; do
            ARTIINFO="$(echo -e $ARTILIST | sed "${ARTICNTER}q;d")"
            ARTIURL="$(echo $ARTIINFO | sed 's/^.*https/https/g')"
            ARTINAME="$(echo $ARTIURL | cut -d? -f1 | cut -d/ -f10)"
            ARTITYPE="$(echo -e $ARTIINFO | sed 's/ https/\\n/g')"
            ARTITYPE="$(echo -e $ARTITYPE | sed '$ d' | sed 's/^.* //g')"
            echo "----> Getting artifact file: $ARTINAME, type: $ARTITYPE"
            curl --progress-bar $ARTIURL -o $DLFOLDER/$ARTITYPE\_$ARTINAME
            ARTICNTER=$(($ARTICNTER + 1))
        done
    done
}

get_tests_from_suite() {
    if ! [ $URL_TYPE -eq 3 ]; then SUITE_ARN="$1"; else SUITE_ARN="$ARN_PART1:suite:$PRJECT_ID/$RUN_ID/$JOB_ID/$SUITE_ID"; fi

    # Get tests details from the suite
    CMDOUTPUT=$($AWSDFCMD list-tests --arn $SUITE_ARN)

    TEST_1ST_ARN="$(echo $CMDOUTPUT | grep " " | cut -d" " -f2)"
    TEST_NUMBER="$(echo $CMDOUTPUT | grep -o "TESTS " | wc -l | sed 's/ //g')"
    echo "-> Found $TEST_NUMBER tests in this suite."

    # Loop through all tests
    TEST_CNTER=0
    while [ $TEST_CNTER -lt $TEST_NUMBER ]; do
        TEST_ARN="$(echo $TEST_1ST_ARN | sed "s/.$/$TEST_CNTER/g")"
        echo "--> Processing test $TEST_CNTER:" $TEST_ARN
        get_test_artifacts $TEST_ARN
        TEST_CNTER=$(($TEST_CNTER + 1))
    done
}

get_suites_from_job() {
    if ! [ $URL_TYPE -eq 2 ]; then JOB_ARN="$1"; else JOB_ARN="$ARN_PART1:job:$PRJECT_ID/$RUN_ID/$JOB_ID"; fi

    # Get suite details from the job
    CMDOUTPUT=$($AWSDFCMD list-suites --arn $JOB_ARN)

    # Get the job's details
    SUITE_1ST_ARN="$(echo $CMDOUTPUT | grep " " | cut -d" " -f2)"
    SUITE_NUMBER="$(echo $CMDOUTPUT | grep -o "SUITES " | wc -l | sed 's/ //g')"
    echo "> Found $SUITE_NUMBER suites in this job."
    echo

    # Loop through all suites
    SUITE_CNTER=0
    while [ $SUITE_CNTER -lt $SUITE_NUMBER ]; do
        SUITE_ARN="$(echo $SUITE_1ST_ARN | sed "s/.$/$SUITE_CNTER/g")"
        echo "-> Processing suite $SUITE_CNTER: " $SUITE_ARN
        get_tests_from_suite $SUITE_ARN
        SUITE_CNTER=$(($SUITE_CNTER + 1))
    done
}

get_jobs_from_run() {
    if ! [ $URL_TYPE -eq 1 ]; then RUN_ARN="$1"; else RUN_ARN="$ARN_PART1:run:$PRJECT_ID/$RUN_ID"; fi
    echo "Processing run: $RUN_ARN"
    echo

    # Get jobs from the run
    CMDOUTPUT="$($AWSDFCMD list-jobs --arn $RUN_ARN)"

    # Get the run's details
    JOB_1ST_ARN="$(echo $CMDOUTPUT | cut -d" " -f2)"
    JOB_NUMBER="$(echo $CMDOUTPUT | grep -o "JOBS " | wc -l | sed 's/ //g')"
    echo "Found $JOB_NUMBER jobs(devices) in this run."

    # Loop through all jobs
    JOB_CNTER=0
    while [ $JOB_CNTER -lt $JOB_NUMBER ]; do
        JOB_ARN="$(echo $JOB_1ST_ARN | sed "s/.$/$JOB_CNTER/g")"
        echo "> Processing job $JOB_CNTER: " $JOB_ARN
        get_suites_from_job $JOB_ARN
        JOB_CNTER=$(($JOB_CNTER + 1))
    done
}

handle_browser_url() {
    echo
    echo 'Testgrid browser test url, details retrieved:'
    echo
    PRJECT_ID="$(echo $1 | cut -d/ -f7)"
    echo ' 1. ProjectID: ' $PRJECT_ID
    RUN_ID="$(echo $1 | cut -d/ -f10)"
    if ! [ $RUN_ID ]; then
        echo "   No valid ID of runs, jobs, suites or test found in the URL."
        echo
        echo "!ERROR: Cannot find valid ID of runs, jobs, suites or test in the URL."
        echo
        exit 1
    fi
    echo ' 2. Session ID: ' $RUN_ID
    SESSION_ARN=$ARN_PART1:testgrid-session:$PRJECT_ID/$RUN_ID

    declare -a ARTI_TYPE=("LOG" "VIDEO")
    # Create subfolder for the test-id
    DLFOLDER=$DOWNLDROOT/$PRJECT_ID/$RUN_ID
    mkdir -p $DLFOLDER
    if ! [ $? -eq 0 ]; then
        echo "!ERROR: Failed to create folder to save files, exiting..."
        exit 1
    fi

    # Loop through the ARTI_TYPE for all artifacts
    for DN_TYPE in "${ARTI_TYPE[@]}"; do
        # List all test artifacts in one type
        CMDOUTPUT=$($AWSDFCMD list-test-grid-session-artifacts --session-arn $SESSION_ARN --type $DN_TYPE)
        if ! [ "$CMDOUTPUT" ]; then
            echo
            echo "---> No artifact found in type: $DN_TYPE"
            echo
            continue
        fi

        echo
        echo "---> Downloading artifact type: $DN_TYPE"
        ARTILIST="$(echo -e $CMDOUTPUT | sed 's/ ARTIFACTS/\\nARTIFACTS/g')"
        ARTICOUNT="$(echo -e $ARTILIST | wc -l)"
        echo "---> Found" $ARTICOUNT "artifacts:"

        ARTICNTER=1
        while [ $ARTICNTER -le $ARTICOUNT ]; do
            ARTIINFO="$(echo -e $ARTILIST | sed "${ARTICNTER}q;d")"
            ARTINAME="$(echo $ARTIINFO | cut -d' ' -f2)"
            ARTITYPE="$(echo $ARTIINFO | cut -d' ' -f3)"
            ARTIURL="$(echo $ARTIINFO | cut -d' ' -f4)"

            echo "----> Getting artifact file: $ARTINAME, type: $ARTITYPE"
            curl --progress-bar $ARTIURL -o $DLFOLDER/$ARTITYPE\_$ARTINAME
            ARTICNTER=$(($ARTICNTER + 1))
        done
    done
}

main() {
    verify_input "$1" # valiate URL

    check_awscli_cred # check awscli and awscli credentials

    if [[ "$1" = *runsselenium* ]]; then
        # handle browser test URL
        handle_browser_url "$1"

    else
        parse_input_url_app "$1" # parse the URL to check the URL type (run, job, suite, test)

        case $URL_TYPE in
        1)
            Message="get_jobs_from_run"
            get_jobs_from_run "$1"
            ;;
        2)
            Message="get_suites_from_job"
            get_suites_from_job "$1"
            ;;
        3)
            Message="get_tests_from_suite"
            get_tests_from_suite "$1"
            ;;
        4)
            Message="get_test_artifacts"
            get_test_artifacts "$1"
            ;;
        *)
            echo "!ERROR: cannot verify the URL, please check your input and try again."
            echo
            exit 1
            ;;
        esac
    fi
    # zip -r9 ./aws-df-$PRJECT_ID.zip $DOWNLDROOT/$PRJECT_ID &>/dev/null
    tar czf ./aws-df-$PRJECT_ID.tgz $DOWNLDROOT/$PRJECT_ID &>/dev/null
    echo
    echo "Done, all logs downloaded into this file: ./aws-df-$PRJECT_ID.tgz"
    echo
    rm -fr "$DOWNLDROOT/$PRJECT_ID"
}

main "$@"
