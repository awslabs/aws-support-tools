<#
.SYNOPSIS
    Run checks needed for an instance to be online in SSM.
.DESCRIPTION
    This is tha main function to go through all checks needed for an EC2 instance to be online in SSM. Each check will be on a seprate function.
.EXAMPLE
    PS C:\> Invoke-SSMChecks
  	PS C:\> Invoke-SSMChecks -GridView "False"
.INPUTS
	endpoints = default as endpoints for AWS Systems Manager
	servicename = default as "amazonssmagent"
	AgentRegistryPath = SSM Agent registry path
	GridView = To have the gridview in the output on or off. default is true. 
.OUTPUTS                                                                            
	[2020-10-19T17:48:21.9526299-04:00] [INFO] Log available at C:\Users\Administrator\Desktop\xxxx\xxxxxxx\log\SSMCheck_2020-10-19-05-48-21.log
	[2020-10-19T17:48:21.9536271-04:00] [INFO] Report available at C:\Users\Administrator\Desktop\xxxx\xxxxxxx\report\SSMCheck_2020-10-19-05-48-21.txt
	Running all the tests can take a few minutes...

		___ _       _______    _____            __                         __  ___                                 
	   /   | |     / / ___/   / ___/__  _______/ /____  ____ ___  _____   /  |/  /___ _____  ____ _____ ____  _____
	  / /| | | /| / /\__ \    \__ \/ / / / ___/ __/ _ \/ __ __ \/ ___/   / /|_/ / __ / __ \/ __ / __ / _ \/ ___/
	 / ___ | |/ |/ /___/ /   ___/ / /_/ (__  ) /_/  __/ / / / / (__  )  / /  / / /_/ / / / / /_/ / /_/ /  __/ /
	/_/  |_|__/|__//____/   /____/\__, /____/\__/\___/_/ /_/ /_/____/  /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/
	                             /____/                                                         /____/

	Check                                               Value                                                                   Note                                                                    
	-----                                               -----                                                                   ----                                                                    
	Windows sysprep image state complete                Pass                                                                    This is the desired state
	Amazon SSM agent service running                    Pass                                                                    amazonssmagent service is in Running state. This is the desired state
	Amazon SSM service account                          LocalSystem                                                             This is the recommended account to use
	EC2 instance metadata accessible                    Pass                                                                    N/A                                                                     
	ssm.us-east-1.amazonaws.com accessible              Pass                                                                    N/A                                                                     
	ec2messages.us-east-1.amazonaws.com accessible      Pass                                                                    N/A                                                                     
	ssmmessages.us-east-1.amazonaws.com accessible      Pass                                                                    N/A                                                                     
	IAM instance profile                                SSM-Role                                                                IAM instance profile SSM-Role is attached to the instance
	IAM profile credential valid                        Pass                                                                    IAM instance profile's credential is up todate. IAM credential
																																Expiration time stamp is 10/19/2020 23:16:32. Last update is
    	                                                                                                                       	10/19/2020 17:15:41 UTC
 	LocalSystem account user API assume role            arn:aws:sts::xxxxxxx:assumed-role/SSM-Role/i-0123456789EXAMPLE		    The role and the instance in the ARN should match the role in the
                                                                                                                            	metadata and the current instanceID
	SSM Agent Proxy Setting                             N/A                                                                     There is no proxy setting for SSM Agent
	System-wide environment variable proxy              N/A                                                                     There is no http_proxy, https_proxy or no_proxy configured for
     		                                                                                                                    System-wide environment variable proxy.
	LocalSystem account user environment variable proxy N/A                                                                     There is no http_proxy, https_proxy or no_proxy configured for
     	                                                                                                                        LocalSystem account user environment variable proxy.
	WinHTTP system-wide proxy                            Current WinHTTP proxy settings:      Direct access (no proxy server).  This is the output of - netsh winhttp show proxy:  Current WinHTTP
      	                                                                                                                        proxy settings:      Direct access (no proxy server).
	LocalSystem account user Internet Explorer proxy    N/A                                                                     If the instance behind a proxy and PowerShell via run command have a
     	                                                                                                                        command which need access to the internet would fail if there is no                                                                                                                                 Internet Explorer proxy settings 
#>


function Invoke-SSMChecks {
	param (
		# Endpoints for AWS Systems Manager https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-create-vpc.html#sysman-setting-up-vpc-create
		$endpoints = @(
			"ssm",
			"ec2messages",
			"ssmmessages",
			"S3",
			"kms",
			"logs"
		),
		# The Windows Service name of the Agent
		[String]$servicename = "amazonssmagent",
		# SSM Agent registry path
		[String]$AgentRegistryPath = "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\AmazonSSMAgent",
		# Set the default file path and log location, all errors should function as STOP errors for logging purposes
		[String]$GridView = "True"
	)
	
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
		#Name the log and report files based on the timestamp
		$TimeStamp = Get-Date -Format "yyyy-MM-dd-hh-mm-ss"
		#The directory of this function
		$SourceDirectory = $PSScriptRoot
		#The parent directory of the module
		$ParentDirectory = (get-item $SourceDirectory).parent.fullname
		#Log directory
		$LogDirectory = ("$ParentDirectory\log\" -replace ("util\\", ""))
		#Log file name
		$LogDestination = $LogDirectory + $FileNamePrefix + $TimeStamp + ".log"
		#Report directory
		$ReportDirectory = ("$ParentDirectory\report\" -replace ("util\\", ""))
		#Report file name
		$reportDestination = $ReportDirectory + $FileNamePrefix + $TimeStamp + ".txt"
		Write-Log -Message "Starting..." 6>> $LogDestination
		New-Item -Path $ParentDirectory -Name "temp" -ItemType "directory" -Force | Out-Null
		Write-Log -Message "Log available at $LogDestination"
		Write-Log -Message "Report available at $reportDestination"
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
		$Output.Add((Get-WindowsImageState 6>> $LogDestination)) | Out-Null
		$serviceavalibility = Get-ServiceAvailability -ServiceName $servicename 6>> $LogDestination
		# Make more checks if the amazonssmagent is available 
		if ($serviceavalibility[0] -eq 1) {
			Write-Log -Message "$servicename is available. Checking the service running status and the account uses to run the service" 6>> $LogDestination
			$Output.Add((Get-ServiceStatus -ServiceName $servicename -ServiceStatus $serviceavalibility[1] 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-ServiceAccount -ServiceName $servicename 6>> $LogDestination)) | Out-Null
		}
		else {
			Write-Log -Message "$servicename is not available. Skipping the check for account uses to run the service" -LogLevel "ERROR" 6>> $LogDestination
			$Output.Add($serviceavalibility) | Out-Null
			$Output.Add((Get-ServiceAccount -ServiceName $servicename -Skip $true 6>> $LogDestination)) | Out-Null
		}
		#Check if the instance have a registration file exit. If does, means the instance is configured as Managed(hybrid) instance and will skip the metadata check.
		
		$InstanceRegistrationResults = (Test-HybridRegistration 6>> $LogDestination)
		$Output.Add(($InstanceRegistrationResults[0] 6>> $LogDestination)) | Out-Null
		if (-not ([string]::IsNullOrEmpty($InstanceRegistrationResults[1]))) {
			$region = $InstanceRegistrationResults[2]
			$Output.Add((Get-MetadataAccess -ManagedInstance $true 6>> $LogDestination)) | Out-Null
			$Output.Add((Test-IAMInstanceProfile -ManagedInstance $true 6>> $LogDestination)) | Out-Null
			$Output.Add((Test-IAMInstanceProfileCredentialLastUpdate -ManagedInstance $true 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation $ParentDirectory 6>> $LogDestination)) | Out-Null
		}
		else {
			# Retrieve Metadata token and Invoke web request reply code for meta data accessibility
			$metadatainfo = (New-MetadataToken 6>> $LogDestination)
			
			if (-not ([string]::IsNullOrEmpty($metadatainfo[1]))) {
				#To check if there is an access to the metadata. Then check the InstanceID, region, IAM profile settings and get STSCallerIdentity under the LocalSystem, call all the checks that would need the access to the metadata
				Write-Log -Message "Metadata is reachable. Retrieve Instance ID and Region from the metadata" 6>> $LogDestination
				$ec2instanceid = Get-InstanceID -Token $metadatainfo[1] 6>> $LogDestination
				$region = Get-Region -Token $metadatainfo[1] 6>> $LogDestination
				$Output.Add((Get-MetadataAccess -StatusCode $metadatainfo[0] -Region $region -EC2InstanceID $ec2instanceid 6>> $LogDestination)) | Out-Null
				$IAMinstanceprofile = Test-IAMInstanceProfile -Token $metadatainfo[1] 6>> $LogDestination
				$Output.Add($IAMinstanceprofile) | Out-Null
				if ($IAMinstanceprofile.Value -ne "N/A") {
					$Output.Add((Test-IAMInstanceProfileCredentialLastUpdate -Token $metadatainfo[1] -IAMInstanceProfile $IAMinstanceprofile.Value 6>> $LogDestination)) | Out-Null
					$Output.Add((Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation $ParentDirectory 6>> $LogDestination)) | Out-Null
				}
				else {
					Write-Log -Message "IAM instance profile is not attached to the instance. Skipping the checks for IAM instance profile last update and STS caller identity" -LogLevel "ERROR" 6>> $LogDestination
					$Output.Add((Test-IAMInstanceProfileCredentialLastUpdate -Token "N/A" -IAMInstanceProfile "N/A" -NoIAMattched $true 6>> $LogDestination)) | Out-Null
					$Output.Add((Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation $ParentDirectory -Skip $true 6>> $LogDestination)) | Out-Null
				}
			}	
			else {
				Write-Log -Message "Metadata is not reachable. Skipping endpoints checks, IAM instance profile, IAM instance profile last update and STS caller identity" -LogLevel "ERROR" 6>> $LogDestination
				$region = 0
				$Output.Add((Test-IAMInstanceProfile -Token "N/A" -NoMetadataAccess $true 6>> $LogDestination)) | Out-Null
				$Output.Add((Test-IAMInstanceProfileCredentialLastUpdate -Token "N/A" -IAMInstanceProfile "N/A" -NoMetadataAccess $true 6>> $LogDestination)) | Out-Null
				$Output.Add((Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation $ParentDirectory -Skip $true 6>> $LogDestination)) | Out-Null

			}
		}
		if ($region -ne 0) {
			foreach ($endpoint in $endpoints) {
				$Output.Add((Test-EndpointsNetworkAccess -Endpoint $endpoint -Region $region 6>> $LogDestination)) | Out-Null
			}
		}
		else {
			foreach ($endpoint in $endpoints) {
				$Output.Add((Test-EndpointsNetworkAccess -Endpoint $endpoint -Region "region" -Skip $true 6>> $LogDestination)) | Out-Null
			}
		}
	
		#Check proxy settings if the amazonssmagent is available
		if ($serviceavalibility -eq 1) {
			Write-Log -Message "$servicename is available. Going through all proxy checks" 6>> $LogDestination
			$Output.Add((Get-AgentProxySettings -Key $AgentRegistryPath 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-SystemWideEnvironmentVariablesProxy 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-LocalSystemAccountEnvironmentVariablesProxy 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-SystemWideProxy 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-IEProxySettings 6>> $LogDestination)) | Out-Null
		}
		else {
			Write-Log -Message "$servicename is not available. Skipping all proxy checks" -LogLevel "ERROR" 6>> $LogDestination
			$Output.Add((Get-AgentProxySettings -Key $AgentRegistryPath -Skip $true 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-SystemWideEnvironmentVariablesProxy -Skip $true 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-LocalSystemAccountEnvironmentVariablesProxy -Skip $true 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-SystemWideProxy -Skip $true 6>> $LogDestination)) | Out-Null
			$Output.Add((Get-IEProxySettings -Skip $true 6>> $LogDestination)) | Out-Null
		}

		$Output | ForEach { [PSCustomObject]$_ } | Format-Table -Wrap
		$Output | ForEach { [PSCustomObject]$_ } | Format-List | Out-File -FilePath $reportDestination
		if ($GridView -eq "True") {
			$Output | ForEach { [PSCustomObject]$_ } | Out-GridView -Title 'SSM troubleshooting' #Format-Table | Out-GridView -PassThru
		}
		
	}

	end {
		Remove-Item -Path "$ParentDirectory\temp" -Recurse
		Write-Log -Message "The END!!!" 6>> $LogDestination
	}
}