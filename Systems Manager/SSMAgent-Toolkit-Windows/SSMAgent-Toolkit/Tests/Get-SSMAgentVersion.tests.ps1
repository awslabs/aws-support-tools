# Pester

Describe "Get-SSMAgentVersion" {
    BeforeAll {
        Write-Host 'This test assume the latest SSM Agent install and the instance have access to the internet.' -BackgroundColor Yellow -ForegroundColor Black
        $Region = "us-east-1"
        $LatestVersionUrl = "https://s3.$Region.amazonaws.com/amazon-ssm-$Region/latest/VERSION"
        $LatestSSMAgentVersion = Invoke-WebRequest -Uri $LatestVersionUrl
        $CurrentSSMAgentVersion = $LatestSSMAgentVersion
        New-Item -Path "TestRegistry:\" -Name "SSMAgent"
        $TestRegistryGUID = (Get-Item -Path "TestRegistry:\").Name -split "\\"
        $RegistryHive = "CurrentUser"
    }
    Context "Calling Get-SSMAgentVersion" {
        It 'When not able to retrieve the install agent''s version but able to get the latest version - Pass' {
            New-ItemProperty -Path "TestRegistry:\SSMAgent" -Name "DisplayName" -Value "Amazon SSM Agent"
            New-ItemProperty -Path "TestRegistry:\SSMAgent" -Name "DisplayVersion" -Value "0.0.0.0"
            $output = Get-SSMAgentVersion -Region $Region -RegistryHive $RegistryHive -RegistryPath "Software\\Pester\\$($TestRegistryGUID[3])"

            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "The latest agent version in $Region is $LatestSSMAgentVersion"            
        }

        It 'When both the Agent and the instance can reach the internet - Pass' {
            $output = Get-SSMAgentVersion -Region $Region
                
            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "The install and the latest agent version in $Region is $LatestSSMAgentVersion"
        }

        It 'When the install version is not the same as the latest version - Pass' {
            Set-ItemProperty -Path "TestRegistry:\SSMAgent" -Name "DisplayVersion" -Value "1.2.3.4"
            $output = Get-SSMAgentVersion -Region $Region -RegistryHive $RegistryHive -RegistryPath "Software\\Pester\\$($TestRegistryGUID[3])"
            
            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "The install SSM Agent version is 1.2.3.4, the latest in $Region is $LatestSSMAgentVersion"
        }

        It 'With no Region or internet access but able to retrieve the install version - Pass' {
            $output = Get-SSMAgentVersion
            
            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "The install SSM Agent version is $CurrentSSMAgentVersion"
        }

        It 'When no Region or internet accessible and not able o retrieve the install version - N/A' {
            Set-ItemProperty -Path "TestRegistry:\SSMAgent" -Name "DisplayVersion" -Value "0.0.0.0"
            $output = Get-SSMAgentVersion -RegistryHive $RegistryHive -RegistryPath "Software\\Pester\\$($TestRegistryGUID[3])"
            
            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "N/A"
            $output.Note | Should -Be "Unable to retrieve the install or latest SSM Agent version"
        }

        It 'When skipping Get-SSMAgentVersion - Skip' {
            $output = Get-SSMAgentVersion -Skip
            
            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the SSM Agent is not installed"
        }
    } 
    AfterAll {
        Remove-ItemProperty -Path TestRegistry:\SSMAgent -Name "DisplayName"
        Remove-ItemProperty -Path TestRegistry:\SSMAgent -Name "DisplayVersion"
        Remove-Item -Path TestRegistry:\SSMAgent        
    }
}