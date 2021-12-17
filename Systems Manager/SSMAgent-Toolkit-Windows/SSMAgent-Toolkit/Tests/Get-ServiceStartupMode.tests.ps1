# Pester

Describe "Get-ServiceStartupMode" {
    BeforeAll {
        Write-Host 'This test assume the SSM Agent installed. The startup mode set as Automatic' -BackgroundColor Yellow -ForegroundColor Black
        $ServiceName = "AmazonSSMAgent"
        $Check = "Amazon SSM service startup mode"
    }

    Context "Calling Get-ServiceStartupMode" {
        It 'When the Startup mode for AmazonSSMAgent service is Automatic' {
            $output = Get-ServiceStartupMode -ServiceName $ServiceName
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Auto"
            $output.Note | Should -Be "This is the recommended startup mode to use"
        }

        It 'When the Startup mode for AmazonSSMAgent service is not Automatic' {
            Set-Service -Name $ServiceName -StartupType "Manual"
            Start-Sleep -s 1

            $output = Get-ServiceStartupMode -ServiceName $ServiceName
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Manual"
            $output.Note | Should -Be "It's recommended to use Automatic startup mode"

            Set-Service -Name $ServiceName -StartupType "Automatic"
            Start-Sleep -s 1
        }  

        It 'When skipping Get-ServiceStartupMode' {
            $output = Get-ServiceStartupMode -ServiceName $ServiceName -Skip
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the $ServiceName service is not available"
        }
    } 
    AfterAll {        
    }
}