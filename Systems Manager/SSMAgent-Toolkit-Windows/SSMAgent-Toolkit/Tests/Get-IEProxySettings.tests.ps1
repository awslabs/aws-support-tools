# Pester

Describe "Get-IEProxySettings" {
    BeforeAll {
        New-Item -Path TestRegistry:\ -Name IEProxySettings
        $Check = "LocalSystem account user Internet Explorer proxy"
    }
  
    Context "Calling Get-IEProxySettings" {
        It 'When no proxy set, ProxyEnable does not exist' {
            $output = Get-IEProxySettings -Key TestRegistry:\IEProxySettings
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "N/A"
            $output.Note | Should -Be "There is no ProxyServer configured" 
        }

        It 'When no proxy set, ProxyEnable equal 0' {
            New-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyEnable" -Value 0

            $output = Get-IEProxySettings -Key TestRegistry:\IEProxySettings
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "N/A"
            $output.Note | Should -Be "There is no ProxyServer configured" 
        }

        It 'When only ProxyServer is set' {
            $ProxyServer = "https://192.168.1.1:88"
            
            New-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyServer" -Value $ProxyServer
            Set-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyEnable" -Value 1

            $output = Get-IEProxySettings -Key TestRegistry:\IEProxySettings
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "ProxyServer = $ProxyServer. ProxyOverride list = "
            $output.Note | Should -Be "Current IE proxy settings for LocalSystem account is $ProxyServer ProxyServer, and  as ProxyOverride list. PowerShell would use these settings"
        }   
        
        It 'When both ProxyServer and ProxyOverride are set' {
            $ProxyServer = "https://192.168.1.1:88"
            $ProxyOverride = "169.254.169.254:88"
            
            New-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyOverride" -Value $ProxyOverride

            $output = Get-IEProxySettings -Key TestRegistry:\IEProxySettings
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "ProxyServer = $ProxyServer. ProxyOverride list = $ProxyOverride"
            $output.Note | Should -Be "Current IE proxy settings for LocalSystem account is $ProxyServer ProxyServer, and $ProxyOverride as ProxyOverride list. PowerShell would use these settings"
        } 

        It 'When only ProxyServer is set' {
            $ProxyOverride = "169.254.169.254:88"
            
            Remove-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyServer"

            $output = Get-IEProxySettings -Key TestRegistry:\IEProxySettings
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "ProxyServer = . ProxyOverride list = $ProxyOverride"
            $output.Note | Should -Be "Current IE proxy settings for LocalSystem account is  ProxyServer, and $ProxyOverride as ProxyOverride list. PowerShell would use these settings"
        } 

        It 'When skipping Get-IEProxySettings' {
            $output = Get-IEProxySettings -Skip
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the service is not available"
        }
    } 
    AfterAll {
        Remove-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyOverride"
        Remove-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyEnable"
        Remove-Item -Path TestRegistry:\IEProxySettings      
    }
}