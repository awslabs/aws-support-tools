# SSM Agent Toolkit

The SSMAgent-Toolkit is a set of PowerShell scripts developed to run multiple checks to determined why an Windows EC2 instance does not come online. It will go through the following walkthrough

![Flowchart](https://github.com/awslabs/aws-support-tools/raw/master/Systems%20Manager/SSMAgent-Toolkit-Windows/SSMAgent-Toolkit_Flowchart.png?raw=1)

## Output

![Output](https://github.com/awslabs/aws-support-tools/raw/master/Systems%20Manager/SSMAgent-Toolkit-Windows/SSMAgent-Toolkit_Output.png?raw=1)

```powershell
PS C:\SSMAgent-Toolkit> Import-Module .\SSMAgent-Toolkit.psm1;Invoke-SSMChecks
[2020-12-28T19:51:40.9309935-05:00] [INFO] Log available at C:\SSMAgent-Toolkit\log\SSMCheck_2020-12-28-07-51-40.log
[2020-12-28T19:51:40.9330057-05:00] [INFO] Report available at C:\SSMAgent-Toolkit\report\SSMCheck_2020-12-28-07-51-40.txt
Running all the tests can take a few minutes...

    ___ _       _______    _____            __                         __  ___
   /   | |     / / ___/   / ___/__  _______/ /____  ____ ___  _____   /  |/  /___ _____  ____ _____ ____  _____
  / /| | | /| / /\__ \    \__ \/ / / / ___/ __/ _ \/ __ __ \/ ___/   / /|_/ / __  / __ \/ __  / __  / _ \/ ___/
 / ___ | |/ |/ /___/ /   ___/ / /_/ (__  ) /_/  __/ / / / / (__  )  / /  / / /_/ / / / / /_/ / /_/ /  __/ /
/_/  |_|__/|__//____/   /____/\__, /____/\__/\___/_/ /_/ /_/____/  /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/
                             /____/                                                         /____/

Check                                               Value                                                                   Note
-----                                               -----                                                                   ----
Windows sysprep image state complete                Pass                                                                    This is the desired state
Amazon SSM agent service running                    Pass                                                                    amazonssmagent service is in Running state. This is the desired state
Amazon SSM service account                          LocalSystem                                                             This is the recommended account to use
Managed(hybrid) Instance Registration               Skip                                                                    The instance is not configured as Managed(hybrid) Instance. Metadata will be used to get the InstanceId and Region
EC2 instance metadata accessible                    Pass                                                                    EC2 InstanceID = i-079fcdxxxxxxxxxxx, Region = us-east-1
IAM instance profile                                SSM-Role                                                                IAM instance profile SSM-Role is attached to the instance
IAM profile credential valid                        Pass                                                                    IAM instance profile's credential is up to date. IAM credential Expiration timestamp is 12/29/2020 01:27:39. The Last update is
                                                                                                                            12/28/2020 19:08:41 UTC
LocalSystem account user API assume role            arn:aws:sts::xxxxxxxxxxxx:assumed-role/SSM-Role/i-079fcdxxxxxxxxxxx     The role and the instance in the ARN should match the role in the metadata and the current instanceID
ssm.us-east-1.amazonaws.com accessible              Pass                                                                    Endpoint IP address is 52.46.145.233
ec2messages.us-east-1.amazonaws.com accessible      Pass                                                                    Endpoint IP address is 52.119.197.249
ssmmessages.us-east-1.amazonaws.com accessible      Pass                                                                    Endpoint IP address is 52.46.132.109
S3.us-east-1.amazonaws.com accessible               Pass                                                                    Endpoint IP address is 52.216.112.125
kms.us-east-1.amazonaws.com accessible              Pass                                                                    Endpoint IP address is 52.46.136.89
logs.us-east-1.amazonaws.com accessible             Pass                                                                    Endpoint IP address is 52.46.142.58
SSM Agent Proxy Setting                             N/A                                                                     There is no proxy setting for SSM Agent
System-wide environment variable proxy              N/A                                                                     There is no http_proxy, https_proxy or no_proxy configured for System-wide environment variable proxy.
LocalSystem account user environment variable proxy N/A                                                                     There is no http_proxy, https_proxy or no_proxy configured for LocalSystem account user environment variable proxy.
WinHTTP system-wide proxy                            Current WinHTTP proxy settings:      Direct access (no proxy server).  This is the output of - netsh winhttp show proxy:  Current WinHTTP proxy settings:      Direct access (no proxy server).
LocalSystem account user Internet Explorer proxy    N/A                                                                     If the instance behind a proxy and PowerShell via run command has a command which needs access to the internet would fail if
                                                                                                                            there are no Internet Explorer proxy settings
```

## Usage

Simply download the ZIP file included in this package and extract. Run one of the followings as an administrator in PowerShell.

```powershell
Import-Module .\SSMAgent-Toolkit.psm1;Invoke-SSMChecks
Import-Module .\SSMAgent-Toolkit.psm1;Invoke-SSMChecks -GridView "False"
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
    Import-Module "$destination\SSMAgent-Toolkit\SSMAgent-Toolkit.psm1"; Invoke-SSMChecks -GridView "False"
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
