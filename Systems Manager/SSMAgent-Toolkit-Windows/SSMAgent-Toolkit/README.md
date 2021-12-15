# Note: Starting with [SSM Agent version 3.1.501.0](https://github.com/aws/amazon-ssm-agent/releases/tag/3.1.501.0). This solution is part of the [ssm-cli](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-cli.html) a subset tool of the SSM Agent.
# SSM Agent Toolkit for Windows

The [SSMAgent-Toolkit for Windows](https://github.com/awslabs/aws-support-tools/tree/master/Systems%20Manager/SSMAgent-Toolkit-Windows) is a set of PowerShell scripts developed to run multiple checks to determined why an Windows EC2 instance does not come online. It will go through the following workflow

![Flowchart](https://github.com/awslabs/aws-support-tools/raw/master/Systems%20Manager/SSMAgent-Toolkit-Windows/SSMAgent-Toolkit_Flowchart.png?raw=1)

## Output

### The instance/server register as a hybrid instance

![Output](https://github.com/awslabs/aws-support-tools/raw/master/Systems%20Manager/SSMAgent-Toolkit-Windows/SSMAgent-Toolkit_HybridOutput.png?raw=1)


```powershell
PS C:\SSMAgent-Toolkit> Import-Module "$destination\SSMAgent-Toolkit\SSMAgent-Toolkit.psm1";Invoke-SSMChecks -Table
Checking for elevated permissions...
Code is running as administrator - executing the script...
[2021-12-09T20:26:38.5340080+00:00] [INFO] Logs directory exists - C:\SSMAgent-Toolkit\logs\
[2021-12-09T20:26:38.5340080+00:00] [INFO] Outputs directory exists - C:\SSMAgent-Toolkit\Outputs\
[2021-12-09T20:26:38.5497378+00:00] [INFO] Logs available at C:\SSMAgent-Toolkit\logs\SSMCheck_2021-12-09-08-26-38.log
[2021-12-09T20:26:38.5497378+00:00] [INFO] Outputs available at C:\SSMAgent-Toolkit\Outputs\SSMCheck_2021-12-09-08-26-38.txt
Running all the tests can take a few minutes...
    ___ _       _______    _____            __                         __  ___
   /   | |     / / ___/   / ___/__  _______/ /____  ____ ___  _____   /  |/  /___ _____  ____ _____ ____  _____
  / /| | | /| / /\__ \    \__ \/ / / / ___/ __/ _ \/ __ __ \/ ___/   / /|_/ / __  / __ \/ __  / __  / _ \/ ___/
 / ___ | |/ |/ /___/ /   ___/ / /_/ (__  ) /_/  __/ / / / / (__  )  / /  / / /_/ / / / / /_/ / /_/ /  __/ /
/_/  |_|__/|__//____/   /____/\__, /____/\__/\___/_/ /_/ /_/____/  /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/
                             /____/                                                         /____/

Check                                               Value                                                                                                  Note
-----                                               -----                                                                                                  ----
Windows sysprep image state complete                Pass                                                                                                   Image state is IMAGE_STATE_COMPLETE. This is the desired state
Amazon SSM agent service running                    Pass                                                                                                   amazonssmagent service is in Running state. This is the desired state
Amazon SSM service account                          LocalSystem                                                                                            This is the recommended account to use
Amazon SSM service startup mode                     Auto                                                                                                   This is the recommended startup mode to use
Managed(hybrid) Instance Registration               Pass                                                                                                   ManagedInstanceID = mi-abcdef01234567890, Region = us-east-1
EC2 instance metadata accessible                    Skip                                                                                                   This test skipped since this server configured as Managed(hybrid) Instance
IAM instance profile                                Skip                                                                                                   This test skipped since this server configured as Managed(hybrid) Instance
IAM profile credential valid                        Skip                                                                                                   This test skipped since this server configured as Managed(hybrid) Instance
LocalSystem account user API assume role            arn:aws:sts::012345678901:assumed-role/AmazonEC2RunCommandRoleForManagedInstances/mi-abcdef01234567890 The role and the instance in the ARN should match the metadata\hybrid registration
ssm.us-east-1.amazonaws.com accessible              Pass                                                                                                   Endpoint IP address is 52.46.141.158
ec2messages.us-east-1.amazonaws.com accessible      Pass                                                                                                   Endpoint IP address is 52.94.228.178
ssmmessages.us-east-1.amazonaws.com accessible      Pass                                                                                                   Endpoint IP address is 52.46.132.109
S3.us-east-1.amazonaws.com accessible               Pass                                                                                                   Endpoint IP address is 52.217.165.48
kms.us-east-1.amazonaws.com accessible              Pass                                                                                                   Endpoint IP address is 52.46.134.194
logs.us-east-1.amazonaws.com accessible             Pass                                                                                                   Endpoint IP address is 3.236.94.199
monitoring.us-east-1.amazonaws.com accessible       Pass                                                                                                   Endpoint IP address is 72.21.206.194
SSM Agent Proxy Setting                             N/A                                                                                                    There is no proxy setting for SSM Agent
System-wide environment variable proxy              N/A                                                                                                    There is no http_proxy, https_proxy or no_proxy configured
LocalSystem account user environment variable proxy N/A                                                                                                    There is no http_proxy, https_proxy or no_proxy configured
WinHTTP system-wide proxy                           N/A                                                                                                    There is no ProxyServer(s) configured for WinHTTP system-wide proxy
LocalSystem account user Internet Explorer proxy    N/A                                                                                                    There is no ProxyServer configured
SSMAgent version                                    Pass                                                                                                   The install and the latest agent version in us-east-1 is 3.1.501.0
Session Manager Plugin version                      Pass               															                           The install and the latest Session Manager Plugin version is 1.2.279.0
```

### The instance register as a EC2 instance

![Output](https://github.com/awslabs/aws-support-tools/raw/master/Systems%20Manager/SSMAgent-Toolkit-Windows/SSMAgent-Toolkit_EC2Output.png?raw=1)

```powershell
PS C:\SSMAgent-Toolkit> Import-Module "$destination\SSMAgent-Toolkit\SSMAgent-Toolkit.psm1";Invoke-SSMChecks -Table
Checking for elevated permissions...
Code is running as administrator - executing the script...
[2021-12-09T20:26:38.5340080+00:00] [INFO] Logs directory exists - C:\SSMAgent-Toolkit\logs\
[2021-12-09T20:26:38.5340080+00:00] [INFO] Outputs directory exists - C:\SSMAgent-Toolkit\Outputs\
[2021-12-09T20:26:38.5497378+00:00] [INFO] Logs available at C:\SSMAgent-Toolkit\logs\SSMCheck_2021-12-09-08-26-38.log
[2021-12-09T20:26:38.5497378+00:00] [INFO] Outputs available at C:\SSMAgent-Toolkit\Outputs\SSMCheck_2021-12-09-08-26-38.txt
Running all the tests can take a few minutes...
    ___ _       _______    _____            __                         __  ___
   /   | |     / / ___/   / ___/__  _______/ /____  ____ ___  _____   /  |/  /___ _____  ____ _____ ____  _____
  / /| | | /| / /\__ \    \__ \/ / / / ___/ __/ _ \/ __ __ \/ ___/   / /|_/ / __  / __ \/ __  / __  / _ \/ ___/
 / ___ | |/ |/ /___/ /   ___/ / /_/ (__  ) /_/  __/ / / / / (__  )  / /  / / /_/ / / / / /_/ / /_/ /  __/ /
/_/  |_|__/|__//____/   /____/\__, /____/\__/\___/_/ /_/ /_/____/  /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/
                             /____/                                                         /____/

Check                                               Value                                                                         Note
-----                                               -----                                                                         ----
Windows sysprep image state complete                Pass                                                                          Image state is IMAGE_STATE_COMPLETE. This is the desired state
Amazon SSM agent service running                    Pass                                                                          amazonssmagent service is in Running state. This is the desired state
Amazon SSM service account                          LocalSystem                                                                   This is the recommended account to use
Amazon SSM service startup mode                     Auto                                                                          This is the recommended startup mode to use
Managed(hybrid) Instance Registration               Skip                                                                          The instance is not configured as Managed(hybrid) Instance. Metadata will be used to get the InstanceId and Region
EC2 instance metadata accessible                    Pass                                                                          EC2 InstanceID = i-abcdef01234567890, Region = us-east-1
IAM instance profile                                SSMInstanceProfile                                                            IAM instance profile SSMInstanceProfile is attached to the instance
IAM profile credential valid                        Pass                                                                          IAM instance profile`'s credential is up to date. IAM credential Expiration timestamp is 10/01/2021 18:26:44.
                                                                                                                                  The Last update is 10/01/2021 12:17:17 UTC
LocalSystem account user API assume role            arn:aws:sts::012345678901:assumed-role/SSMInstanceProfile/i-abcdef01234567890 The role and the instance in the ARN should match the metadata\hybrid registration
ssm.us-east-1.amazonaws.com accessible              Pass                                                                          Endpoint IP address is 52.46.145.233
ec2messages.us-east-1.amazonaws.com accessible      Pass                                                                          Endpoint IP address is 52.46.138.63
ssmmessages.us-east-1.amazonaws.com accessible      Pass                                                                          Endpoint IP address is 52.46.132.109
S3.us-east-1.amazonaws.com accessible               Pass                                                                          Endpoint IP address is 52.217.98.142
kms.us-east-1.amazonaws.com accessible              Pass                                                                          Endpoint IP address is 52.46.136.89
logs.us-east-1.amazonaws.com accessible             Pass                                                                          Endpoint IP address is 3.236.94.131
monitoring.us-east-1.amazonaws.com accessible       Pass                                                                          Endpoint IP address is 72.21.206.194
SSM Agent Proxy Setting                             N/A                                                                           There is no proxy setting for SSM Agent
System-wide environment variable proxy              N/A                                                                           There is no http_proxy, https_proxy or no_proxy configured
LocalSystem account user environment variable proxy N/A                                                                           There is no http_proxy, https_proxy or no_proxy configured
WinHTTP system-wide proxy                           N/A                                                                           There is no ProxyServer(s) configured for WinHTTP system-wide proxy
LocalSystem account user Internet Explorer proxy    N/A                                                                           There is no ProxyServer configured
SSMAgent version                                    Pass                                                                          The install and the latest agent version in us-east-1 is 3.1.501.0
Session Manager Plugin version                      Pass               															  The install and the latest Session Manager Plugin version is 1.2.279.0
```

## Usage

Simply download the ZIP file included in this package and extract. Run the one of the followings as administrator in PowerShell.

```powershell
Import-Module .\SSMAgent-Toolkit.psm1;Invoke-SSMChecks
Import-Module .\SSMAgent-Toolkit.psm1;Invoke-SSMChecks -Table
Import-Module .\SSMAgent-Toolkit.psm1;Invoke-SSMChecks -GridView
```

Or run the following sample code as an administrator in PowerShel to download the ZIP file included in this package, extract and execute the toolkit. 

```powershell
#SSMAgent-Toolkit-Windows - https://github.com/awslabs/aws-support-tools/tree/master/Systems%20Manager/SSMAgent-Toolkit-Windows
$uri = 'https://github.com/awslabs/aws-support-tools/raw/master/Systems%20Manager/SSMAgent-Toolkit-Windows/SSMAgent-Toolkit.zip'
$destination = (Get-Location).Path
if ((Test-Path -Path "$destination\SSMAgent-Toolkit.zip" -PathType Leaf) -or (Test-Path -Path "$destination\SSMAgent-Toolkit")) { 
    write-host "File $destination\SSMAgent-Toolkit.zip or folder $destination\SSMAgent-Toolkit found, exiting" 
}
else {
    # Enable TLS 1.2 for this PowerShell session only.
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($uri, "$destination\SSMAgent-Toolkit.zip")
    Write-host "SSMAgent-Toolkit.zip"
    Expand-Archive -Path "$destination\SSMAgent-Toolkit.zip" -DestinationPath "$destination\SSMAgent-Toolkit"
    Write-host "Extracting SSMAgent-Toolkit.zip complete successfully"
    Import-Module "$destination\SSMAgent-Toolkit\SSMAgent-Toolkit.psm1"; Invoke-SSMChecks -Table
}
```

### Prerequisites

No Prerequisites is required

### Installing

No installation is required on Windows systems.

## Built With

PowerShell 5.1

## Authors

* Ali Alzand
* Thanks to Taka Matsumoto and Adam Creech for your contribution.