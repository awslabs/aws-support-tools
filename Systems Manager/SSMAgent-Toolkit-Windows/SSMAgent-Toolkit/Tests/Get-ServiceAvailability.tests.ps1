# Pester

Describe "Get-ServiceAvailability" {
    BeforeAll {
        $Check = "Amazon SSM agent service running"
        Write-Host 'This test assume the SSM Agent installed.' -BackgroundColor Yellow -ForegroundColor Black
    }

    Context "Calling Get-ServiceAvailability" {
        It 'When Service exist' {
            $output = Get-ServiceAvailability -ServiceName "AmazonSSMAgent"
                
            $output[0] | Should -Be 1
            $output[1] | Should -Be "Running"
        }

        It 'When the service does not exist' {
            $output = Get-ServiceAvailability -ServiceName "AmazonSSMAgentx"
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Fail"
            $output.Note | Should -Be "Please make sure the SSM agent is installed"
        }  
    } 
    AfterAll {    
    }
}