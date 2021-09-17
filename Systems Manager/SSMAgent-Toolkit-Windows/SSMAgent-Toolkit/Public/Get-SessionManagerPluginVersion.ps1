<#
  .Synopsis
    Check the installed and latest version of Session Manager Plugin.
  .Description
    This is a public function used to check the Session Manager Plugin version values for both installed and publically available.
  .Example
    Get-SessionManagerPluginVersion
  .INPUTS
    N/A
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-SessionManagerPluginVersion {
  [CmdletBinding()]
  param (
    [String]$LatestVersionUrl = "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/VERSION",
    [String]$SessionManagerPluginVersionPath = "\Amazon\SessionManagerPlugin\VERSION",
    [Switch]$Skip
  ) 
  
  $check = "Session Manager Plugin version"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if (-not ($Skip)) {
    $ProgramFiles = [Environment]::GetEnvironmentVariable("ProgramFiles")
    $FullSessionManagerPluginVersionPath = "$ProgramFiles\$SessionManagerPluginVersionPath"

    Write-Log -Message "Testing if SessionManager path exist. $FullSessionManagerPluginVersionPath"
    if (Test-Path $FullSessionManagerPluginVersionPath) {
      $CurrentSessionManagerPluginVersion = Get-Content $FullSessionManagerPluginVersionPath
    
      Write-Log -Message "Checking the latest Session Manager Plugin version from $LatestVersionUrl."
      Write-Log -Message "Checking the current Session Manager Plugin version from $FullSessionManagerPluginVersionPath"
      Write-Log -Message "Current Session Manager Plugin version is $CurrentSessionManagerPluginVersion"
      $value = "Pass"
      $note = "Session Manager Plugin version is $CurrentSessionManagerPluginVersion"
    

      try {
        $LatestSessionManagerPluginVersion = Invoke-WebRequest -Uri $LatestVersionUrl
        $note += ", the latest Session Manager Plugin version is $LatestSessionManagerPluginVersion."
      }
      catch {
        Write-Log -Message ("Unable to retrieve the latest SSM Agent version from $LatestVersionUrl. " + $($PSitem.ToString())) -LogLevel "ERROR"
      }
    }
    else {
      $value = "Skip"
      $note = "This test skipped since the Session Manager Plugin is not is not installed."
      Write-Log -Message "The Session Manager Plugin version check skipped since is not is not installed" -LogLevel "INFO"
      Write-Log -Message "To install Session Manager Plugin - https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html" -LogLevel "INFO"
    }
  }

  else {
    $value = "Skip"
    $note = "This test skipped since the SSM Agent is not installed."
    Write-Log -Message "The Session Manager Plugin Version check skipped since the SSM Agent is not installed" -LogLevel "WARN"
  }

  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}