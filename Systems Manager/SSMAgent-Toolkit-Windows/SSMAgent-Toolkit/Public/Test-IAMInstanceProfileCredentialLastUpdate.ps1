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
    $NoMetadataAccess = Switch to skip this function if there is no metadata access.
    $ManagedInstance = Switch to skip this function if the instance registered as hybrid instance.
    $NoIAMattached = Switch to skip this function if there is no iam attached to the instance.
  .OUTPUTS                                                                            
    Return the IAM instance profile.
#>

Function Test-IAMInstanceProfileCredentialLastUpdate {
  [CmdletBinding()]
  param (
    [String]$Token,
    [String]$IAMInstanceProfile,
    [Switch]$NoMetadataAccess,
    [Switch]$ManagedInstance,
    [Switch]$NoIAMattached
  )
  $check = "IAM profile credential valid"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if ($NoMetadataAccess) {
    $value = "Skip"
    $note = "This test skipped since the EC2 instance metadata is not accessible"
    Write-Log -Message "Unable to retrieve the IAM instance profile's LastUpdated and Expiration time stamp from the EC2 instance metadata or no IAM instance profile attached to the instance" -LogLevel "ERROR"
  }
  elseif ($NoIAMattached) {
    $value = "Skip"
    $note = "This test skipped since there is no IAM instance profile attached to the instance"
    Write-Log -Message "There is no IAM instance profile attached to the instance" -LogLevel "ERROR"
  }
  elseif ($ManagedInstance) {
    $value = "Skip"
    $note = "This test skipped since this server configured as Managed(hybrid) Instance"
    Write-Log -Message "Get the IAMInstanceProfileCredentialLastUpdate test skipped since this server configured as Managed(hybrid) Instance" -LogLevel "Info"
  }
  else {
    #LastUpdate time of the IAM instance profile
    $Uri = "http://169.254.169.254/latest/meta-data/iam/security-credentials/$IAMInstanceProfile"
    [System.Collections.IDictionary]$Headers = @{"X-aws-ec2-metadata-token" = $Token }
    $IAMMetadata = Invoke-CustomHTTPRequest -Uri $Uri -Headers $Headers | ConvertFrom-Json
    
    $LastUpdatedUTC = ([DateTime]($IAMMetadata.LastUpdated)).ToUniversalTime()
    $ExpirationUTC  = ([DateTime]($IAMMetadata.Expiration)).ToUniversalTime()

    Write-Log -Message "Last IAM Credential update from metadata is $($IAMMetadata.LastUpdated) in UTC"
    Write-Log -Message "Last IAM Credential update variable is $LastUpdatedUTC in UTC"
    Write-Log -Message "IAM Credential expiration from metadata is $($IAMMetadata.Expiration) in UTC"
    Write-Log -Message "IAM Credential expiration variable is $ExpirationUTC UTC"
        
    $CurrentTimeUTC = [DateTime]::UtcNow
    Write-Log -Message "Current time UTC is $CurrentTimeUTC UTC"

    #Check if the last credential update of the IAMInstanceProfile is more than 6 hours.
    if ($ExpirationUTC -gt $CurrentTimeUTC) {
      $value = "Pass"
      $note = "IAM instance profile's credential is up to date. IAM credential Expiration timestamp is $ExpirationUTC UTC. The Last update is $LastUpdatedUTC UTC"
      Write-Log -Message $note
    }
    elseif ($ExpirationUTC -lt $CurrentTimeUTC) {
      $value = "Fail"
      $note = "Credential Expiration time is in the past.Please make sure IAM Role is attach to the instance,Stop and start the instance"
      Write-Log -Message "Credential Expiration time is in the past for $IAMInstanceProfile IAM instance profile. The Last update is $LastUpdatedUTC UTC. IAM credential Expiration timestamp is $ExpirationUTC UTC. Please make sure IAM Role is attach to the instance,Stop and start the instance" -LogLevel "ERROR"
    }
  }
  New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}