<#
  .Synopsis
    Test a TCP connection against an endpoint 
  .Description
    This is a public function used to test a connection using Test-NetConnection
  .Example
    Test-EndpointsNetworkAccess -Endpoint "ssm" -Region "us-east-1"
  .INPUTS
	Endpoint
    Region
    Skip = Switch to skip this function if the region can't be retrieved.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>

Function Test-EndpointsNetworkAccess {
    [CmdletBinding()]
    param (
        [String]$Endpoint,
        [String]$Region,
        [Switch]$Skip
    )

    begin {
        $check = "$Endpoint.$Region.amazonaws.com accessible"
        Write-Log -Message "New check....."
        Write-Log -Message "$check"
        Write-Log "Testing a TCP connection over Port: 443"
        
    }

    process {
     
        if (-not ($Skip)) {
            try {
                # Sample failed response
                # ComputerName           : amazon.com
                # RemoteAddress          : 176.0.0.100
                # RemotePort             : 8000
                # InterfaceAlias         : Ethernet 2
                # SourceAddress          : 192.168.1.100
                # PingSucceeded          : True
                # PingReplyDetails (RTT) : 50 ms
                # TcpTestSucceeded       : False
                # Checking the endpoint
                $result = Test-NetConnection -ComputerName "$Endpoint.$Region.amazonaws.com" -Port 443 -ErrorAction Ignore
                Write-Log -Message "Remote URL: $($result.ComputerName)"
                Write-Log -Message "Remote Address: $($result.RemoteAddress)"
                Write-Log -Message "Remote Port: $($result.RemotePort)"
                Write-Log -Message "Interface Alias: $($result.InterfaceAlias)"
                Write-Log -Message "Source Address: $($result.SourceAddress.IPAddress)"
                Write-Log -Message "PingSucceeded: $($result.PingSucceeded)"
                Write-Log -Message "Ping Reply Details: $($result.PingReplyDetails)"
                Write-Log -Message "Tcp Test Succeeded: $($result.TcpTestSucceeded)"
                # Check if the connection is successful or not
                if ($result.TcpTestSucceeded -eq "True" ) {
                    $value = "Pass"
                    $note = "Endpoint IP address is $($result.RemoteAddress.IPAddressToString)"
                    Write-Log -Message "$Endpoint.$Region.amazonaws.com is reachable via port 443. Endpoint IP address is $($result.RemoteAddress.IPAddressToString)"
                }
                else {
                    $value = "Fail"
                    $note = "Please make sure the TCP connection to the endpoint $Endpoint.$Region.amazonaws.com for the TCP port 443 is accessible. Endpoint IP address is $($result.RemoteAddress.IPAddressToString)"
                    Write-Log -Message "$Endpoint.$Region.amazonaws.com is not reachable via port 443. Endpoint IP address is $($result.RemoteAddress.IPAddressToString)" -LogLevel "ERROR"
                }
            }
            catch {
                Write-Log -Message "Failed..." -LogLevel "ERROR"
                Write-Log -Message "$($_)" -LogLevel "ERROR"
                $value = "Fail"
                $note = "Please make sure the TCP connection to the endpoint $Endpoint.$Region.amazonaws.com for the TCP port 443 is accessible"
            }
        }
    
        else {
            $value = "Skip"
            $note = "This test skipped since EC2 instance metadata is not accessible and the instance is not configured as Managed(hybrid) Instance."
            Write-Log -Message "The $check check skipped since the region information in the EC2 instance metadata is not accessible or under the Managed(hybrid) Instance registration file" -LogLevel "ERROR"
        }
    }
    

    end {
        return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
    }
}