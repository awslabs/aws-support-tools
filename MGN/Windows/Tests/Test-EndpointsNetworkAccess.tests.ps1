# Pester

Describe "Test-EndpointsNetworkAccess" {
    BeforeAll {
        Write-Output 'This test assume the instance have access to the internet or ssm endpoint.'
        $Endpoint = "mgn"
        $Region = "us-east-1"
        $result = Test-NetConnection -ComputerName "$Endpoint.$Region.amazonaws.com" -Port 443 -ErrorAction Ignore
    }
    Context "Calling Test-EndpointsNetworkAccess" {
        It 'With existing endpoint - Pass' {
            $output = Test-EndpointsNetworkAccess -Endpoint "$Endpoint.$region.amazonaws.com"

            $output.check | Should -Be "$Endpoint.$Region.amazonaws.com"
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. Endpoint IP address is $($result.RemoteAddress.IPAddressToString)."
        }

        It 'With fake endpoint - Fail' {
            $Endpoint = "mgn1"

            $output = Test-EndpointsNetworkAccess -Endpoint mgn1.$region.amazonaws.com

            $output.check | Should -Be "$Endpoint.$Region.amazonaws.com"
            $output.value | Should -Be "[RED]"
            $output.Action | Should -Be "Please make sure the TCP connection to the endpoint $Endpoint.us-east-1.amazonaws.com for the TCP port 443 is accessible. Endpoint IP address is ."
        }

        It 'When skipping Test-EndpointsNetworkAccess' {
            $output = Test-EndpointsNetworkAccess -Endpoint mgn.$region.amazonaws.com -Skip

            $output.check | Should -Be "$Endpoint.$Region.amazonaws.com"
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. Skipped."
        }
    }
    AfterAll {

    }
}