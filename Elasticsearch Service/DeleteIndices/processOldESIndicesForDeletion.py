#!/usr/bin/python
from __future__ import print_function

import requests
import datetime
import time
import sys
from pprint import pprint

########## MAIN CODE ##########
print ("-------------------")
print ("Starting program...\n")

def get_indices():

    ##### Variable Declarations
    esEndpoint="http://"+sys.argv[1]+"/"

    indicesList=[]
    creationTimes=[]
    removeElements=[]
    temp_list = []
    # get the list of all available indices.
    indices = requests.get(esEndpoint+"_cat/indices")
    result = indices.text.split('\n')
    del result[-1]

    for line in result:
        indicesList.append(line.split()[2])


    # remove the .kibana4 (or ".kibana" in ES 5.1) index from the list as it is a required/default index in ES.
    if ".kibana-4" in indicesList:
        indicesList.remove(".kibana-4")
    elif ".kibana" in indicesList:
        indicesList.remove(".kibana")



    # get the creation times for the indices.
    for i in range (0,len(indicesList)):
        cdates = requests.get(esEndpoint+indicesList[i])
        cdates2 = cdates.json()
        creationTimes.append(cdates2[indicesList[i]]['settings']['index']['creation_date'])


    print ("\n\nEpoch Timestamps in human readable format are: ")
    print ("IndexName\t\tCreationTime (Epoch)\tCreationTime (Human Readable - UTC)")
    for i in range (0,len(creationTimes)):
        print (indicesList[i]+": \t\t"+creationTimes[i]+"\t\t"+datetime.datetime.fromtimestamp(float(creationTimes[i]) / 1000).strftime('%Y-%m-%d %H:%M:%S'))
    print ("")

    temp_list = [indicesList,creationTimes,removeElements,esEndpoint]
    return temp_list

list_l = get_indices()

### get the value from the user which determines which indices we should remove. 

print ("Do you want to delete indices based on minutes, hours or days?")
print("Please select the corresponding number")
print("1. Minutes")
print("2. Hours")
print("3. Days")
choice_number = str(input())
if choice_number == "1":
    print("You have selected 1, please enter the value in Minutes")
    choice_minutes = int(input())
    offset = 1000*60*choice_minutes
    print("The offset is set as",offset)

elif choice_number == "2":
    print("You have selected 2, please enter the value in Hours")
    choice_hours = int(input())
    offset = 1000*60*60*choice_hours
    print("The offset is set as",offset)


elif choice_number == "3":
    print("You have selected 3, please enter the value in Days")
    choice_days = int(input())
    offset = 1000*60*60*24*choice_days
    print("The offset is set as",offset)

currentTime = int(time.time() * 1000)
checkTime = currentTime - offset

indicesList = list_l[0]
creationTimes = list_l[1]
removeElements = list_l[2]
esEndpoint = list_l[3]

# check the element values to see if they are outside the threshold time. Add the index element numbers to an array.
for i in range (0, len(creationTimes)):
    if checkTime > int(creationTimes[i]):
        removeElements.append(i)

# If there are no indices in the threshold time, exit the program - else continue on...
print ("\nThreshold time (UTC) to check indices against is:")
print (datetime.datetime.fromtimestamp(checkTime / 1000).strftime('%Y-%m-%d %H:%M:%S'))
if (len(removeElements) != 0):
    print ("\nThe following indices are candidates for removal:")
    for element in removeElements:
        print (indicesList[element])
else:
    print ("\nThere are no indices that are older than the threshold time of: " + (datetime.datetime.fromtimestamp(checkTime / 1000).strftime('%Y-%m-%d %H:%M:%S')))
    print ("\nExiting program...")
    print ("-------------------\n\n")
    sys.exit(0)


print ("\n\nAre you sure that you have taken a manual snapshot? (Yes/No)")
print ("> ", end="")
choice = raw_input().upper()
if ((choice == 'Y') or (choice == 'YES') or (choice == 'yes') or (choice == 'y')):

    # Index candidates found for deletion. Continuing on with the program.
    print ("\n\nAre you sure you wish to remove indices that were created before this threshold value? (Yes/No)")
    print ("This option can NOT be undone!")
    print ("> ", end="")
    choice = raw_input().upper()


    if ((choice == 'Y') or (choice == 'YES')):
        #remove the indices
        print ("Removing the indices...")
        for element in removeElements:
            delete = requests.delete(esEndpoint+indicesList[element])
            print ("Index removed: "+indicesList[element])

        print("\nIndices successfully removed.")
        print ("-------------------\n\n")

        time.sleep(2)

        # get the new list of all available indices.

        get_indices()

    else:
        print ("'No' option selected or invalid input. Exiting without removing any indices.")
        print ("If 'Yes' was desired, please re-run this program")
        print ("-------------------\n\n")
        sys.exit(0)
else:
    print ("Please take a manual snapshot!!!!")
    print ("For more information please follow the link here: https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-managedomains-snapshots.html")
    sys.exit(0)


    ########## END OF MAIN CODE ##########
