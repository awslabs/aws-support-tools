<#
  .Synopsis
    Retrieve the IAM instance profile expiration and last update time from the metadata.
  .Description
    This is a public function used to retrieve the IAM instance profile expiration and last update time from the metadata using Invoke-CustomHTTPRequest function.
  .Example
    Test-IAMInstanceProfileCredentialLastUpdate -Token $token -IAMInstanceProfile $profilename -NoMetadataAccess $false -ManagedInstance $false -NoIAMattached $false
  .INPUTS
    $Token
    $IAMInstanceProfile
    $NoMetadataAccess = $false
    $ManagedInstance = $false
    $NoIAMattached = $false
  .OUTPUTS                                                                            
    Return the IAM instance profile.
#>

Function Test-IAMInstanceProfileCredentialLastUpdate {
  [CmdletBinding()]
  param (
    [String]$Token,
    [String]$IAMInstanceProfile,
    [String]$NoMetadataAccess = $false,
    [String]$ManagedInstance = $false,
    [String]$NoIAMattached = $false
  )
  $check = "IAM profile credential valid"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if (($NoMetadataAccess -eq $true)) {
    $value = "Skip"
    $note = "This test skipped since the EC2 instance metadata is not accessible"
    Write-Log -Message "Unable to retrieve the IAM instance profile's LastUpdated and Expiration time stamp from the EC2 instance metadata or no IAM instance profile attached to the instance" -LogLevel "ERROR"
  }
  elseif (($NoIAMattached -eq $true)) {
    $value = "Skip"
    $note = "This test skipped since there is no IAM instance profile attached to the instance"
    Write-Log -Message "There is no IAM instance profile attached to the instance" -LogLevel "ERROR"
  }
  elseif (($ManagedInstance -eq $true)) {
    $value = "Skip"
    $note = "This test skipped since this server configured as Managed(hybrid) Instance"
    Write-Log -Message "Get the IAMInstanceProfileCredentialLastUpdate test skipped since this server configured as Managed(hybrid) Instance" -LogLevel "Info"
  }
  else {
    #LastUpdate time of the IAM instance profile
    $Uri = "http://169.254.169.254/latest/meta-data/iam/security-credentials/$IAMInstanceProfile"
    [System.Collections.IDictionary]$Headers = @{"X-aws-ec2-metadata-token" = $Token }
    $IAMMetadata = Invoke-CustomHTTPRequest -Uri $Uri -Headers $Headers | ConvertFrom-Json
    
    [DateTime]$LastUpdatedUTC = $IAMMetadata.LastUpdated
    [DateTime]$ExpirationUTC = $IAMMetadata.Expiration

    Write-Log -Message "Last IAM Credential update is $LastUpdatedUTC UTC"
    Write-Log -Message "IAM Credential expiration is $ExpirationUTC UTC"
        
    #Current time - 6 hours
    $CurrentTimeUTC = [DateTime]::UtcNow
    $TimeMinus6Hours = $CurrentTimeUTC.AddHours(-6)
    Write-Log -Message "Current time - 6 Hours is $TimeMinus6Hours UTC"

    #Check if the last credential update of the IAMInstanceProfile is more than 6 hours.
    if ($ExpirationUTC -gt $CurrentTimeUTC) {
      $value = "Pass"
      $note = "IAM instance profile's credential is up to date. IAM credential Expiration timestamp is $ExpirationUTC. The Last update is $LastUpdatedUTC UTC"
      Write-Log -Message $note
    }
    elseif ($ExpirationUTC -lt $CurrentTimeUTC) {
      $value = "Fail"
      $note = "Credential Expiration time is in the past.Please make sure IAM Role is attach to the instance,Stop and start the instance"
      Write-Log -Message "Credential Expiration time is in the past for $IAMInstanceProfile IAM instance profile. The Last update is $LastUpdatedUTC UTC. Please make sure IAM Role is attach to the instance,Stop and start the instance" -LogLevel "ERROR"
    }
  }
  New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}