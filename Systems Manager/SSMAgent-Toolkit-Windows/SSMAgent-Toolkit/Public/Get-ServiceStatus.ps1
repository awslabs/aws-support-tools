<#
  .Synopsis
    Check the if the the service running state.
  .Description
    This is a public function used to check the if the the service running state.
  .Example
    Get-ServiceStatus -ServiceStatus "Running"
  .INPUTS
    ServiceName
    ServiceStatus
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-ServiceStatus {
  [CmdletBinding()]
  param (
    [String]$ServiceName = "amazonssmagent",
    [String]$ServiceStatus
  )
   
  $check = "Amazon SSM agent service running"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if ($ServiceStatus -ne "Running") {
    $value = "Fail"
    $note = "Please make sure the $ServiceName service is in Running state"
    Write-Log -Message "$ServiceName service is not in Running state" -LogLevel "ERROR"
  }
  else {
    $value = "Pass"
    $note = "$ServiceName service is in Running state. This is the desired state"
    Write-Log -Message $note
  }
            
  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}