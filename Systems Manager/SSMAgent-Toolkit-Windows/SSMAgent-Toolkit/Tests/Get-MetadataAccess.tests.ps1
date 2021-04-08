# Pester

Describe "Get-MetadataAccess" {
    BeforeAll {
        $Region = "us-east-1"
        $EC2InstanceID = "i-abcdef01234567890"
        $Check = "EC2 instance metadata accessible"
        Write-Host 'This test assume there is an access to the instance metadate.' -BackgroundColor Yellow -ForegroundColor Black


        #$output | Should -Match 'i-\b[0-9,a-z]{17}\b'
        #$output | Should -BeIn @("us-east-2","us-east-1","us-west-1","us-west-2","af-south-1","ap-east-1","ap-south-1","ap-northeast-3","ap-northeast-2","ap-southeast-1","ap-southeast-2","ap-northeast-1","ca-central-1","cn-north-1","cn-northwest-1","eu-central-1","eu-west-1","eu-west-2","eu-south-1","eu-west-3","eu-north-1","me-south-1","sa-east-1")
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
            $output = Get-MetadataAccess -StatusCode 201 -Region $Region -EC2InstanceID $EC2InstanceID -ManagedInstance $true
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since this server configured as Managed(hybrid) Instance"
        }
    } 
    AfterAll {
        
    }
}