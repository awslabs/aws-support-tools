<#
  .Synopsis
    Print out the results of the metadata accessibility.
  .Description
    This is a public function used to print out the results of the metadata accessibility.
  .Example
    Get-MetadataAccess -StatusCode 200 -Region "us-east-1" -EC2InstanceID "i-xxxxxxxx"
  .INPUTS
    StatusCode
    Region
    EC2InstanceID
    ManagedInstance = Default is $false, if call the function with $true value will skip the check.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>

Function Get-MetadataAccess {
  [CmdletBinding()]
  param (
    [String]$StatusCode,
    [String]$Region,
    [String]$EC2InstanceID,
    [String]$ManagedInstance = $false
  )
  $check = "EC2 instance metadata accessible"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"
  
  if ($ManagedInstance -ne $true) {
    #Check if there is access to the metadata
    if ($StatusCode -eq 200) {
      $value = "Pass"
      $note = "EC2 InstanceID = $EC2InstanceID, Region = $Region"
      Write-Log -Message "Metadata is accessible"
    }
    else {
      $value = "Fail"
      $note = "Please make sure there is a route to 169.254.169.254 via primary interface in the OS route table"
      Write-Log -Message "Metadata is not accessible. Check https://aws.amazon.com/premiumsupport/knowledge-center/waiting-for-metadata/ to troubleshoot" -LogLevel "ERROR"
    }
  }
  else {
    $value = "Skip"
    $note = "This test skipped since this server configured as Managed(hybrid) Instance"
    Write-Log -Message "Skipping Metadata accessibility check since this server configured as Managed(hybrid) Instance"
  }
  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}