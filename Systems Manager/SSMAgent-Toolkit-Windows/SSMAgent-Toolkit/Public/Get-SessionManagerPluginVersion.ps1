<#
  .Synopsis
    Check the installed and latest version of Session Manager Plugin.
  .Description
    This is a public function used to check the Session Manager Plugin version values for both installed and publicly available.
  .Example
    Get-SessionManagerPluginVersion
  .INPUTS
    LatestVersionUrl = The path to latest version URL. Default value: "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/VERSION".
    SessionManagerPluginVersionPath = The path for installed session manager agent. Default value: "$Env:ProgramFiles\Amazon\SessionManagerPlugin\VERSION".
    Skip = Switch to skip this function if the service is not available.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-SessionManagerPluginVersion {
  [CmdletBinding()]
  param (
    [String]$LatestVersionUrl = "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/VERSION",
    [String]$SessionManagerPluginVersionPath = "$Env:ProgramFiles\Amazon\SessionManagerPlugin\VERSION",
    [Switch]$Skip
  ) 
  
  $check = "Session Manager Plugin version"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if (-not ($Skip)) {    
    Write-Log -Message "Testing if SessionManager path exist. $SessionManagerPluginVersionPath"
    if (Test-Path $SessionManagerPluginVersionPath) {
      $CurrentSessionManagerPluginVersion = Get-Content $SessionManagerPluginVersionPath
    
      Write-Log -Message "Checking the latest Session Manager Plugin version from $LatestVersionUrl."
      Write-Log -Message "Checking the install Session Manager Plugin version from $SessionManagerPluginVersionPath"
      Write-Log -Message "The install Session Manager Plugin version is $CurrentSessionManagerPluginVersion"
      $value = "Pass"
    
      try {
        $LatestSessionManagerPluginVersion = Invoke-RestMethod -Uri $LatestVersionUrl
        Write-Log -Message "The latest Session Manager Plugin version is $LatestSessionManagerPluginVersion."
        if ([System.Version]$CurrentSessionManagerPluginVersion -eq [System.Version]$LatestSessionManagerPluginVersion) {
          Write-Log -Message "The install and the latest Session Manager Plugin version is $LatestSessionManagerPluginVersion."
          $note = "The install and the latest Session Manager Plugin version is $LatestSessionManagerPluginVersion"
        }
        else {
          Write-Log -Message "The install Session Manager Plugin version is $CurrentSessionManagerPluginVersion, the latest is $LatestSessionManagerPluginVersion."
          $note = "The install Session Manager Plugin version is $CurrentSessionManagerPluginVersion, the latest is $LatestSessionManagerPluginVersion" 
        }
      }
      catch {
        Write-Log -Message ("Unable to retrieve the latest Session Manager Plugin version from $LatestVersionUrl. " + $($PSitem.ToString())) -LogLevel "ERROR"
        $note = "The install Session Manager Plugin version is $CurrentSessionManagerPluginVersion"
      }
    }
    
    else {
      $value = "Skip"
      $note = "This test skipped since the Session Manager Plugin is not is not installed"
      Write-Log -Message "The Session Manager Plugin version check skipped since is not is not installed" -LogLevel "INFO"
      Write-Log -Message "To install Session Manager Plugin - https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html" -LogLevel "INFO"
    }
  }

  else {
    $value = "Skip"
    $note = "This test skipped since the SSM Agent is not installed"
    Write-Log -Message "The Session Manager Plugin Version check skipped since the SSM Agent is not installed" -LogLevel "WARN"
  }

  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}