<#
  .Synopsis
    Retrive the region from the metadata.
  .Description
    This is a public function used to retrive the region from the metadata using Invoke-CustomHTTPRequest function.
  .Example
    Get-Region -Token $token
  .INPUTS
	  $Token = String.
  .OUTPUTS                                                                            
    Return the region.
#>
Function Get-Region {
  [CmdletBinding()]
  param (
    [String]$Token
  )
  try {
    #Get the region from the metadata
    $Uri = "http://169.254.169.254/latest/dynamic/instance-identity/document" 
    [System.Collections.IDictionary]$Headers = @{"X-aws-ec2-metadata-token" = $Token }
    $Region = (Invoke-CustomHTTPRequest -Uri $Uri -Headers $Headers) | ConvertFrom-Json
    Write-Log -Message "Region from metadata is $($Region.region)"
    return $Region.region
  }
  catch {
    Write-Log -Message ("Unable to retrieve the region from the metadata: " + $($PSitem.ToString())) -LogLevel "ERROR"
    Write-Log -Message "Make sure the instance has access to metadata path http://169.254.169.254/latest/dynamic/instance-identity/document" -LogLevel "ERROR"
    return 0
  }
   
}