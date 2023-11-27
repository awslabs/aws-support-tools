# Pester

Describe "Get-SystemWideEnvironmentVariablesProxy" {
    BeforeAll {
        New-Item -Path TestRegistry:\ -Name SystemWideEnvironmentVariablesProxy
        $check = "System-wide environment variable proxy"
    }

    Context "Calling Get-SystemWideEnvironmentVariablesProxy" {
        It 'When no proxy set' {
            $output = Get-SystemWideEnvironmentVariablesProxy -Key TestRegistry:\SystemWideEnvironmentVariablesProxy -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. There is no http_proxy, https_proxy or no_proxy configured."
        }

        It 'When only http_proxy is set' {
            $HttpProxy = "http://192.168.1.1:88"

            New-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "http_proxy" -value $HttpProxy

            $output = Get-SystemWideEnvironmentVariablesProxy -Key TestRegistry:\SystemWideEnvironmentVariablesProxy -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "http_proxy = $HttpProxy. https_proxy = N/A. no_proxy = N/A."
        }

        It 'When only http_proxy and https_proxy are set' {
            $HttpProxy = "http://192.168.1.1:88"
            $HttpsProxy = "https://192.168.1.1:88"

            New-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "https_proxy" -value $HttpsProxy

            $output = Get-SystemWideEnvironmentVariablesProxy -Key TestRegistry:\SystemWideEnvironmentVariablesProxy -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "http_proxy = $HttpProxy. https_proxy = $HttpsProxy. no_proxy = N/A."
        }

        It 'When http_proxy, https_proxy and no_proxy are set' {
            $HttpProxy = "http://192.168.1.1:88"
            $HttpsProxy = "https://192.168.1.1:88"
            $NoProxy = "169.254.169.254:88"

            New-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "no_proxy" -value $NoProxy

            $output = Get-SystemWideEnvironmentVariablesProxy -Key TestRegistry:\SystemWideEnvironmentVariablesProxy -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "http_proxy = $HttpProxy. https_proxy = $HttpsProxy. no_proxy = $NoProxy."
        }

        It 'When only https_proxy and no_proxy are set' {
            $HttpsProxy = "https://192.168.1.1:88"
            $NoProxy = "169.254.169.254:88"

            Remove-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "http_proxy"

            $output = Get-SystemWideEnvironmentVariablesProxy -Key TestRegistry:\SystemWideEnvironmentVariablesProxy -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "http_proxy = N/A. https_proxy = $HttpsProxy. no_proxy = $NoProxy."
        }

        It 'When only https_proxy is set' {
            $HttpsProxy = "https://192.168.1.1:88"

            Remove-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "no_proxy"

            $output = Get-SystemWideEnvironmentVariablesProxy -Key TestRegistry:\SystemWideEnvironmentVariablesProxy -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "http_proxy = N/A. https_proxy = $HttpsProxy. no_proxy = N/A."
        }

        It 'When only no_proxy is set' {
            $NoProxy = "169.254.169.254:88"

            Remove-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "https_proxy"
            New-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "no_proxy" -value $NoProxy

            $output = Get-SystemWideEnvironmentVariablesProxy -Key TestRegistry:\SystemWideEnvironmentVariablesProxy -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "http_proxy = N/A. https_proxy = N/A. no_proxy = $NoProxy."
        }

        It 'When only http_Proxy and no_proxy are set' {
            $HttpProxy = "http://192.168.1.1:88"
            $NoProxy = "169.254.169.254:88"

            New-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "http_proxy" -value $HttpProxy

            $output = Get-SystemWideEnvironmentVariablesProxy -Key TestRegistry:\SystemWideEnvironmentVariablesProxy -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[YELLOW]"
            $output.Action | Should -Be "http_proxy = $HttpProxy. https_proxy = N/A. no_proxy = $NoProxy."
        }

        It 'When skipping Get-SystemWideEnvironmentVariablesProxy' {
            $output = Get-SystemWideEnvironmentVariablesProxy -Skip -ConsoleOnly $true

            $output.check | Should -Be $check
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. Skipped."
        }
    }
    AfterAll {
        Remove-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "no_proxy"
        Remove-ItemProperty -Path "TestRegistry:\SystemWideEnvironmentVariablesProxy" -Name "http_proxy"
        Remove-Item -Path TestRegistry:\SystemWideEnvironmentVariablesProxy
    }
}