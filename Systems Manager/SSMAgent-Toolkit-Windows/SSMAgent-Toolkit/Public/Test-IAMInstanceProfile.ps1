<#
  .Synopsis
    Retrieve the IAM instance profile from the metadata.
  .Description
    This is a public function used to retrieve the IAM instance profile from the metadata using Invoke-CustomHTTPRequest function.
  .Example
    Test-IAMInstanceProfile -Token $token -NoMetadataAccess $false -ManagedInstance $false
  .INPUTS
    $Token
    $NoMetadataAccess = $false,
    $ManagedInstance = $false.
  .OUTPUTS                                                                            
    Return the IAM instance profile.
#>

Function Test-IAMInstanceProfile {
  [CmdletBinding()]
  param (
    [String]$Token,
    [String]$NoMetadataAccess = $false,
    [String]$ManagedInstance = $false
  )

  $check = "IAM instance profile"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"
    
  if (($NoMetadataAccess -eq $true)) {
    $value = "Skip"
    $note = "This test skipped since the EC2 instance metadata is not accessible"
    Write-Log -Message "Unable to retrieve the IAM instance profile from the EC2 instance metadata" -LogLevel "ERROR"
  }
  elseif (($ManagedInstance -eq $true)) {
    $value = "Skip"
    $note = "This test skipped since this server configured as Managed(hybrid) Instance"
    Write-Log -Message "Get the IAMInstanceProfile test skipped since this server configured as Managed(hybrid) Instance" -LogLevel "Info"
  }
  else {
    try {
      #Check if there IAMInstanceProfile present in the metadata
      $Uri = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
      [System.Collections.IDictionary]$Headers = @{"X-aws-ec2-metadata-token" = $Token }
      $IAMInstanceProfile = Invoke-CustomHTTPRequest -Uri $Uri -Headers $Headers
      if ($IAMInstanceProfile -ne 0) {
        $value = "$IAMInstanceProfile"
        $note = "IAM instance profile $IAMInstanceProfile is attached to the instance"
        Write-Log -Message "$IAMInstanceProfile is the instance profile name retrieved from the metadata."
        Write-Log -Message "Make sure it does have enough permission - https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-instance-profile.html"
      }
      else {
        $value = "N/A"
        $note = "Please make sure IAM Role is attach to the instance,Stop and start the instance"
        Write-Log -Message ("Unable to retrieve the IAM instance profile") -LogLevel "ERROR"
      }
    }
    catch {
      $value = "N/A"
      $note = "Please make sure IAM Role is attach to the instance,Stop and start the instance"
      Write-Log -Message ("Unable to retrieve the IAM instance profile: " + $($PSitem.ToString())) -LogLevel "ERROR"
    }
  }
  New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}