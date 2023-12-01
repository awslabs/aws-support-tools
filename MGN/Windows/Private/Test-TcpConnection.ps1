<#
  .Synopsis
    Test a TCP connection against an endpoint
  .Description
    This is a public function used to test a connection using Test-NetConnection
  .Example
    Test-TcpConnection -Endpoint "mgn.us-east-1.amazonaws.com"
  .INPUTS
	Endpoint
    Skip = Switch to skip this function.
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>

Function Test-TcpConnection {
  [CmdletBinding()]
  param (
    [String]$Endpoint,
    [Switch]$Skip
  )

  begin {
    $check = $Endpoint
    Write-Log -Message "___________________________________________________________________"
    Write-Log -Message "New check....."
    Write-Log -Message "$check"
    Write-Log "Testing a TCP connection over Port: 443"
  }

  process {

    if (-not ($Skip)) {
      try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($Endpoint, 443)
        $tcpClient.Close()
        $value = "[GREEN]"
        Write-Log -Message "The check ""$check"" output is $value"
        $Action = "No action required. Endpoint is reachable."
        Write-Log -Message "$Endpoint is reachable via port 443."
        Write-Log -Message $Action
      }
      catch {
        $value = "[RED]"
        Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
        $Action = "Please make sure the endpoint $Endpoint is accessible via TCP port 443."
        Write-Log -Message $Action -LogLevel "ERROR"
      }
    }
    else {
      $value = "[GREEN]"
      Write-Log -Message "The check ""$check"" output is $value"
      $Action = "No action required. Skipped."
      Write-Log -Message $Action
    }
  }
  end {
    if ($value -ne "[GREEN]") {
      $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
    }
    return Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
  }
}