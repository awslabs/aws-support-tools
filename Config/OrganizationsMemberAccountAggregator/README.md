# AWS Config Service Organization-Wide Member Account Config Aggregator 

AWS Config Service offers an option that integrates with AWS Organizations that have All Features Enabled to automatically create a Configuration Aggregator in your Organizations Master Account that aggregates all of your Member Accounts in all supported AWS Regions. This aggregator can only be created in the Master Account of the Organization.

The purpose of this script is to create a Config Aggregator in an Organizations Member Account that Aggregates all of your Organization's Member Accounts across all supported Regions. Normally this requires Creating an Aggregator in one of your Member Account and inviting all of the Accounts in your Organization. This would then require signing in to each Member Account in your Organization and adding an Authorization for the Aggregator Account. This script automates that process by assuming the Organizations Access Roles of each of your Member Accounts to create the Config Aggregator and to Authorize the Aggregator in the Master Account as well as all of the Member Accounts.

Note: You must run this script in an Organizations Master Account with all Features Enabled.

Each Member Account must have an OrganizationAccountAccessRole who's name matches the string provided to the variable orgs_access_role_name in the script. The OrganizationAccountAccessRoles must have the proper IAM permissions to perform all Config API calls contained in the script. The credentials used to run the script in the Organizations Master Account must have IAM permissions to List Accounts in Organizations as well as perform the requisite Config Service API calls.
