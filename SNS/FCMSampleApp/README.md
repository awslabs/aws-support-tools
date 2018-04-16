Android Firebase Cloud Messaging(FCM) Push Notification Steps
===============================
Simple GCM Test project with SNS integration based on FCM.
Google made public announcement that the GCM server and client APIs are deprecated and will be removed as soon as April 11, 2019 and all customer needs to update client and server code to use FCM before April 11, 2019. AWS SNS is compatible with FCM so you can still use SNS to deliver mobile push notification to mobile devices. Below is a sample demo code to show how to use FCM to deliver a mobile notification.

Please note these steps follow the Google Firebase guideline to demostrate how to use AWS SNS service integrating with Firebase Cloud Messaging(FCM) to deliver mobile push notification. The steps have been verified on April 16th, 2018 with Android Studio 3.0.1. The Firebase and Google service versions may be upgraded after then. And also be aware that the following steps are just for testing purpose.

Create Android Project
----------------------
1. In Android Studio create a new project with application name **FCMSampleApp**, Company domain **example.com** and select **Empty Activity**.
2. Enable Firebase Cloud services for this application by visiting [here](https://console.firebase.google.com/u/2/?pli=1).

    1. Create a project with a name, for example: **FCMTest**
    2. Add Firebase to your Android app
    3. For package name enter **com.example.fcmsampleapp**.
    4. Download the "google-services.json" for further use
    5. skip the Add Firebase SDK step as we will do it later and Finish.
    6. Click **Project Overview** -> **Project Settings** -> **CLOUD MESSAGING**. and Note down your Server Key
4. Move the downloaded **google-services.json** file to **FCMSampleApp** project **app/** directory.
5. In project level **build.gradle** under **dependencies {..}** include the following classpath:
    
    ```json    
    classpath 'com.google.gms:google-services:3.2.0'
    ```
    
6. In application level **build.gradle** add the following under **dependencies {..}**:

    ```json
    compile 'com.google.firebase:firebase-core:15.0.0'
    compile 'com.google.firebase:firebase-messaging:15.0.0'
    compile 'com.google.android.gms:play-services-base:15.0.0'
    ```
    
7. Also, in application level **build.gradle** add the following at the end of the file:

    ```json
    apply plugin: 'com.google.gms.google-services'
    ```
    
8. Add a new Java class **RegistrationIntentService** under **com.example.fcmsampleapp** package with the following contents:

    ```java
	        
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

    ```

9. Add a new Java class **MyFcmListenerService** under **com.example.fcmsampleapp** package with the following contents:

    ```java
    
    	package com.example.fcmsampleapp;
        import com.google.firebase.messaging.FirebaseMessagingService;
        import com.google.firebase.messaging.RemoteMessage;
        import android.util.Log;

        public class MyFcmListenerService extends FirebaseMessagingService {
            private static final String TAG = "MyFirebaseMsgService";

            @Override
            public void onMessageReceived(RemoteMessage remoteMessage) {
                Log.d(TAG, "Receive MSG From: " + remoteMessage.getFrom());
                if (remoteMessage.getData().size() > 0) {
                    Log.d(TAG, "Message data payload: " + remoteMessage.getData());
                }
            }
        }
    ```

9. Match or replace the content of **MainActivity** class with the following:

    ```java
    
        package com.example.fcmsampleapp;

        import android.content.Intent;
        import android.support.v7.app.AppCompatActivity;
        import android.os.Bundle;
        import android.util.Log;
        import com.google.android.gms.common.ConnectionResult;
        import com.google.android.gms.common.GoogleApiAvailability;

        public class MainActivity extends AppCompatActivity {

            private static final String TAG = "MainActivity";
            private static final int PLAY_SERVICES_RESOLUTION_REQUEST = 9000;

            @Override
            protected void onCreate(Bundle savedInstanceState) {
                super.onCreate(savedInstanceState);
                setContentView(R.layout.activity_main);
                if (checkPlayServices()) {
                    Intent intent = new Intent(this, RegistrationIntentService.class);
                    startService(intent);
                }
            }

            private boolean checkPlayServices() {
                GoogleApiAvailability apiAvailability = GoogleApiAvailability.getInstance();
                int resultCode = apiAvailability.isGooglePlayServicesAvailable(this);
                if (resultCode != ConnectionResult.SUCCESS) {
                    if (apiAvailability.isUserResolvableError(resultCode)) {
                        apiAvailability.getErrorDialog(this, resultCode, PLAY_SERVICES_RESOLUTION_REQUEST)
                                .show();
                    } else {
                        Log.i(TAG, "This device is not supported.");
                        finish();
                    }
                    return false;
                }
                return true;
            }
        }
    ```

10. Match or replace **AndroidManifest.xml** file with the following:

    ```xml
        <?xml version="1.0" encoding="utf-8"?>
        <manifest xmlns:android="http://schemas.android.com/apk/res/android"
            package="com.example.fcmsampleapp">

            <application
                android:allowBackup="true"
                android:icon="@mipmap/ic_launcher"
                android:label="@string/app_name"
                android:roundIcon="@mipmap/ic_launcher_round"
                android:supportsRtl="true"
                android:theme="@style/AppTheme">

                <activity android:name=".MainActivity">
                    <intent-filter>
                        <action android:name="android.intent.action.MAIN" />
                        <category android:name="android.intent.category.LAUNCHER" />
                    </intent-filter>
                </activity>

                <service
                    android:name=".MyFcmListenerService">
                    <intent-filter>
                        <action android:name="com.google.firebase.MESSAGING_EVENT"/>
                    </intent-filter>
                </service>

                <service
                    android:name=".RegistrationIntentService"
                    android:exported="false" >
                    <intent-filter>
                        <action android:name="com.google.android.c2dm.intent.RECEIVE" />
                    </intent-filter>
                </service>
            </application>

        </manifest>  
        ```

11. Run project to get **Registration Token** which will be printed out in the console.

Publishing Notification using CURL
----------------------------------
1. You can run the below command to send message to device:

    ```bash
    curl -X POST --header "Authorization: key=<your-key>" \
        --Header "Content-Type: application/json" \
        https://fcm.googleapis.com/fcm/send \
        -d "{\"to\":\"<yourtoken>\",\"data\":{\"Message\":\"mytest\"}}"
    ```
    
Publishing Notification using AWS SNS
-------------------------------------
Advantage of using SNS is scalability which is required when publishing tens of millions of notifications in a very short time and abstracts interaction with different push services behind a unified API.

1. Add a new platform application in SNS console -> Applications.
2. Enter **FCMSampleApp** for the name.
3. Select **GCM** from the **Push Notification Platform** drop down menu.
4. In the **API key** field paste your **Server API Key**.
5. Click **Create Platform Application** button.
6. Click on the new application ARN to enter.
7. Click **Create Platform Endpoint** button.
8. Paste your **Device Token** in the **Device token** field.
9. Enter optional data in **User Data** field.
10. Click **Add Endpoint** button.
11. Select the newly added endpoint from the list.
12. Click **Publish to endpoint** button.
13. Select **JSON** for **Message format**.
14. Enter the following in the **Message** box and click **Publish message** button.

    ```json
    {
    "GCM": "{ \"data\": { \"message\": \"Test message from SNS console.\", \"title\": \"FCMSampleApp\" } }"
    }
    ```        
    
