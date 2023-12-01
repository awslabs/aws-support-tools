# Pester

Describe "Get-IEProxySetting" {
    BeforeAll {
        New-Item -Path TestRegistry:\ -Name IEProxySettings
        $check = "LocalSystem account user Internet Explorer proxy"
    }

    Context "Calling Get-IEProxySetting" {
        It 'When no proxy set, ProxyEnable does not exist' {
            $output = Get-IEProxySetting -Key TestRegistry:\IEProxySettings

            $output.check | Should -Be $check
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. there is no ProxyServer configured."
        }

        It 'When no proxy set, ProxyEnable equal 0' {
            New-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyEnable" -value 0

            $output = Get-IEProxySetting -Key TestRegistry:\IEProxySettings

            $output.check | Should -Be $check
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. there is no ProxyServer configured."
        }

        It 'When only ProxyServer is set' {
            $ProxyServer = "https://192.168.1.1:88"

            New-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyServer" -value $ProxyServer
            Set-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyEnable" -value 1

            $output = Get-IEProxySetting -Key TestRegistry:\IEProxySettings

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "Current IE proxy settings for LocalSystem account is $ProxyServer ProxyServer, and  as ProxyOverride list. PowerShell would use these settings"
        }

        It 'When both ProxyServer and ProxyOverride are set' {
            $ProxyServer = "https://192.168.1.1:88"
            $ProxyOverride = "169.254.169.254:88"

            New-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyOverride" -value $ProxyOverride

            $output = Get-IEProxySetting -Key TestRegistry:\IEProxySettings

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "Current IE proxy settings for LocalSystem account is $ProxyServer ProxyServer, and $ProxyOverride as ProxyOverride list. PowerShell would use these settings"
        }

        It 'When only ProxyServer is set' {
            $ProxyOverride = "169.254.169.254:88"

            Remove-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyServer"

            $output = Get-IEProxySetting -Key TestRegistry:\IEProxySettings

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "Current IE proxy settings for LocalSystem account is  ProxyServer, and $ProxyOverride as ProxyOverride list. PowerShell would use these settings"
        }

        It 'When skipping Get-IEProxySetting' {
            $output = Get-IEProxySetting -Skip

            $output.check | Should -Be $check
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. Skipped."
        }
    }
    AfterAll {
        Remove-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyOverride"
        Remove-ItemProperty -Path "TestRegistry:\IEProxySettings" -Name "ProxyEnable"
        Remove-Item -Path TestRegistry:\IEProxySettings
    }
}