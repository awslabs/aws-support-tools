# Pester

Describe "Get-ServiceAccount" {
    BeforeAll {
        $ServiceName = "AmazonSSMAgent"
        $Check = "Amazon SSM service account"
        Write-Host 'This test assume the SSM Agent installed.' -BackgroundColor Yellow -ForegroundColor Black
    }

    Context "Calling Get-ServiceAccount" {
        It 'When the ServiceAccount for AmazonSSMAgent service is LocalSystem' {
            $output = Get-ServiceAccount -ServiceName $ServiceName
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "LocalSystem"
            $output.Note | Should -Be "This is the recommended account to use"
        }

        It 'When the ServiceAccount for AmazonSSMAgent service is not the LocalSystem' {
            $Service = Get-WmiObject Win32_Service -Filter "Name='$ServiceName'"
	        $Service.Change($null,$null,$null,$null,$null,$null,".\Guest","P@ssw0rd")

            $output = Get-ServiceAccount -ServiceName $ServiceName
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Not -Be "LocalSystem"
            $output.Note | Should -Be "It's recommended to use Local System Account"

            $Service.Change($null,$null,$null,$null,$null,$false,'LocalSystem','',$null,$null,$null) | Out-Null
        }  

        It 'When skipping Get-ServiceAccount' {
            $output = Get-ServiceAccount -ServiceName $ServiceName -Skip $true
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since The $ServiceName service is not available"
        }
    } 
    AfterAll {        
    }
}