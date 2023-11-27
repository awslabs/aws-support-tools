<#
  .Synopsis
    Test a TCP connection against an endpoint
  .Description
    This is a public function used to test a connection using Test-NetConnection
  .Example
    Test-EndpointsNetworkAccess -Endpoint "mgn.us-east-1.amazonaws.com"
  .INPUTS
	Endpoint
    Skip = Switch to skip this function.
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>

Function Test-EndpointsNetworkAccess {
  [CmdletBinding()]
  param (
    [String]$mgnVpceId,
    [String]$s3VpceId,
    [String]$region = "us-east-1",
    [Switch]$Skip
  )
  if (-not ($Skip)) {
    $Endpoints = @()
    $publicMgnEndpoints = @(
      "mgn.$region.amazonaws.com"
    )
    $publicS3Endpoints = @(
      "aws-mgn-clients-$region.s3.$region.amazonaws.com",
      "aws-mgn-clients-hashes-$region.s3.$region.amazonaws.com",
      "aws-mgn-internal-$region.s3.$region.amazonaws.com",
      "aws-mgn-internal-hashes-$region.s3.$region.amazonaws.com",
      "aws-application-migration-service-$region.s3.$region.amazonaws.com",
      "aws-application-migration-service-hashes-$region.s3.$region.amazonaws.com",
      "amazon-ssm-$region.s3.$region.amazonaws.com",
      "S3.$region.amazonaws.com"
    )


    $privateMgnEndpoints = @(
      "$mgnVpceId.mgn.$region.vpce.amazonaws.com"
    )
    # For VPC Interface Endpoints, no matter what you put the bucket name as it will always resolve to the VPCE IP.
    # Therefore, just checking to make sure the VPCE is available via TCP 443 should be good enough.
    $privateS3Endpoints = @(
      "bucket.$s3VpceId.S3.$region.vpce.amazonaws.com"
    )

    if ($s3VpceId) {
      ForEach ($privateS3Endpoint in $privateS3Endpoints) {
        $Endpoints += $privateS3Endpoint -join ""

      }
    }
    else {
      ForEach ($publicS3Endpoint in $publicS3Endpoints) {
        $Endpoints += $publicS3Endpoint -join ""
      }
    }



    if ($mgnVpceId) {
      ForEach ($privateMgnEndpoint in $privateMgnEndpoints) {
        $Endpoints += $privateMgnEndpoint -join ""

      }
    }
    else {
      ForEach ($publicMgnEndpoint in $publicMgnEndpoints) {
        $Endpoints += $publicMgnEndpoint -join ""
      }

    }
    foreach ($Endpoint in $Endpoints) {
      $endpointOutput = Test-TcpConnection -Endpoint $Endpoint
      if ($endpointOutput.value -ne "[GREEN]") {
        $Reachable = $false
      }
    }
    if ($Reachable -ne $false) {
      $check = "Endpoints Connectivity"
      $value = "[GREEN]"
      Write-Log -Message "The check ""$check"" output is $value"
      $Action = "No action required. All endpoints are reachable."
      Write-Log -Message $Action
      $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
    }
  }
  else {
    $check = "Endpoints Connectivity"
    $value = "[GREEN]"
    Write-Log -Message "The check ""$check"" output is $value"
    $Action = "No action required. Skipped."
    Write-Log -Message $Action
    $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
  }
}