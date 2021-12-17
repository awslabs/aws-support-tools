<#
.SYNOPSIS
    Run checks needed for an instance to be online in SSM.
.DESCRIPTION
    This is tha main function to go through all checks needed for an EC2 instance to be online in SSM. Each check will be on a separate function. For more information visit - https://github.com/awslabs/aws-support-tools/tree/master/Systems%20Manager/SSMAgent-Toolkit-Windows
.EXAMPLE
    PS C:\> Invoke-SSMChecks
  	PS C:\> Invoke-SSMChecks -GridView
	PS C:\> Invoke-SSMChecks -Table
.INPUTS
	endpoints = default as endpoints for AWS Systems Manager
	GridView = Switch to have the output as gridview.
	GridView = Switch to have the output as table.
.OUTPUTS
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
#>


function Invoke-SSMChecks {
	param (
		# Endpoints for AWS Systems Manager https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-create-vpc.html#sysman-setting-up-vpc-create
		$endpoints = @(
			"ssm",
			"ec2messages",
			"ec2",
			"ssmmessages",
			"S3",
			"kms",
			"logs",
			"monitoring"
		),
		[Switch]$GridView,
		[Switch]$Table
	)
	
	#Set the default file path and logs location, all errors should function as STOP errors for logging purposes
	begin {
		Write-Host "Checking for elevated permissions..."
		if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
			Write-Warning "Insufficient permissions to run this script. Open the PowerShell console as an administrator and run this script again."
			Break
		}
		else {
			Write-Host "Code is running as administrator - executing the script..." -ForegroundColor Green
		}
		#Prefix for the file names
		$FileNamePrefix = "SSMCheck_"
		#Name the log and Outputs files based on the timestamp
		$TimeStamp = Get-Date -Format "yyyy-MM-dd-hh-mm-ss"
		#The directory of this function
		$SourceDirectory = $PSScriptRoot
		#The parent directory of the module
		$ParentDirectory = (get-item $SourceDirectory).parent.fullname
		#Logs directory
		$LogsDirectory = ("$ParentDirectory\logs\" -replace ("util\\", ""))
		#Create logs directory if it does not exist
		if (-not (Test-Path $LogsDirectory)) {
			Write-Log -Message "Creating logs directory - $LogsDirectory"
			New-item -Path $LogsDirectory -ItemType Directory | Out-Null
		}
		else {
			Write-Log -Message "Logs directory exists - $LogsDirectory"
		}
		#Logs file name
		$LogsDestination = $LogsDirectory + $FileNamePrefix + $TimeStamp + ".log"
		#Outputs directory
		$OutputsDirectory = ("$ParentDirectory\Outputs\" -replace ("util\\", ""))
		#Create the Outputs directory if it does not exist
		if (-not (Test-Path $OutputsDirectory)) {
			Write-Log -Message "Creating Outputs directory - $OutputsDirectory"
			New-item -Path $OutputsDirectory -ItemType Directory | Out-Null
		}
		else {
			Write-log -Message "Outputs directory exists - $OutputsDirectory"
		}
		#Outputs file name
		$OutputsDestination = $OutputsDirectory + $FileNamePrefix + $TimeStamp + ".txt"
		Write-Log -Message "Starting..." 6>> $LogsDestination
		New-Item -Path $ParentDirectory -Name "temp" -ItemType "directory" -Force | Out-Null
		Write-Log -Message "Logs available at $LogsDestination"
		Write-Log -Message "Outputs available at $OutputsDestination"
		Write-Host "Running all the tests can take a few minutes..." -BackgroundColor Yellow -ForegroundColor Black
		#Set the output object
		$Output = New-Object -TypeName "System.Collections.ArrayList"
	}

	process {

		Write-Host @"

    ___ _       _______    _____            __                         __  ___                                 
   /   | |     / / ___/   / ___/__  _______/ /____  ____ ___  _____   /  |/  /___ _____  ____ _____ ____  _____
  / /| | | /| / /\__ \    \__ \/ / / / ___/ __/ _ \/ __ `__ \/ ___/   / /|_/ / __  `/ __ \/ __  `/ __  `/ _ \/ ___/
 / ___ | |/ |/ /___/ /   ___/ / /_/ (__  ) /_/  __/ / / / / (__  )  / /  / / /_/ / / / / /_/ / /_/ /  __/ /    
/_/  |_|__/|__//____/   /____/\__, /____/\__/\___/_/ /_/ /_/____/  /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/     
                             /____/                                                         /____/             
"@
		
		# Calling each check in order
		$Output.Add((Get-WindowsImageState 6>> $LogsDestination)) | Out-Null
		$ServiceAvailability = Get-ServiceAvailability 6>> $LogsDestination
		# Make more checks if the amazonssmagent is available 
		if ($ServiceAvailability[0] -eq 1) {
			$Output.Add((Get-ServiceStatus -ServiceStatus $ServiceAvailability[1] 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-ServiceAccount 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-ServiceStartupMode 6>> $LogsDestination)) | Out-Null
		}
		else {
			$Output.Add($ServiceAvailability) | Out-Null
			$Output.Add((Get-ServiceAccount -Skip 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-ServiceStartupMode -Skip 6>> $LogsDestination)) | Out-Null
		}
		#Check if the instance have a registration file exit. If does, means the instance is configured as Managed(hybrid) instance and will skip the metadata check.
		
		$InstanceRegistrationResults = (Test-HybridRegistration 6>> $LogsDestination)
		$Output.Add(($InstanceRegistrationResults[0] 6>> $LogsDestination)) | Out-Null
		if (-not ([string]::IsNullOrEmpty($InstanceRegistrationResults[1]))) {
			$region = $InstanceRegistrationResults[2]
			$Output.Add((Get-MetadataAccess -ManagedInstance 6>> $LogsDestination)) | Out-Null
			$Output.Add((Test-IAMInstanceProfile -ManagedInstance 6>> $LogsDestination)) | Out-Null
			$Output.Add((Test-IAMInstanceProfileCredentialLastUpdate -ManagedInstance 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation $ParentDirectory 6>> $LogsDestination)) | Out-Null
		}
		else {
			# Retrieve Metadata token and Invoke web request reply code for meta data accessibility
			$MetadataInfo = (New-MetadataToken 6>> $LogsDestination)
			
			if (-not ([string]::IsNullOrEmpty($MetadataInfo[1]))) {
				#To check if there is an access to the metadata. Then check the InstanceID, region, IAM profile settings and get STSCallerIdentity under the LocalSystem, call all the checks that would need the access to the metadata
				Write-Log -Message "Metadata is reachable. Retrieve Instance ID and Region from the metadata" 6>> $LogsDestination
				$ec2instanceid = Get-InstanceID -Token $MetadataInfo[1] 6>> $LogsDestination
				$region = Get-Region -Token $MetadataInfo[1] 6>> $LogsDestination
				$Output.Add((Get-MetadataAccess -StatusCode $MetadataInfo[0] -Region $region -EC2InstanceID $ec2instanceid 6>> $LogsDestination)) | Out-Null
				$IAMinstanceprofile = Test-IAMInstanceProfile -Token $MetadataInfo[1] 6>> $LogsDestination
				$Output.Add($IAMinstanceprofile) | Out-Null
				if ($IAMinstanceprofile.Value -ne "N/A") {
					$Output.Add((Test-IAMInstanceProfileCredentialLastUpdate -Token $MetadataInfo[1] -IAMInstanceProfile $IAMinstanceprofile.Value 6>> $LogsDestination)) | Out-Null
					$Output.Add((Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation $ParentDirectory 6>> $LogsDestination)) | Out-Null
				}
				else {
					Write-Log -Message "IAM instance profile is not attached to the instance. Skipping the checks for IAM instance profile last update and STS caller identity" -LogLevel "ERROR" 6>> $LogsDestination
					$Output.Add((Test-IAMInstanceProfileCredentialLastUpdate -Token "N/A" -IAMInstanceProfile "N/A" -NoIAMattached 6>> $LogsDestination)) | Out-Null
					$Output.Add((Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation $ParentDirectory -Skip 6>> $LogsDestination)) | Out-Null
				}
			}	
			else {
				Write-Log -Message "Metadata is not reachable. Skipping endpoints checks, IAM instance profile, IAM instance profile last update and STS caller identity" -LogLevel "ERROR" 6>> $LogsDestination
				$region = 0
				$ec2instanceid = "i-0123456789abcdefa"
				$Output.Add((Get-MetadataAccess -StatusCode $MetadataInfo[0] -Region $region -EC2InstanceID $ec2instanceid 6>> $LogsDestination)) | Out-Null
				$Output.Add((Test-IAMInstanceProfile -Token "N/A" -NoMetadataAccess 6>> $LogsDestination)) | Out-Null
				$Output.Add((Test-IAMInstanceProfileCredentialLastUpdate -Token "N/A" -IAMInstanceProfile "N/A" -NoMetadataAccess 6>> $LogsDestination)) | Out-Null
				$Output.Add((Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation $ParentDirectory -Skip 6>> $LogsDestination)) | Out-Null

			}
		}
		if ($region -ne 0) {
			foreach ($endpoint in $endpoints) {
				$Output.Add((Test-EndpointsNetworkAccess -Endpoint $endpoint -Region $region 6>> $LogsDestination)) | Out-Null
			}
		}
		else {
			foreach ($endpoint in $endpoints) {
				$Output.Add((Test-EndpointsNetworkAccess -Endpoint $endpoint -Region "region" -Skip 6>> $LogsDestination)) | Out-Null
			}
		}
	
		#Check proxy settings if the amazonssmagent is available
		if ($ServiceAvailability -eq 1) {
			Write-Log -Message "The service is available. Going through all proxies' check" 6>> $LogsDestination
			$Output.Add((Get-AgentProxySettings 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-SystemWideEnvironmentVariablesProxy 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-LocalSystemAccountEnvironmentVariablesProxy 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-SystemWideProxy 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-IEProxySettings 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-SSMAgentVersion -Region $region 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-SessionManagerPluginVersion 6>> $LogsDestination)) | Out-Null
		}
		else {
			Write-Log -Message "The service is not available. Skipping all proxies's check" -LogLevel "ERROR" 6>> $LogsDestination
			$Output.Add((Get-AgentProxySettings -Skip 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-SystemWideEnvironmentVariablesProxy -Skip 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-LocalSystemAccountEnvironmentVariablesProxy -Skip 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-SystemWideProxy -Skip 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-IEProxySettings -Skip 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-SSMAgentVersion -Skip 6>> $LogsDestination)) | Out-Null
			$Output.Add((Get-SessionManagerPluginVersion -Skip 6>> $LogsDestination)) | Out-Null
		}

		if ($Table) {
			$Output | ForEach { [PSCustomObject]$_ } | Format-Table -Wrap
		}
		elseif ($GridView) {
			$Output | ForEach { [PSCustomObject]$_ } | Out-GridView -Title 'SSM troubleshooting'
		}
		else {
			$Output | ForEach { [PSCustomObject]$_ } | Format-List
		}

		$Output | ForEach { [PSCustomObject]$_ } | Format-List | Out-File -FilePath $OutputsDestination
		
	}

	end {
		Remove-Item -Path "$ParentDirectory\temp" -Recurse
		Write-Log -Message "The END!!!" 6>> $LogsDestination
	}
}