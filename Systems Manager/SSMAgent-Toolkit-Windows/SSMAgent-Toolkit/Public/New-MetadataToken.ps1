<#
  .Synopsis
    Retrieve metadata token and statuscode to metadata url.
  .Description
    This is a public function used to retrieve metadata token and statuscode to metadata url by using Invoke-CustomHTTPRequest function. This will helps t know if we have metadata accessibility or not.
  .Example
    Test-MetadataToken
  .INPUTS
	  N/A
  .OUTPUTS                                                                            
    Return the status code.
#>

Function New-MetadataToken {
  # This function to check if the instance have an access to the instance Metadata
  try {
    $Uri = "http://169.254.169.254/latest/api/token"
    $Method = "PUT"
    [System.Collections.IDictionary]$Headers = @{"X-aws-ec2-metadata-token-ttl-seconds" = "300" }
    $token = Invoke-CustomHTTPRequest -Uri $Uri -Method $Method -Headers $Headers
    # This will only execute if the Invoke-WebRequest is successful.
    if ($token -eq 0) {
      Write-Log -Message ("Unable to retrieve metadata token: " + $($PSitem.ToString())) -LogLevel "ERROR"
      return 0
    }
    else {
      $StatusCode = $token.StatusCode
      Write-Log -Message "Metadata's token has been retrieved."
      return $StatusCode, $token
    }
  }
  catch {
    Write-Log -Message ("Unable to retrieve metadata token: " + $($PSitem.ToString())) -LogLevel "ERROR"
    return 0
  }
}