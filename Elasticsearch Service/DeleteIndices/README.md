Use-Case:
~~~~~~~~

What if you want the ability to list out all your indices in your ES cluster and be able to delete indices older than a time value specified by you?


The attached script in this article will solve the above Use-Case as it reads the indexes creation_time data and uses that to determine the age of the index. It uses the "requests" library in python to get the index data from your ES cluster including its creation time. The level of granularity for specifying time in the script is in Minutes, Hours or Days.

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
PLEASE NOTE:
~~~~~~~~~~~~~

-IT IS HIGHLY ADVISED TO TAKE A MANUAL SNAPSHOT OF YOUR ES CLUSTER BEFORE USING THIS SCRIPT.
-PLEASE FOLLOW THE INSTRUCTIONS AT THE PROVIDED LINK TO CREATE A MANUAL SNAPSHOT BEFORE USING THIS SCRIPT.
-AWS IS NOT AT FAULT FOR ANY DATA LOSS OR MISUSE OF THIS SCRIPT.

ES manual snapshot:
http://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-managedomains.html#es-managedomains-snapshots

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

Summary of Script Execution:
~~~~~~~~~~~~~~~~~~~~~~~~~

1) The script prompts the user to choose one of the following:
    Minutes, Hours or Days to specify the time value.

2) Based on what is selected above, the user enters a value which could be in Minutes, Hours or Days.

3) The indices found are displayed to the user.

4) A check is done to see if any indices are older than the time offset.

5) It then does a quick calculation to see if each index is older than the user specified value. If they are, their position in the list is noted, and these indices are then passed to the delete request against the ES API to delete these indices from your ES Cluster. If no index candidates are found, the script exits.

6) If some indices are found to be older than the user specified value, then the user is prompted if they have taken a manual snapshot before proceeding. If "No" the script exits.

7) The user is asked if they are sure that they want to delete their indices.

8) If the user select "Y" or "yes", the index positions that were flagged are deleted from the ES cluster.

Using the Code:
~~~~~~~~~~~~~
To use the code, all you need to do is to pass in your Elasticsearch endpoint as an argument, For example:

**********
python processOldESIndicesForDeletion.py myElasticsearchEndpoint.us-east-1.es.amazonaws.com
**********


