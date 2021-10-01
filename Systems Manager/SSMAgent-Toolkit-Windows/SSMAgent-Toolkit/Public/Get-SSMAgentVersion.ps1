<#
  .Synopsis
    Check the installed and latest version of SSM Agent.
  .Description
    This is a public function used to check the SSM Agent version values for both installed and publicly available.
  .Example
    Get-SSMAgentVersion
  .INPUTS
    Region = The region to when SSM Agent register to.
    RegistryHive = The registry hive where we look for installed applications. Default value: "LocalMachine".
    RegistryPath = The path for the install applications in the registry. Default value: "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall".
    Skip = Switch to skip this function if the service is not available.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-SSMAgentVersion {
  [CmdletBinding()]
  param (
    [String]$Region,
    [String]$RegistryHive = "LocalMachine",
    [String]$RegistryPath = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall", #Define the variable to hold the location of Currently Installed Programs,
    [Switch]$Skip
  ) 
  
  $check = "SSMAgent version"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if (-not ($Skip)) { 
    $LatestVersionUrl = "https://s3.$Region.amazonaws.com/amazon-ssm-$Region/latest/VERSION"
    Write-Log -Message "Checking the latest SSM agent from $LatestVersionUrl."
    
    try {
      Write-Log -Message "Checking the install agent version from $RegistryHive`:\$RegistryPath"
      $CurrentSSMAgentVersion = Get-AppVersionNumber -RegHive $RegistryHive -Path $RegistryPath -AppName "Amazon SSM Agent"
      $CurrentSSMAgentVersion = [System.Version]$CurrentSSMAgentVersion
      Write-Log -Message "The install SSM Agent version is $CurrentSSMAgentVersion"
    }
    catch {
      Write-Log -Message ("Unable to retrieve the install SSM Agent version from $RegistryHive`:\$RegistryPath. " + $($PSitem.ToString())) -LogLevel "ERROR"
      $CurrentSSMAgentVersion = [System.Version]"0.0.0.0"
    }

    try {
      $LatestSSMAgentVersion = Invoke-RestMethod -Uri $LatestVersionUrl
      Write-Log -Message "The latest agent version in $Region is $LatestSSMAgentVersion."
      $value = "Pass"
      if ([System.Version]$CurrentSSMAgentVersion -eq "0.0.0.0") {
        $note = "The latest agent version in $Region is $LatestSSMAgentVersion"
      }
      elseif ([System.Version]$CurrentSSMAgentVersion -eq [System.Version]$LatestSSMAgentVersion) {
        Write-Log -Message "The install and the latest agent version in $Region is $LatestSSMAgentVersion."
        $note = "The install and the latest agent version in $Region is $LatestSSMAgentVersion"
      }
      elseif ([System.Version]$CurrentSSMAgentVersion -ne [System.Version]$LatestSSMAgentVersion) {
        Write-Log -Message "The install SSM Agent version is $CurrentSSMAgentVersion, the latest in $Region is $LatestSSMAgentVersion."
        $note = "The install SSM Agent version is $CurrentSSMAgentVersion, the latest in $Region is $LatestSSMAgentVersion" 
      }
    }
    catch {
      if ([System.Version]$CurrentSSMAgentVersion -eq "0.0.0.0") {
        $value = "N/A"
        Write-Log -Message ("Unable to retrieve the install or latest SSM Agent version from $LatestVersionUrl. " + $($PSitem.ToString())) -LogLevel "ERROR"
        $note = "Unable to retrieve the install or latest SSM Agent version"
      }
      else {
        $value = "Pass"
        Write-Log -Message ("Unable to retrieve the latest SSM Agent version from $LatestVersionUrl." + $($PSitem.ToString())) -LogLevel "ERROR"
        $note = "The install SSM Agent version is $CurrentSSMAgentVersion"
      }
    }
  }

  else {
    $value = "Skip"
    $note = "This test skipped since the SSM Agent is not installed"
    Write-Log -Message "The SSMAgent Version check skipped since the SSM Agent is not installed" -LogLevel "ERROR"
    Write-Log -Message "Installing and configuring SSM Agent on EC2 instances for Windows Server - https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-install-ssm-win.html" -LogLevel "INFO"
  }

  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}