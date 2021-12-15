<#
  .Synopsis
    Paster unit test to test Test-IAMInstanceProfileCredentialLastUpdate function.
  .Description
    This test assume there is an access to the instance metadata and have a profile attached with "SSMInstanceProfile" as a name.
#>

Describe "Test-IAMInstanceProfileCredentialLastUpdate" {
    BeforeAll {
        Write-Host 'This test assume there is an access to the instance metadata and have a IAM instance profile attached.' -BackgroundColor Yellow -ForegroundColor Black
        $Check = "IAM profile credential valid"

        $metadatainfo = New-MetadataToken
        $IAMinstanceprofile = Test-IAMInstanceProfile -Token $metadatainfo[1]
        $Uri = "http://169.254.169.254/latest/meta-data/iam/security-credentials/$($IAMinstanceprofile.Value)"
        [System.Collections.IDictionary]$Headers = @{"X-aws-ec2-metadata-token" = $metadatainfo[1] }
        $IAMMetadata = Invoke-RestMethod -Uri $Uri -Headers $Headers
        [DateTime]$LastUpdatedUTC = $IAMMetadata.LastUpdated
        [DateTime]$ExpirationUTC = $IAMMetadata.Expiration
    }
    Context "Calling Test-IAMInstanceProfileCredentialLastUpdate" {
        It 'IAM instance profile attached' {
            $output = Test-IAMInstanceProfileCredentialLastUpdate -Token $metadatainfo[1] -IAMInstanceProfile $IAMinstanceprofile.Value
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "IAM instance profile's credential is up to date. IAM credential Expiration timestamp is $ExpirationUTC UTC. The Last update is $LastUpdatedUTC UTC"
        }

        It 'Metadata is not accessible - Skip' {           
            $output = Test-IAMInstanceProfileCredentialLastUpdate -Token "abcdef0123456789" -IAMInstanceProfile "any" -NoMetadataAccess
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the EC2 instance metadata is not accessible"
        }

        It 'Instance registered as hybrid instance - Skip' {
            $output = Test-IAMInstanceProfileCredentialLastUpdate -Token "abcdef0123456789" -IAMInstanceProfile "any" -ManagedInstance
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since this server configured as Managed(hybrid) Instance"
        }

        It 'IAM instance profile is not attached to the instance' {
            $output = Test-IAMInstanceProfileCredentialLastUpdate -Token "abcdef0123456789" -IAMInstanceProfile "any" -NoIAMattached
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since there is no IAM instance profile attached to the instance"
        }

        It 'IAM instance profile is not attached to the instance' {
            Set-Date -Date (Get-Date).AddDays(1)
            $output = Test-IAMInstanceProfileCredentialLastUpdate -Token $metadatainfo[1] -IAMInstanceProfile $IAMinstanceprofile.Value         
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Fail"
            $output.Note | Should -Be "Credential Expiration time is in the past.Please make sure IAM Role is attach to the instance,Stop and start the instance"
        }
    } 
    AfterAll {
        Set-Date -Date (Get-Date).AddDays(-1)
    }
}


