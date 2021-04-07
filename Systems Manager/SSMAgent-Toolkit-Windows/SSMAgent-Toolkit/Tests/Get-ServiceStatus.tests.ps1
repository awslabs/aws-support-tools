# Pester

Describe "Get-ServiceStatus" {
    BeforeAll {
        $ServiceName = "AmazonSSMAgent"
        $Check = "Amazon SSM agent service running"
        Write-Host 'This test assume the SSM Agent installed.' -BackgroundColor Yellow -ForegroundColor Black
    }

    Context "Calling Get-ServiceStatus" {
        It 'When AmazonSSMAgent service is Running' {
            $output = Get-ServiceStatus -ServiceName $ServiceName -ServiceStatus "Running"
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "$ServiceName service is in Running state. This is the desired state"
        }

        It 'When AmazonSSMAgent service is not Running' {
            $output = Get-ServiceStatus -ServiceName $ServiceName -ServiceStatus "Stopped"
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Fail"
            $output.Note | Should -Be "Please make sure the $ServiceName service is in Running state"
        }  
    } 
    AfterAll {        
    }
}