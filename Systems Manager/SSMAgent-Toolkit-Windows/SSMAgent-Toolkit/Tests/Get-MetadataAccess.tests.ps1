# Pester

Describe "Get-MetadataAccess" {
    BeforeAll {
        Write-Host 'This test assume there is an access to the instance metadata.' -BackgroundColor Yellow -ForegroundColor Black
        $Region = "us-east-1"
        $EC2InstanceID = "i-abcdef01234567890"
        $Check = "EC2 instance metadata accessible"
    }

    Context "Calling Get-MetadataAccess" {
        It 'When Metadata is accessible' {
            $output = Get-MetadataAccess -StatusCode 200 -Region $Region -EC2InstanceID $EC2InstanceID
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "EC2 InstanceID = $EC2InstanceID, Region = $Region"
        }

        It 'When Metadata is accessible is accessible' {
            $output = Get-MetadataAccess -StatusCode 201 -Region $Region -EC2InstanceID $EC2InstanceID
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Fail"
            $output.Note | Should -Be "Please make sure there is a route to 169.254.169.254 via primary interface in the OS route table"
        }  

        It 'When skipping Get-MetadataAccess' {
            $output = Get-MetadataAccess -StatusCode 201 -Region $Region -EC2InstanceID $EC2InstanceID -ManagedInstance
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since this server configured as Managed(hybrid) Instance"
        }
    } 
    AfterAll {
        
    }
}