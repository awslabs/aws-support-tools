<#
  .Synopsis
    Check the if the service is available under Windows Services.
  .Description
    This is a public function used to check the if the service is available under Windows Services.
  .Example
    Get-ServiceAvailability
  .INPUTS
    ServiceName
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-ServiceAvailability {
  [CmdletBinding()]
  param (
    [String]$ServiceName = "amazonssmagent"
  )
  $check = "Amazon SSM agent service running"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  Write-Log -Message "Checking if we can retrieve the service using Get-Service $ServiceName"
  $Service = Get-Service $ServiceName -ErrorAction SilentlyContinue
  
  if ($Service) {
    Write-Log -Message "$ServiceName service is available."
    return 1, $Service.Status
  }
  else {
    $value = "Fail"
    $note = "Please make sure the SSM agent is installed."
    Write-Log -Message "$ServiceName service is not available. Please make sure the SSM agent is installed." -LogLevel "ERROR"
  }
  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}