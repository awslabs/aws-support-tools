package com.example.fcmsampleapp;

import android.app.IntentService;
import android.content.Intent;
import android.util.Log;

import com.google.firebase.iid.FirebaseInstanceId;

public class RegistrationIntentService extends IntentService {

    private static final String TAG = "RegIntentService";

    public RegistrationIntentService() {
        super(TAG);
    }

    @Override
    protected void onHandleIntent(Intent intent) {
        try {
            String token = FirebaseInstanceId.getInstance().getToken();
            Log.i(TAG, "FCM Registration Token: " + token);
            // TODO: Implement this method to send any registration to your app's servers.
            sendRegistrationToServer(token);
        } catch (Exception e) {
            Log.d(TAG, "Failed to complete token refresh", e);
        }
    }

    private void sendRegistrationToServer(String token) {
        // TODO: send the token to SNS and create platform endpoint
    }
}
