<#
  .Synopsis
    Check if the instance is Managed(Hybrid) instance Retrieve the region and mi- id.
  .Description
    This is a public function used to check if the instance is Managed(Hybrid) instance Retrieve the region and mi- id. This function will check if $Env:ProgramData\Amazon\SSM\InstanceData\registration exist or not.
  .Example
    Test-HybridRegistration
  .INPUTS
	N/A
  .OUTPUTS                                                                            
    Return the region and mi- id.
#>
Function Test-HybridRegistration {
  [CmdletBinding()]
  param (
  )
   
  $check = "Managed(hybrid) Instance Registration"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if (Test-Path $Env:ProgramData\Amazon\SSM\InstanceData\registration) {
    $RegistrationFile = Get-Content "$Env:ProgramData\Amazon\SSM\InstanceData\registration" | Out-String | ConvertFrom-Json
    Write-Log -Message "The ID of the instance retrieved from the hybrid registration file is $RegistrationFile.ManagedInstanceID"
    Write-Log -Message "Region from the hybrid registration file is $RegistrationFile.Region"

    $value = "Pass"
    $note = "ManagedInstanceID = $($RegistrationFile.ManagedInstanceID), Region = $($RegistrationFile.Region)"
    Write-Log -Message "Pulling the information from $Env:ProgramData\Amazon\SSM\InstanceData\registration. The instance will skip checking the metadata."
    Write-Log -Message "ManagedInstanceID = $RegistrationFile.ManagedInstanceID, Region = $RegistrationFile.Region"
    return (New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"), $($RegistrationFile.ManagedInstanceID), $($RegistrationFile.Region)
  }
  else {
    $value = "Skip"
    $note = "The instance is not configured as Managed(hybrid) Instance. Metadata will be used to get the InstanceId and Region "
    Write-Log -Message $note
    return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
  }
            
    
}