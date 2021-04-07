# Pester

Describe "Test-EndpointsNetworkAccess" {
    BeforeAll {
        $Endpoint = "ssm"
        $Region = "us-east-1"
        $result = Test-NetConnection -ComputerName "$Endpoint.$Region.amazonaws.com" -Port 443 -ErrorAction Ignore
        Write-Host 'This test assume the instance have access to the internet or ssm endpoint.' -BackgroundColor Yellow -ForegroundColor Black
    }
    Context "Calling Test-EndpointsNetworkAccess" {
        It 'With existing endpoint - Pass' {
            $output = Test-EndpointsNetworkAccess -Endpoint $Endpoint -Region $Region
                
            $output.Check | Should -Be "$Endpoint.$Region.amazonaws.com accessible"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "Endpoint IP address is $($result.RemoteAddress.IPAddressToString)"
        }

        It 'With fake endpoint - Fail' {
            $Endpoint = "ssm1"
            
            $output = Test-EndpointsNetworkAccess -Endpoint "ssm1" -Region $Region
            
            $output.Check | Should -Be "$Endpoint.$Region.amazonaws.com accessible"
            $output.Value | Should -Be "Fail"
            $output.Note | Should -Be "Please make sure the TCP connection to the endpoint $Endpoint.us-east-1.amazonaws.com for the TCP port 443 is accessible. Endpoint IP address is "
        }

        It 'When skipping Test-EndpointsNetworkAccess' {
            $output = Test-EndpointsNetworkAccess -Endpoint "ssm" -Region $Region -Skip $true
            
            $output.Check | Should -Be "$Endpoint.$Region.amazonaws.com accessible"
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since EC2 instance metadata is not accessible and the instance is not configured as Managed(hybrid) Instance."
        }
    } 
    AfterAll {
        
    }
}