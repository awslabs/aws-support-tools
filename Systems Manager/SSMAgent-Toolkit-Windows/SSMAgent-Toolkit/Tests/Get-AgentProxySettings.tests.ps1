# Pester

Describe "Get-AgentProxySettings" {
    BeforeAll {
        Write-Host 'This test assume the SSM agent is install.' -BackgroundColor Yellow -ForegroundColor Black
        New-Item -Path TestRegistry:\ -Name AgentProxySettings
        $Check = "SSM Agent Proxy Setting"
    }
  
    Context "Calling Get-AgentProxySettings" {
        It 'When no proxy is configure' {
            $output = Get-AgentProxySettings -Key TestRegistry:\AgentProxySettings
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "N/A"
            $output.Note | Should -Be "There is no proxy setting for SSM Agent"
        }

        It 'When proxy is configure' {
            $ProxyValue = @("http_proxy=192.168.1.1:88", "no_proxy=169.254.169.254")
            New-ItemProperty -Path "TestRegistry:\AgentProxySettings" -Name "Environment" -Value $ProxyValue -PropertyType MultiString

            $output = Get-AgentProxySettings -Key TestRegistry:\AgentProxySettings
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "$($ProxyValue[0]) $($ProxyValue[1])"
            $output.Note | Should -Be "SSM Agent configured with proxy settings"
        }       
        
        It 'When skipping Get-AgentProxySettings' {
            $output = Get-AgentProxySettings -Skip
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the service is not available"
        }
    } 
    AfterAll {
        Remove-ItemProperty -Path "TestRegistry:\AgentProxySettings" -Name "Environment"
        Remove-Item -Path TestRegistry:\AgentProxySettings
    }
}