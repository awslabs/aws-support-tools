# Pester

Describe "Test-HybridRegistration" {
    BeforeAll {
        $ManagedInstanceID = "mi-abcdef01234567890"
        $Region = "us-east-1"
        $Check = "Managed(hybrid) Instance Registration"

        #create a here-string and write the contents to the test drive
        @"
{
    "ManagedInstanceID":"$ManagedInstanceID",
    "Region":"$Region"
}
"@ | Set-Content -Path TestDrive:\testregistration
    }

    Context "Calling Test-HybridRegistration" {
        It 'When RegistrationFile exist' {
            $output = Test-HybridRegistration -RegistrationFilePath TestDrive:\testregistration
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "ManagedInstanceID = $ManagedInstanceID, Region = $Region"
        }

        It 'When RegistrationFile does not exist' {
            $output = Test-HybridRegistration -RegistrationFilePath TestDrive:\testregistrationx
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "The instance is not configured as Managed(hybrid) Instance. Metadata will be used to get the InstanceId and Region"
        }  
    } 
    AfterAll {    
        Remove-Item -Path TestDrive:\testregistration
    }
}