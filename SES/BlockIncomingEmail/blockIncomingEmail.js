'use strict';

const AWS = require('aws-sdk');

exports.handler = (event, context, callback) => {
    console.log('Blocking email filter starting');

    const sesNotification = event.Records[0].ses;
    const messageId = sesNotification.mail.messageId;
    const receipt = sesNotification.receipt;
    const mail = sesNotification.mail;  
 
    // Convert the environment variable into array. Clean spaces from it.
    var blockingListString = process.env.blockingList;
    blockingListString = blockingListString.replace(/\s/g,'');  
    var blockingListArray = blockingListString.split(",");

    // Check if the mail source matches with any of the email addresses or domains defined in the environment variable
    function isListed() {
        var length = blockingListArray.length;
        for(var i = 0; i < length; i++) {
            if (mail.source.endsWith(blockingListArray[i]))
                return true;
        }
        return false;
    }

    console.log('Processing message:', messageId);

        // Processing the message
    if (isListed()) {
            callback(null, {'disposition':'STOP_RULE_SET'});
            console.log('Rejecting messageId: ', messageId, ' - Source: ', mail.source, ' - Recipients: ',receipt.recipients,' - Subject: ', mail.commonHeaders['subject']);
    }
    else {
        console.log('Accepting messageId:', messageId, ' - Source: ', mail.source, ' - Recipients: ',receipt.recipients,' - Subject: ', mail.commonHeaders['subject']);
        callback();
    }
};
