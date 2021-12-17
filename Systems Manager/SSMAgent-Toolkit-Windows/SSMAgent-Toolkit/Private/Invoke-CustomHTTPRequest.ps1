<#
  .Synopsis
    Make an HTTP request with custom error handling
  .Description
    This is a private function used to make an HTTP request to a custom endpoint including a custom error handling. 
  .Example
    Invoke-CustomHTTPRequest
#>

function Invoke-CustomHTTPRequest {
  [CmdletBinding()]
  param (
    [string]$Uri,
    [string]$Method = "Get",
    [System.Collections.IDictionary]$Headers
		
  )
    
  begin {
    Write-Log "Making an HTTP request"
    Write-Log "URL: $($Uri), Method: $($Method)" 
    Write-Log "Headers Keys: $($Headers.Keys), Headers Values: $($Headers.Values)"
  }
    
  process {
    try {
      $httpResponse = Invoke-WebRequest -Uri $Uri -Method $Method -Headers $Headers -UseBasicParsing
      $resStatusCode = $httpResponse.StatusCode
      if ($resStatusCode -eq 200) {
        Write-Log "Successfully made the request - Status Code: $($resStatusCode)"
      }
      if ($PSCmdlet.MyInvocation.BoundParameters["Verbose"].IsPresent) {
        Write-Log -Message "$($httpResponse.RawContent)" -LogLevel DEBUG
      }
      return $httpResponse
    }
    catch [System.Net.WebException] {
      # The exception that is thrown when an error occurs while accessing the network through a pluggable protocol.
      # https://docs.microsoft.com/en-us/dotnet/api/system.net.webexception?view=netcore-3.1
      Write-Log -Message "Failed..." -LogLevel "ERROR"
      Write-Log -Message "$($_.Exception.Response)" -LogLevel "ERROR"
      $statusCode = [int]$_.Exception.Response.StatusCode
      $response = $_.Exception.Response.StatusDescription
      Write-Log -Message "Status Code: $($statusCode)" -LogLevel "ERROR"
      Write-Log -Message "$($response)" -LogLevel "ERROR"
      return 0
    }
    catch {
      Write-Log -Message "Failed..." -LogLevel "ERROR"
      Write-Log -Message "$($_)" -LogLevel "ERROR"
      return 0
    }
  }
    
  end {
  }
}