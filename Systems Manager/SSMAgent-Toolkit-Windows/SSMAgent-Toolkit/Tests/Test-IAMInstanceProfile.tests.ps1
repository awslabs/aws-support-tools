<#
  .Synopsis
    Paster unit test to test Test-IAMInstanceProfile function.
  .Description
    This test assume there is an access to the instance metadata and have a profile attached with "SSMInstanceProfile" as a name.
#>

Describe "Test-IAMInstanceProfile" {
    BeforeAll {
        Write-Host 'This test assume there is an access to the instance metadata and have a profile attached with "SSMInstanceProfile" as a name.' -BackgroundColor Yellow -ForegroundColor Black
        $Check = "IAM instance profile"
    }
    Context "Calling Test-IAMInstanceProfile" {
        It 'IAM instance profile "SSMInstanceProfile" exist' {
            $metadatainfo = New-MetadataToken
            $output = Test-IAMInstanceProfile -Token $metadatainfo[1]
            $IAMInstanceProfile = "SSMInstanceProfile"
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be $IAMInstanceProfile
            $output.Note | Should -Be "IAM instance profile $IAMInstanceProfile is attached to the instance"
        }

        It 'Metadata is not accessible - Skip' {           
            $output = Test-IAMInstanceProfile -Token "abcdef0123456789" -NoMetadataAccess
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the EC2 instance metadata is not accessible"
        }

        It 'Instance registered as hybrid instance - Skip' {
            $output = Test-IAMInstanceProfile -Token "abcdef0123456789" -ManagedInstance
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since this server configured as Managed(hybrid) Instance"
        }

        It 'IAM instance profile is not attached to the instance' {
            $output = Test-IAMInstanceProfile -Token "abcdef0123456789"
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "N/A"
            $output.Note | Should -Be "Please make sure IAM Role is attach to the instance,Stop and start the instance"
        }
    } 
    AfterAll {        
    }
}