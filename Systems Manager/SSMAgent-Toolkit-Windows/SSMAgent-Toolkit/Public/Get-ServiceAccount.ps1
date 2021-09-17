<#
  .Synopsis
    Check the if the account which the service is running as.
  .Description
    This is a public function used to check the if the account which the service is running as.
  .Example
    Get-ServiceAccount
  .INPUTS
    ServiceName
    Skip = Switch to skip this function if the service is not available.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-ServiceAccount {
  [CmdletBinding()]
  param (
    [String]$ServiceName = "amazonssmagent",
    [Switch]$Skip
  )
  $check = "Amazon SSM service account"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  $ServiceLogonAsAccount = (Get-WmiObject Win32_Service -Filter "Name='$ServiceName'").StartName
  
  if (-not ($Skip)) {
    if ($ServiceLogonAsAccount -ne "LocalSystem") {
      $value = $ServiceLogonAsAccount
      $note = "It's recommended to use Local System Account"
      Write-Log -Message "$ServiceName service account is not Local System account" -LogLevel "ERROR"
    }
    else {
      $value = $ServiceLogonAsAccount
      $note = "This is the recommended account to use"
      Write-Log -Message "$ServiceName service account is Local System account. This is the desired account."
    }    
  }
  else {
    $value = "Skip"
    $note = "This test skipped since the $ServiceName service is not available"
    Write-Log -Message "The Amazon SSM service account check skipped since The $ServiceName service is not available" -LogLevel "ERROR"
  }
    
  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}