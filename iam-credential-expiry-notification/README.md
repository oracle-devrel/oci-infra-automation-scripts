# Create Expiry Email Notification of OCI IAM Credentials

## Introduction
This is a automation solution to receive early email notification for expiry IAM credentials.

## Architecture

![solution architecture](<Secret expiry notification-1.drawio.png>)

## Build and Deploy Function
### Prerequisites
#### Dynamic Group

  ```
  # Replace OCID for function compartment
  All {resource.type = 'fnfunc', resource.compartment.id = '<function-compartment>'}
  
  Example:
  All {resource.type = 'fnfunc', resource.compartment.id = 'ocid1.compartment.oc1..aaaaaaaanovmfmmnonjjyxeq4jyghszj2eczlrkgj5svnxrt...'}
  ```

#### Policies

  ```
  # Replace dynamic-group-name, function-compartment and OCID of vault secret for OCI function

  Allow dynamic-group <dynamic-group-name> to read secret-family in compartment <function-compartment> where target.secret.id='<ocid of smtp password vaultsecret>'
  Allow dynamic-group <dynamic-group-name> to inspect compartments in tenancy
  ```

### Configure approved sender in email delivery
An approved sender must be set up for all “From:” addresses sending mail through OCI.

1. Open the navigation menu of OCI Console and click Developer Services.
2. Under Application Integration, click Email Delivery.
3. Under Email Delivery, click Approved Senders.
4. Click Create Approved Sender and enter the email address that you want to list as an approved sender.

    > Note: If your OCI email delivery SMTP connection endpoint is smtp.email.ap-mumbai-1.oci.oraclecloud.com then add noreply@notification to region and enter in approved sender email address. For example, noreply@notification.ap-mumbai-1.oci.oraclecloud.com.

5. Click Add to add email address to your Approved Senders list.

### Create secret in OCI vault
1. Open the navigation menu, click Identity & Security, and then click Vault.
2. Under List scope, select a compartment that contains the vault.
    > Note: If you need to create a new vault and master encryption key, follow the instructions in Create Vault and Master Encryption Key.

3. Under Resources, click Create Secret and select appropriate master encryption key.
4. Enter smptppass in name field and description SMTP password for OCI email delivery authentication.
5. Select the format plain-text for Secret Type Template and enter smtp password, for contents of the secret.
    > Note: Please store SMTP password to OCI vault.

### Create and deploy OCI function
1. On **OCI console**, click **Cloud Shell** in the top navigation.
2. Create **function** using Fn project CLI from cloud shell.
```
fn init --runtime python <function-name>

Example: fn init --runtime python expiry-notification-func
Change directory to the newly created directory.
```
3. Create **app** to deploy the function.
```
# Specify the OCID of subnet

fn create app expiry-notification-app --annotation oracle.com/oci/subnetIds='["<subnet OCID>"]'

Example:  fn create app expiry-notification-app --annotation oracle.com/oci/subnetIds='["ocid1.subnet.oc1.ap-mumbai-1.aaaaaaaabitp32dkyox37qa3tk3evl2nxivwb....."]'
```
4. Copy and paste content of **func.py** from this repo and overwriting the existing content.
5. You could replace **companylogo.png** with your company logo and update HTML text as email body in script. Default is Oracle logo.
6. Update config parameters in **func.yaml** file.
7. Run below command to **deploy the function**.
```
fn -v deploy --app <app-name>

Example: fn -v deploy --app expiry-notification-app
```
## Create Schedule in Resource Scheduler
1. Open the navigation menu and click Governance & Administration.
2. Under Resource Scheduler, click Schedules.
3. Under Create a Schedule, click Create a Schedule. The Create a schedule dialog box opens.
4. Fill up schedule name, schedule description and action to be executed as start under basic information and click Next.
5. Under resources select your function compartment and function and click Next. 
6. Under schedule select Daily and configure other parameters as per your requirement.
7. In the Repeat every field, enter how often you would like the schedule to run or use the menu to select an interval. The minimum value is 1. The maximum value is 99.
8. In the Start Time field, enter the time in hours and minutes in 24-hour format.
9. Click Next to go to the Review and Create Schedule.

 You will now receive expiry email notification for IAM credential.

## License
Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK.