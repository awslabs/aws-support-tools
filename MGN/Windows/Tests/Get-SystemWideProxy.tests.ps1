# Pester

Describe "Get-SystemWideProxy" {
    BeforeAll {
        Write-Information "This test will set Winhttp proxy and reset it to default"
        $check = "WinHTTP system-wide proxy"

        $command = cmd /C "netsh winhttp show proxy"
        $value = "$command"
        Write-Information "The current output of - netsh winhttp show proxy - is: " $value
        $confirmation = Read-Host "This test will set Winhttp proxy and reset it to default. Are you sure You Want To Proceed [y/n]"
        if ($confirmation -ne 'y') {
            exit
        }

    }
    Context "Calling Get-SystemWideProxy" {
        It 'With set value' {

            cmd /C 'netsh winhttp set proxy proxy-server="http=myproxy;https=sproxy:88" bypass-list="*.foo.com"'

            $output = Get-SystemWideProxy

            $output.check | Should -Be $check
            $output.value | Should -Be '[YELLOW]'
            $output.Action | Should -Be 'Current WinHTTP system-wide proxy settings for LocalSystem account is http=myproxy;https=sproxy:88 as ProxyServer(s), and *.foo.com as Bypass list. Windows Update service would use these settings'
        }

        It 'With no proxy' {

            cmd /C 'netsh winhttp reset proxy'

            $output = Get-SystemWideProxy

            $output.check | Should -Be $check
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. There is no ProxyServer(s) configured for WinHTTP system-wide proxy."
        }

        It 'When skipping Get-SystemWideProxy' {
            $output = Get-SystemWideProxy -Skip

            $output.check | Should -Be $check
            $output.value | Should -Be "[GREEN]"
            $output.Action | Should -Be "No action required. Skipped."
        }
    }
    AfterAll {

    }
}