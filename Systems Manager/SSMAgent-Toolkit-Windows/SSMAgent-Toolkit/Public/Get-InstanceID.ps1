<#
  .Synopsis
    Retrive the instance id from the metadata.
  .Description
    This is a public function used to retrive the instance id from the metadata using Invoke-CustomHTTPRequest function.
  .Example
    Get-InstanceID -Token $token
  .INPUTS
	$Token = String.
  .OUTPUTS                                                                            
    Return the instance id.
#>
Function Get-InstanceID {
    [CmdletBinding()]
    param (
        [String]$Token
    )
    #Get the instance from the metadata
    try {
        #Get the instance id from the metadata
        $Uri = "http://169.254.169.254/latest/meta-data/instance-id"
        [System.Collections.IDictionary]$Headers = @{"X-aws-ec2-metadata-token" = $Token }
        $instanceid = Invoke-CustomHTTPRequest -Uri $Uri -Headers $Headers
        Write-Log -Message "The ID of the instance retrieved from the metadata is $instanceid"
        return $instanceid
    }
    catch {
        Write-Log -Message ("Unable to retrieve the Instance ID from the metadata: " + $($PSitem.ToString())) -LogLevel "ERROR"
        Write-Log -Message "Unable to retrieve the instance id from the metadata. Make sure the instance has access to metadata path http://169.254.169.254/latest/meta-data/instance-id" -LogLevel "ERROR"
    }
}