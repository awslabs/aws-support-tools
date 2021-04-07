# Pester

Describe "New-MetadataToken" {
    BeforeAll {
        Write-Host 'This test assume there is an access to the instance metadate.' -BackgroundColor Yellow -ForegroundColor Black
    }

    Context "Calling New-MetadataToken" {
        It 'When Metadata is reachable' {
            $output = New-MetadataToken

            $output[0] | Should -Be 200

        }

        It 'When Metadata is not reachable' {
            $output = New-MetadataToken -Uri "http://169.254.169.254/latest/apix/token"
                
            $output | Should -Be 0
        }  
    } 
    AfterAll {    
    }
}