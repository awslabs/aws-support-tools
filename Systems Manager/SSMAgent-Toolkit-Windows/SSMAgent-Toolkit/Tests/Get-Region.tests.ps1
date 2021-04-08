# Pester

Describe "Get-Region" {
    BeforeAll {
        Write-Host 'This test assume there is an access to the instance metadate.' -BackgroundColor Yellow -ForegroundColor Black
    }

    Context "Calling Get-Region" {
        It 'When returning a valid value for the region' {
            $metadatainfo = New-MetadataToken
            $output = Get-Region -Token $metadatainfo[1]
            
            $output | Should -BeIn @("us-east-2","us-east-1","us-west-1","us-west-2","af-south-1","ap-east-1","ap-south-1","ap-northeast-3","ap-northeast-2","ap-southeast-1","ap-southeast-2","ap-northeast-1","ca-central-1","cn-north-1","cn-northwest-1","eu-central-1","eu-west-1","eu-west-2","eu-south-1","eu-west-3","eu-north-1","me-south-1","sa-east-1")
        }

        It 'When Metadata is not reachable' {
            $output = Get-Region -Token "abcdef0123456789"
                
            $output | Should -Be 0
        }  
    } 
    AfterAll {    
    }
}