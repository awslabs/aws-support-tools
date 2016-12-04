Android Push Notification Steps
===============================
Simple GCM Test project with SNS integration.

Create Android Project
----------------------
1. In Android Studio create a new project with application name **GCMSampleApp**, Company domain **example.com** and select **Empty Activity**.
2. Enable Google services for this application by visiting [here](https://developers.google.com/mobile/add?platform=android&cntapi=gcm&cnturl=https:%2F%2Fdevelopers.google.com%2Fcloud-messaging%2Fandroid%2Fclient&cntlbl=Continue%20Adding%20GCM%20Support&%3Fconfigured%3Dtrue).
    1. For app name enter **GCMSampleApp**.
    2. For package name enter **com.example.gcmsampleapp**.
    3. Click **Choose and configure services**.
    4. Click **Cloud Messaging** and **Enable**.
    5. Click **Generate configuration files**.
    6. Click **Download google-services.json**.
    7. Note down **Server API Key** as we will need this to push notification both using curl and SNS.
3. Move the downloaded **google-services.json** file to **GCMSampleApp** project **app/** directory.
4. In project level **build.gradle** under **dependencies {..}** include the following classpath:
    
    ```json    
    classpath 'com.google.gms:google-services:1.5.0-beta2'
    ```
    
5. In application level **build.gradle** add the following under **dependencies {..}**:

    ```json
    compile 'com.google.android.gms:play-services-gcm:8.3.0'
    ```
    
6. Also, in application level **build.gradle** add the following at the end of the file:

    ```json
    apply plugin: 'com.google.gms.google-services'
    ```
    
7. Add a new Java class **RegistrationIntentService** under **com.example.gcmsampleapp** package with the following contents:

    ```java
    
    package com.example.gcmsampleapp;

    import android.app.IntentService;
    import android.content.Intent;
    import android.util.Log;
    
    import com.google.android.gms.gcm.GoogleCloudMessaging;
    import com.google.android.gms.iid.InstanceID;
    
    public class RegistrationIntentService extends IntentService {
    
        private static final String TAG = "RegIntentService";
    
        public RegistrationIntentService() {
            super(TAG);
        }
    
        @Override
        protected void onHandleIntent(Intent intent) {
            Log.i(TAG, "Getting token.");
            try {
                InstanceID instanceID = InstanceID.getInstance(this);
                String token = instanceID.getToken(getString(R.string.gcm_defaultSenderId),
                        GoogleCloudMessaging.INSTANCE_ID_SCOPE, null);
                Log.i(TAG, "GCM Registration Token: " + token);
    
                // TODO: Implement this method to send any registration to your app's servers.
                sendRegistrationToServer(token);
    
            } catch (Exception e) {
                Log.d(TAG, "Failed to complete token refresh", e);
            }
        }
    
        private void sendRegistrationToServer(String token) {
    
        }
    }
    ```

8. Add a new Java class **MyGcmListenerService** under **com.example.gcmsampleapp** package with the following contents:

    ```java
    
    package com.example.gcmsampleapp;
    
    import android.app.NotificationManager;
    import android.app.PendingIntent;
    import android.content.Context;
    import android.content.Intent;
    import android.media.RingtoneManager;
    import android.net.Uri;
    import android.os.Bundle;
    import android.support.v4.app.NotificationCompat;
    import android.util.Log;
    
    import com.google.android.gms.gcm.GcmListenerService;
    
    public class MyGcmListenerService extends GcmListenerService {
    
        private static final String TAG = "MyGcmListenerService";
    
        @Override
        public void onMessageReceived(String from, Bundle data) {
            String title = data.getString("title");
            String message = data.getString("message");
            Log.d(TAG, "From: " + from);
            Log.d(TAG, "Title: " + title);
            Log.d(TAG, "Message: " + message);
    
            sendNotification(title, message);
        }
    
        private void sendNotification(String title, String message) {
            Intent intent = new Intent(this, MainActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            PendingIntent pendingIntent = PendingIntent.getActivity(this, 0 /* Request code */, intent,
                    PendingIntent.FLAG_ONE_SHOT);
    
            Uri defaultSoundUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
            NotificationCompat.Builder notificationBuilder = new NotificationCompat.Builder(this)
                    .setSmallIcon(R.drawable.common_ic_googleplayservices)
                    .setContentTitle(title)
                    .setContentText(message)
                    .setAutoCancel(true)
                    .setSound(defaultSoundUri)
                    .setContentIntent(pendingIntent);
    
            NotificationManager notificationManager =
                    (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
    
            notificationManager.notify(0 /* ID of notification */, notificationBuilder.build());
        }
    }
    ```

9. Match or replace the content of **MainActivity** class with the following:

    ```java
    
    package com.example.gcmsampleapp;
    
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
                // Start IntentService to register this application with GCM.
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
        package="com.example.gcmsampleapp">
    
        <uses-sdk android:minSdkVersion="8" android:targetSdkVersion="17"/>
        <uses-permission android:name="android.permission.INTERNET" />
        <uses-permission android:name="android.permission.WAKE_LOCK" />
        <uses-permission android:name="com.google.android.c2dm.permission.RECEIVE" />
    
        <permission android:name="com.example.gcmsampleapp.permission.C2D_MESSAGE"
            android:protectionLevel="signature" />
        <uses-permission android:name="com.example.gcmsampleapp.permission.C2D_MESSAGE" />
    
        <application
            android:allowBackup="true"
            android:icon="@mipmap/ic_launcher"
            android:label="@string/app_name"
            android:supportsRtl="true"
            android:theme="@style/AppTheme">
            <activity android:name=".MainActivity">
                <intent-filter>
                    <action android:name="android.intent.action.MAIN" />
    
                    <category android:name="android.intent.category.LAUNCHER" />
                </intent-filter>
            </activity>
    
            <receiver
                android:name="com.google.android.gms.gcm.GcmReceiver"
                android:exported="true"
                android:permission="com.google.android.c2dm.permission.SEND" >
                <intent-filter>
                    <action android:name="com.google.android.c2dm.intent.RECEIVE" />
                    <category android:name="com.example.gcmsampleapp" />
                </intent-filter>
            </receiver>
            <service
                android:name="com.example.gcmsampleapp.MyGcmListenerService"
                android:exported="false" >
                <intent-filter>
                    <action android:name="com.google.android.c2dm.intent.RECEIVE" />
                </intent-filter>
            </service>
            <service
                android:name="com.example.gcmsampleapp.RegistrationIntentService"
                android:exported="false">
            </service>
    
        </application>
    
    </manifest>
    ```

11. Run project to get **Registration Token** which will be printed out in the console.

Publishing Notification using CURL
----------------------------------
1. Create a file **notification.json** with the following content. Replace `"to":` value with your device **Registration Token**:

    ```json
    {
        "to": "ddW-zstyaWY:APA91bEcgwEq-PI8PgH3FWUZv-9K2wTNdgZ9PyZOJIOXaJRlmSPtCVyL1VL-N1kGIJRsXBK_sKL8x7vciOO5T8vTTlhPtyce1NSszkJf9hOizvpZ7X5fU2NClRuTE8QSUAvY1JL44uJa", 
        "data": {
            "message":"Test message from curl.", 
            "title":"GCMSampleApp"
        }
    }
    ```

2. Run the following CURL command to publish directly to GCM. Replace `<API KEY HERE>` with your **Server API Key**:

    ```bash
    curl https://gcm-http.googleapis.com/gcm/send -H "Authorization: key=<API KEY HERE>" -H "Content-Type: application/json" -d @notification.json
    ```
    
Publishing Notification using AWS SNS
-------------------------------------
Advantage of using SNS is scalability which is required when publishing tens of millions of notifications in a very short time and abstracts interaction with different push services behind a unified API.

1. Add a new platform application in SNS console -> Applications.
2. Enter **GCMSampleApp** for the name.
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
    "GCM": "{ \"data\": { \"message\": \"Test message from SNS console.\", \"title\": \"GCMSampleApp\" } }"
    }
    ```        
    