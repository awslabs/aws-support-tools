# Pester

Describe "Get-InstanceID" {
    BeforeAll {
        Write-Host 'This test assume there is an access to the instance metadateand.' -BackgroundColor Yellow -ForegroundColor Black
    }

    Context "Calling Get-InstanceID" {
        It 'When returning a valid value for Instance ID' {
            $metadatainfo = New-MetadataToken
            $output = Get-InstanceID -Token $metadatainfo[1]
            
            $output | Should -Match 'i-\b[0-9,a-z]{17}\b'
        }

        It 'When Metadata is not reachable' {
            $output = Get-InstanceID -Token "abcdef0123456789"
                
            $output | Should -Be $null
        }  
    } 
    AfterAll {    
    }
}



