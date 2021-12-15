<#
  .Synopsis
    Check the Startup mode for the service.
  .Description
    This is a public function used to check the startup mode for the services and compare it with the desire state.
  .Example
    Get-ServiceStartupMode
  .INPUTS
    ServiceName
    Skip = Switch to skip this function if the service is not available.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-ServiceStartupMode {
  [CmdletBinding()]
  param (
    [String]$ServiceName = "amazonssmagent",
    [Switch]$Skip
  )
  $check = "Amazon SSM service startup mode"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  $ServiceStartupMode = (Get-WmiObject Win32_Service -Filter "Name='$ServiceName'").StartMode
  
  if (-not ($Skip)) {
    if ($ServiceStartupMode -ne "Auto") {
      $value = $ServiceStartupMode
      $note = "It's recommended to use Automatic startup mode"
      Write-Log -Message "$ServiceName startup mode is not Automatic. It's recommended to update the startup more to Automatic. " -LogLevel "ERROR"
    }
    else {
      $value = $ServiceStartupMode
      $note = "This is the recommended startup mode to use"
      Write-Log -Message "$ServiceName startup mode is Automatic. This is the desired account."
    }    
  }
  else {
    $value = "Skip"
    $note = "This test skipped since the $ServiceName service is not available"
    Write-Log -Message "The Amazon SSM service startup mode check skipped since The $ServiceName service is not available. " -LogLevel "ERROR"
  }
    
  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}