# Pester

Describe "Get-SystemWideProxy" {
    BeforeAll {
        $Check = "WinHTTP system-wide proxy" 

        $command = cmd /C "netsh winhttp show proxy"
        $value = "$command"
        Write-Host "The current output of - netsh winhttp show proxy - is: " $value
        Write-Host "This test will set Winhttp proxy and reset it to default" -BackgroundColor Yellow -ForegroundColor Black
        $confirmation = Read-Host "Are you sure You Want To Proceed [y/n]"
        if ($confirmation -ne 'y') {
            exit
        }

    }
    Context "Calling Get-SystemWideProxy" {
        It 'With set value' {

            cmd /C 'netsh winhttp set proxy proxy-server="http=myproxy;https=sproxy:88" bypass-list="*.foo.com"'
            
            $output = Get-SystemWideProxy
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be 'ProxyServer(s) = http=myproxy;https=sproxy:88. Bypass list = *.foo.com'
            $output.Note | Should -Be 'Current WinHTTP system-wide proxy settings for LocalSystem account is http=myproxy;https=sproxy:88 as ProxyServer(s), and *.foo.com as Bypass list. Windows Update service would use these settings.'
        }

        It 'With no proxy' {

            cmd /C 'netsh winhttp reset proxy'
                        
            $output = Get-SystemWideProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "N/A"
            $output.Note | Should -Be "There is no ProxyServer(s) configured for WinHTTP system-wide proxy. Note: This proxy settings mainly used to by Windows Update service"
        }

        It 'When skipping Get-SystemWideProxy' {
            $output = Get-SystemWideProxy -Skip
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the service is not available"
        }
    } 
    AfterAll {
        
    }
}