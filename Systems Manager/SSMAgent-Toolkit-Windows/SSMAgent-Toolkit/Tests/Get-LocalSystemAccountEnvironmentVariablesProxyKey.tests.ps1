# Pester

Describe "Get-LocalSystemAccountEnvironmentVariablesProxy" {
    BeforeAll {
        New-Item -Path TestRegistry:\ -Name LocalSystemAccountEnvironmentVariablesProxy
        $Check = "LocalSystem account user environment variable proxy"
    }
  
    Context "Calling Get-LocalSystemAccountEnvironmentVariablesProxy" {
        It 'When no proxy set' {
            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Key TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "N/A"
            $output.Note | Should -Be "There is no http_proxy, https_proxy or no_proxy configured." 
        }

        It 'When only http_proxy is set' {
            $HttpProxy = "http://192.168.1.1:88"
            
            New-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "http_proxy" -Value $HttpProxy

            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Key TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "http_proxy = $HttpProxy. https_proxy = N/A. no_proxy = N/A."
            $output.Note | Should -Be "http_proxy = $HttpProxy. There is no https_proxy configured. There is no no_proxy configured."
        }   
        
        It 'When only http_proxy and https_proxy are set' {
            $HttpProxy = "http://192.168.1.1:88"
            $HttpsProxy = "https://192.168.1.1:88"
            
            New-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "https_proxy" -Value $HttpsProxy

            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Key TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "http_proxy = $HttpProxy. https_proxy = $HttpsProxy. no_proxy = N/A."
            $output.Note | Should -Be "http_proxy = $HttpProxy. https_proxy = $HttpsProxy. There is no no_proxy configured."
        } 

        It 'When http_proxy, https_proxy and no_proxy are set' {
            $HttpProxy = "http://192.168.1.1:88"
            $HttpsProxy = "https://192.168.1.1:88"
            $NoProxy = "169.254.169.254:88"
            
            New-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "no_proxy" -Value $NoProxy

            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Key TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "http_proxy = $HttpProxy. https_proxy = $HttpsProxy. no_proxy = $NoProxy."
            $output.Note | Should -Be "http_proxy = $HttpProxy. https_proxy = $HttpsProxy. no_proxy = $NoProxy."
        } 

        It 'When only https_proxy and no_proxy are set' {
            $HttpsProxy = "https://192.168.1.1:88"
            $NoProxy = "169.254.169.254:88"
            
            Remove-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "http_proxy"

            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Key TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "http_proxy = N/A. https_proxy = $HttpsProxy. no_proxy = $NoProxy."
            $output.Note | Should -Be "There is no http_proxy configured. https_proxy = $HttpsProxy. no_proxy = $NoProxy."
        } 

        It 'When only https_proxy is set' {
            $HttpsProxy = "https://192.168.1.1:88"
                        
            Remove-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "no_proxy"

            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Key TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "http_proxy = N/A. https_proxy = $HttpsProxy. no_proxy = N/A."
            $output.Note | Should -Be "There is no http_proxy configured. https_proxy = $HttpsProxy. There is no no_proxy configured."
        } 

        It 'When only no_proxy is set' {
            $NoProxy = "169.254.169.254:88"
            
            Remove-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "https_proxy"
            New-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "no_proxy" -Value $NoProxy

            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Key TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "http_proxy = N/A. https_proxy = N/A. no_proxy = $NoProxy."
            $output.Note | Should -Be "There is no http_proxy configured. There is no https_proxy configured. no_proxy = $NoProxy."
        }

        It 'When only http_Proxy and no_proxy are set' {
            $HttpProxy = "http://192.168.1.1:88"
            $NoProxy = "169.254.169.254:88"
            
            New-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "http_proxy" -Value $HttpProxy
            
            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Key TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "http_proxy = $HttpProxy. https_proxy = N/A. no_proxy = $NoProxy."
            $output.Note | Should -Be "http_proxy = $HttpProxy. There is no https_proxy configured. no_proxy = $NoProxy."
        }

        It 'When skipping Get-LocalSystemAccountEnvironmentVariablesProxy' {
            $output = Get-LocalSystemAccountEnvironmentVariablesProxy -Skip $true
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the service is not available"
        }
    } 
    AfterAll {
        Remove-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "no_proxy"
        Remove-ItemProperty -Path "TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy" -Name "http_proxy"
        Remove-Item -Path TestRegistry:\LocalSystemAccountEnvironmentVariablesProxy
    }
}