# MGN toolkit

The **MGN-Toolkit** is a set of PowerShell scripts developed to run multiple checks for common MGN related tasks to help migrating to AWS.

## Sample Output

```powershell
PS C:\Users\Administrator\desktop\MGN-toolkit\Windows> Import-Module .\MGN-Toolkit.psd1;invoke-mgntoolkit -SpeedTestIP 107.22.91.96 -WriteOpsTimer 30
Checking prerequisites before executing the MGN Toolkit...
[2023-10-26T08:56:34.2798000-04:00] [INFO] Code is running as administrator...
[2023-10-26T08:56:34.2954000-04:00] [INFO] Server Version 6.1.7601 is compatible with this module...
[2023-10-26T08:56:34.3110000-04:00] [INFO] The PowerShell Version 3 is compatible with this module - Executing script
[2023-10-26T08:56:34.3110000-04:00] [INFO] Creating logs directory - C:\Users\Administrator\desktop\MGN-toolkit\Windows\logs\
[2023-10-26T08:56:34.3266000-04:00] [INFO] Logs available at C:\Users\Administrator\desktop\MGN-toolkit\Windows\logs\MGNToolkit_2023-10-26T08-56-34.log
[2023-10-26T08:56:34.3422000-04:00] [INFO] Outputs available at C:\Users\Administrator\desktop\MGN-toolkit\Windows\Outputs\MGNToolkit_2023-10-26T08-56-34.txt
Running all the tests can take a few minutes...
    __  ___ ______ _   __   ______               __ __    _  __
   /  |/  // ____// | / /  /_  __/____   ____   / // /__ (_)/ /_
  / /|_/ // / __ /  |/ /    / /  / __ \ / __ \ / // //_// // __/
 / /  / // /_/ // /|  /    / /  / /_/ // /_/ // // ,<  / // /_
/_/  /_/ \____//_/ |_/    /_/   \____/ \____//_//_/|_|/_/ \__/
Please follow the following documentation to create the Speed Test instance before proceeding with the Bandwidth Test: https://docs.aws.amazon.com/mgn/latest/ug/Replication-Related-FAQ.html#perform-connectivity-bandwidth-test

Check                         Value         Action
-----                         -----         ------
AD Domain Controller          [GREEN]         No action required. The Active directory role can not be found.
Antivirus                     [GREEN]         No action required. No antivirus can be found or enabled.
BitLocker                     [GREEN]         No action required. BitLocker is not available on this system.
Boot Mode                     [YELLOW]        The Boot Disk is Basic, and the Boot Mode is Legacy BIOS. Select the Legacy BIOS option for Boot Mode during Target Launch - https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ami-boot.html
Root Disk Free Space          [GREEN]         No action required. There is 102.278 GB free space on C drive.
Authentication method         [YELLOW]        This host is not part of a domain. If the current user is part of the Administrators group, you can use it to RDP to server after migration.
.NET Framework Version        [GREEN]         No action required. .NET Framework 4.8.03761 is installed
Free RAM                      [GREEN]         No action required. The system has 2166 MB of RAM free RAM
Trusted Root Certificates     [RED]           Please ensure the Certificates which are showing a status of 'False' are installed by following our documentation here - https://docs.aws.amazon.com/mgn/latest/ug/Troubleshooting-Agent-Issues.html#error-certificate-verify-failed
SC.exe and NET.exe            [GREEN]         No action required. Both sc.exe (service control executable) and net.exe (net command executable) exist in C:\Windows\System32.
WMI Service Status            [GREEN]         No action required. WMI Service is running.
Proxy Settings                [GREEN]         No action required. There is no Proxy settings configured can be found.
Endpoints Connectivity        [GREEN]         No action required. All endpoints are reachable.
Upload Bandwidth              [YELLOW]        The Bandwidth Upload speed was Upload rate:515.00 Mbps. Compare this Bandwidth result with the results from the Check-DiskActivity cmdlet during a time of high disk activity to ensure the bandwidth is sufficient.
Disk Write Activity Average   [YELLOW]        The average for Disk Write Activity was 0.1848 Mbps. Compare this result with the Upload results from the Check-Bandwidth function to ensure it is sufficient.
Disk Write Activity Maximum   [YELLOW]        The Max for Disk Write Activity was 1.1241 Mbps. Ensure your Staging Area disk settings will be sufficient if there are frequent maximum spikes of this value, to avoid Replication Backlog

```
### Prerequisites

* PowerShell 3.0 or above
* Local Administrator account
* Microsoft Windows Server 2008R2 and above

## Usage

### Manual

1. Clone the repo.
2. Depending on the use-case, run the one of the following as an Administrator in PowerShell.

    #### Run all checks
    ##### Switches
    - `Region` : `Optional`. Used to specify the desired region. By default the module will run in `us-east-1`.
    - `SpeedTestIP` : `Optional`. The Ipaddress of the [speed test server](https://docs.aws.amazon.com/mgn/latest/ug/Replication-Related-FAQ.html#perform-connectivity-bandwidth-test). By default `Get-Bandwidth` is not invoked.
    - `WriteOpsTimer` : `Optional`. The number of seconds to calculate IOPS. By default `WriteOpsTimer` is 20 seconds.
    - `MgnVpceId`: `Optional`. If you are using a VPC Endpoint for MGN, you can specify the Endpoint ID + Suffix for the Endpoint connectivity test. Please enter the VPC Endpoint Id and suffix from the DNS names.
    - `S3VpceId`: `Optional`. If you are using a VPC Endpoint for S3, you can specify the Endpoint ID + Suffix for the Endpoint connectivity test. Please enter the VPC Endpoint Id and suffix from the DNS names.
    - `List`: `Optional`. The output will be generated using the [Format-List](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/format-list?view=powershell-7.3) method. By default the module will use [Format-Table](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/format-table?view=powershell-7.3).
    - `GridView` : `Optional`. The output will be generated using the [Out-GridView](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/out-gridview?view=powershell-7.3) method. By default the module will use [Format-Table](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/format-table?view=powershell-7.3).

    ##### Examples with switches added
    ```powershell
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -region <region>
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -region <region> -MgnVpceId <vpce-id>-<suffix> -S3VpceId <vpce-id>-<suffix>
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -region <region> -SpeedTestIP <IP-Address> -List
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -region <region> -WriteOpsTimer <Seconds> -GridView
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -region <region> -SpeedTestIP <IP-Address> -WriteOpsTimer <Seconds>

    ```

    ##### All checks in `us-east-2` region
    ```powershell
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -SpeedTestIP 1.1.1.1 -WriteOpsTimer 20 -region us-east-2
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -SpeedTestIP 1.1.1.1 -WriteOpsTimer 20 -region us-east-2 -List
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -SpeedTestIP 1.1.1.1 -WriteOpsTimer 20 -region us-east-2 -GridView
    Import-Module .\MGN-Toolkit.psm1;Invoke-MGNToolkit -SpeedTestIP 1.1.1.1 -WriteOpsTimer 20 -region us-east-2 -MgnVpceId vpce-12345678910111213-abcd1234 -S3VpceId vpce-12345678910111213-abcd1234
    ```


    #### Run specific check
    To learn more about each check please reference the [check table](https://gitlab.aws.dev/aaalzand/mgn-toolkit/-/blob/main/Windows/README.md?ref_type=heads#checks) below.

    ##### AD Domain Controller or Authentication method
    ```powershell
    Import-Module .\MGN-Toolkit.psm1
    $Output = New-Object -TypeName "System.Collections.ArrayList"
    $productType = (Get-CimInstance -ClassName Win32_OperatingSystem).ProductType
    Get-DomainControllerStatus -product $productType
    $Output | ForEach { [PSCustomObject]$_ } | Format-Table -Wrap
    ```
    ##### Upload Bandwidth
    ```powershell
    Import-Module .\MGN-Toolkit.psm1
    $Output = New-Object -TypeName "System.Collections.ArrayList"
    Get-Bandwidth -SpeedTestIP 1.1.1.1
    $Output | ForEach { [PSCustomObject]$_ } | Format-Table -Wrap
    ```
    ##### Disk Write Activity Average and Maximum
    ```powershell
    Import-Module .\MGN-Toolkit.psm1
    $Output = New-Object -TypeName "System.Collections.ArrayList"
    Get-DiskActivity -Seconds 30
    $Output | ForEach { [PSCustomObject]$_ } | Format-Table -Wrap
    ```
    ##### Test endpoints reachability
    ```powershell
    Import-Module .\MGN-Toolkit.psm1
    $Output = New-Object -TypeName "System.Collections.ArrayList"
    $Region = "us-east-1"
    $MgnVpceId = ""
    $S3VpceId = ""
    (Test-EndpointsNetworkAccess -region $Region -mgnVpceId $MgnVpceId -s3VpceId $S3VpceId) | Out-Null
    $Output | ForEach { [PSCustomObject]$_ } | Format-Table -Wrap
    ```
    ##### For all other functions use the method below with the appropriate [function name](www.google.com)
    ```powershell
    Import-Module .\MGN-Toolkit.psm1
    $Output = New-Object -TypeName "System.Collections.ArrayList"
    <function name>
    $Output | ForEach { [PSCustomObject]$_ } | Format-Table -Wrap
    ```

### Download, Extract, and Execute the Toolkit

1. Run the following sample code as an Administrator in PowerShell to download the ZIP file included in this package, extract and execute the toolkit.
    - Adjust the last line as needed with the desired parameters mentioned [here](https://gitlab.aws.dev/aaalzand/mgn-toolkit/-/blob/main/Windows/README.md?ref_type=heads#examples-with-switches-added)

    ```powershell
    #MGN-Toolkit
    $uri = 'TBD'
    $destination = (Get-Location).Path
    if ((Test-Path -Path "$destination\MGN-Toolkit.zip" -PathType Leaf) -or (Test-Path -Path "$destination\MGN-Toolkit")) {
        write-host "File $destination\MGN-Toolkit.zip or folder $destination\MGN-Toolkit found, exiting"
    }
    else {
        Write-host "Enable TLS 1.2 for this PowerShell session only."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $webClient = New-Object System.Net.WebClient
        Write-host "Downloading MGN-Toolkit.zip"
        $webClient.DownloadFile($uri, "$destination\MGN-Toolkit.zip")
        Write-host "MGN-Toolkit.zip download successfully"
        [System.IO.Compression.ZipFile]::ExtractToDirectory("$destination\MGN-Toolkit.zip","$destination\MGN-Toolkit")
        Write-host "Extracting MGN-Toolkit.zip complete successfully"
        Import-Module "$destination\MGN-Toolkit\WindowsMigration-Toolkit.psm1"; Invoke-MGNToolkit
    }
    ```


## Checks
| Check | Description | Function name | Input Parameter
| --- | --- | --- | --- |
| AD Domain Controller | Check if the [AD-Domain-Services](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview) role is installed and if the host is a Domain Controller. [Domain controller considerations](https://docs.aws.amazon.com/mgn/latest/ug/General-Questions-FAQ.html#What-Active-Directory). | Get-DomainControllerStatus | ProductType
| Antivirus | Check if an Anti-Virus software is installed. This check will recommend allow listing MGN specific directories. When migrating with MGN, we install software and make changes so the machine can run natively on AWS, which Anti-Virus software can sometimes block. [64-bit - C:\Program Files(x86)\AWS Replication Agent] [32-bit - C:\Program Files\AWS Replication Agent]. **Please note, due to all the possible third-party software, this may not be able to detect ALL Antivirus's**. | Check-AntivirusEnabled | NA
| BitLocker | Check if BitLocker is enabled. [BitLocker is not supported](https://docs.aws.amazon.com/mgn/latest/ug/FAQ.html#does-mgn-bitlocker) when using MGN. | Get-BitLockerStatus | NA
| Boot Mode | Checks if the root disk is Dynamic/Basic and GPT/MBR to ensure you pick [the necessary Boot Mode](https://docs.aws.amazon.com/mgn/latest/ug/boot-mode.html) based on the results. | Get-BootMode | NA
|Root Disk Free Space  | Check if there is at least 2GB of free space on the root volume. The space will be used for driver installation and other AWS software (EC2launch, SSMAgent, etc.) during migration | Get-RootDiskSpace | NA
| Authentication method | Check whether the host is part of a domain or not. The check will help with determined the authentication method needed post migration | Get-Authenticationmethod | ProductType
| .NET Framework Versions | Checks what the .NET Framework Version is to ensure the required version is installed for the AWS Replication Agent installation | Get-DotNetFrameworkVersion | NA
| Free RAM | Checks to ensure there is at least [300 MB of free RAM to run the AWS Replication Agent](https://docs.aws.amazon.com/mgn/latest/ug/installation-requirements.html#general-requirements2)  | Get-FreeRAM | NA
| Trusted Root Certificates | Check whether Amazon + Starfield certificates are installed in the Trusted Root Certificate store. The certificates are required for the [AWS Replication Agent installation](https://docs.aws.amazon.com/mgn/latest/ug/Troubleshooting-Agent-Issues.html#error-certificate-verify-failed) | Get-TrustedRootCertificate | NA
| sc.exe and net.exe check | Checks to make sure sc.exe and net.exe are in the C:\Windows\System32 directory for [AWS Replication Agent installation](https://docs.aws.amazon.com/mgn/latest/ug/Troubleshooting-Agent-Issues.html#Installation-Failed-Windows) | Get-SCandNET| NA
| WMI Service | Checks to make sure the WMI Service is in a running state, as this is required for AWS Replication Agent installation | Get-WMIServiceStatus | NA
| Proxy | Checks to see if there is any type of proxy installed([IE](https://docs.microsoft.com/en-us/troubleshoot/windows-server/identity/security-identifiers-in-windows), [LocalSystem account user environment variable](https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables), [System-wide environment variable](https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables), [WinHTTP system-wide](https://learn.microsoft.com/en-us/windows/win32/winhttp/winhttp-start-page)). The AWS Replication Agent requires [TCP Port 443 communication to AWS Endpoints](https://docs.aws.amazon.com/mgn/latest/ug/Network-Requirements.html#Source-Manager-TCP-443) | Get-ProxySetting | NA
| Test Endpoint Connectivity | Checks TCP Port 443 access to the necessary Endpoints for [AWS Replication Agent installation](https://docs.aws.amazon.com/mgn/latest/ug/Network-Requirements.html) | Test-EndpointsNetworkAccess | NA
| Bandwidth Upload Speed | Check the upload speed to from the Source Server to the AWS Staging Area subnet. Low speeds may cause slow replication performance. For bandwidth test follow the [documentation](https://docs.aws.amazon.com/mgn/latest/ug/Replication-Related-FAQ.html#perform-connectivity-bandwidth-test).| Get-Bandwidth | -SpeedTestIP <IP-Address>
| Disk Write Activity Average and Maximum | Checks what the Average and Maximum Disk Write/s is. This result compared with the Bandwidth Upload Speed check can help determine if there is sufficient bandwidth speeds to replicate data based on the source server data change rate  | Get-DiskActivity | -WriteOpsTimer <Seconds>



## Values
| Value | Description |
| --- | --- |
|GREEN| The check found no issues. |
|YELLOW| The check found some items that should be reviewed and taken into consideration when performing a migration. |
|RED| The check found issues that will block the migration. Please follow the recommendations provided to resolve any issues. |


## Troubleshooting
| Log Location | Description |
| --- | --- |
| %MGN-Toolkit%\Windows\logs | The log file will contain the outputs from each function and highlight any errors when it was executed. You can use this log to investigate any issues during the execution of each function. |


## Built With

PowerShell 3.0

## Authors

* Ali Alzand
* Tim Hall
* Imthian Ramgobin
