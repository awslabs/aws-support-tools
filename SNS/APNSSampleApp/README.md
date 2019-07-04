IOS Push Notification Steps
===========================
Simple IOS APNs Test project with SNS integration.

Create IOS Project
-------------------
1. Create a new project in XCode.
    1. Choose **Single View Application**.
    2. Enter **APNSSampleApp** for **Product Name**.
    3. Enter **com.example** for **Organization Identifier**.
    4. Leave **Language** to **Objective-C**.
2. Replace **AppDelegate.m** file content with the following:

    ```objectivec
     
    //
    //  AppDelegate.m
    //  APNSSampleApp
    //
    //
    
    #import "AppDelegate.h"
    
    @interface AppDelegate ()
    
    @end
    
    @implementation AppDelegate
    
    
    - (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
        // Override point for customization after application launch.
        
        // Register for push rotifications
        if ([[[UIDevice currentDevice] systemVersion] floatValue] >= 8.0) {
            [[UIApplication sharedApplication] registerUserNotificationSettings:[UIUserNotificationSettings settingsForTypes:(UIUserNotificationTypeSound | UIUserNotificationTypeAlert | UIUserNotificationTypeBadge) categories:nil]];
            [[UIApplication sharedApplication] registerForRemoteNotifications];
        } else {
            [[UIApplication sharedApplication] registerForRemoteNotificationTypes:
             (UIUserNotificationTypeBadge | UIUserNotificationTypeSound | UIUserNotificationTypeAlert)];
        }
        
        return YES;
    }
    
    - (void)application:(UIApplication *)application didRegisterForRemoteNotificationsWithDeviceToken:(NSData *)deviceToken {
        NSString * deviceTokenString = [[[[deviceToken description]
                                          stringByReplacingOccurrencesOfString: @"<" withString: @""]
                                         stringByReplacingOccurrencesOfString: @">" withString: @""]
                                        stringByReplacingOccurrencesOfString: @" " withString: @""];
        NSLog(@"Successfully registered for push notifications.");
        NSLog(@"Device token: %@", deviceTokenString);
    }
    
    - (void)application:(UIApplication *)application didFailToRegisterForRemoteNotificationsWithError:(NSError *)error {
        NSLog(@"Failed to register for push notifications.");
        NSLog(@"%@, %@", error, error.localizedDescription);
    }
    
    -(void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo {
        application.applicationIconBadgeNumber = 0;
        
        if (application.applicationState == UIApplicationStateActive) {
            NSString *title = [[userInfo objectForKey:@"aps"] objectForKey:@"title"];
            NSString *alert = [[userInfo objectForKey:@"aps"] objectForKey:@"alert"];
            UIAlertView *alertView = [[UIAlertView alloc] initWithTitle:title message:alert delegate:self cancelButtonTitle:@"OK" otherButtonTitles:nil];
            
            [alertView show];
        }    
    }
    
    - (void)applicationWillResignActive:(UIApplication *)application {
        
    }
    
    - (void)applicationDidEnterBackground:(UIApplication *)application {
        
    }
    
    - (void)applicationWillEnterForeground:(UIApplication *)application {
        
    }
    
    - (void)applicationDidBecomeActive:(UIApplication *)application {
        
    }
    
    - (void)applicationWillTerminate:(UIApplication *)application {
        
    }
    
    @end
    ```
    
Register App Id in iTunes Connect
---------------------------------
1. Open iTunes Connect by visiting [here](https://developer.apple.com/account/ios/identifiers/bundle/bundleList.action).
2. Add a new App ID:
    1. Name: **APNSSampleApp**.
    2. Bundle ID: **com.example.APNSSampleApp**.
    3. Enable Services: **Push Notifications**.
    4. Continue -> Submit -> Done.
3. Click newly added App Id **APNSSampleApp**.
4. Click **Edit**.
5. For **Push Notifications** under **Development SSL Certificate** click **Create Certificate**.
6. Click **Continue** to get to **Upload CSR** page.
7. Generate a new CSR using Keychain:
    1. Open **Keychain Access**.
    2. From **Keychain Access** menu -> **Certificate Assistant** sub menu click **Request a Certificate From a Certificate Authority...**
    3. Enter your email address, **APNSSampleApp Development** in the Common Name field.
    4. Select **Saved to disk** option.
    5. Click **Continue** and **Save**.
8. Back in upload CSR page in iTunes Connect click **Choose file**, select the saved CSR and upload.
9. Click **Generate** button.
10. After certificate is generated click **Download** button to download.
11. Save it as **APNSSampleAppDevelopment.cer**.
12. Double click **APNSSampleAppDevelopment.cer** to add to Keychain.
13. Right click the added certificate in Keychain and click **Export**.
14. Save as **APNSSampleAppDevelopment.p12**.
15. **DO NOT ENTER A PASSWORD** when prompted to secure the exported certificate.
16. Back in iTunes Connect under **Provisioning Profiles** click **Development**.
17. Add a new Provisioning profile to allow the app installed on your development device:
    1. Under Development choose **iOS App Development**.
    2. Click **Continue**.
    3. Select **APNSSampleApp** from **App ID** drop down menu and click **Continue**.
    4. Select your certificate and click **Continue**.
    5. Select your device from the list and click **Continue**.
    6. Enter **APNSSampleApp** in the **Profile Name:** field.
    7. Click **Generate** and **Download**.
    8. Open the downloaded provisioning profile to add to xCode.
    9. Open project setting tab General in Xcode, deselecte **Automatically manage signing** if it is selected
    10. Select the provisioning profile added in step 8 for **Signing (Debug)**
18. In xCode click on Project name **APNSSampleApp** then click **Capabilities** tab.
19. Switch **On** Push Notifications.

Get device Token
----------------
1. Run the app in xCode and select your device as the target to run on.
2. Tap OK to allow push notifications as the application starts. Notifications can also be turned On from device settings -> notifications.
3. As the application starts it will register with Apple and will log device token in xCode console which we will need for sending notification to the device.

Publishing Notification using AWS SNS
-------------------------------------
Advantage of using SNS is scalability which is required when publishing tens of millions of notifications in a very short time and abstracts interaction with different push services behind a unified API.

1. Create a new platform application in SNS console -> **Side Menu - Mobile - Push notifications**.
2. Enter **APNSSampleApp** for the name.
3. Select **Apple iOS/VoIP/Mac** from the **Push notification platform** drop down menu.
4. Select **Used for development in sandbox** as the generated certificate is for development
5. Select **iOS push certificate** from the **Push certificate type** drop down menu.
6. Click **Choose file** button.
7. Select **APNSSampleAppDevelopment.p12** file that we exported from Keychain.
8. Click **Load Credentials from File** to populate **Certificate** and **Private Key** boxes.
9. Click **Create platform application** button.
10. Click on the new application name to enter.
11. Click **Create application endpoint** button.
12. Paste your **Device Token** in the **Device token** field.
13. Enter optional data in **User Data** field.
14. Click **Create application endpoint** button.
15. Select the newly added endpoint from the list.
16. Click **Publish message** button.
17. Enter the following in the **Message body to send to the endpoint** box and click **Publish message** button.

    ```json
    {
    "APNS_SANDBOX":"{\"aps\":{\"alert\":\"Test message from SNS console.\", \"title\": \"APNSSampleApp\"}}"
    }
    ```        
    
