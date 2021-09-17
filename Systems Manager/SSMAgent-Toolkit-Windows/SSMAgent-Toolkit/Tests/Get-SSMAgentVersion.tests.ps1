# Pester

Describe "Get-SSMAgentVersion" {
    BeforeAll {
        $Region = "us-east-1"
        $LatestVersionUrl = "https://s3.$Region.amazonaws.com/amazon-ssm-$Region/latest/VERSION"
        $ProgramFiles = [Environment]::GetEnvironmentVariable("ProgramFiles")
        $SSMAgentPath = "$ProgramFiles\Amazon\SSM\amazon-ssm-agent.exe"
        $CurrentSSMAgentVersion = Invoke-Expression "& `"$SSMAgentPath`" -version"
        $LatestSSMAgentVersion = Invoke-WebRequest -Uri $LatestVersionUrl
        Write-Host 'This test assume the SSM Agent install and the instance have access to the internet.' -BackgroundColor Yellow -ForegroundColor Black            
    }
    Context "Calling Get-SSMAgentVersion" {
        It 'When both the Agent and the instance can reach the internet - Pass' {
            $output = Get-SSMAgentVersion -Region $Region
                
            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "$CurrentSSMAgentVersion, the latest agent version in $Region is $LatestSSMAgentVersion."
        }

        It 'With no Region or internet access - Pass' {
            $output = Get-SSMAgentVersion
            
            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "$CurrentSSMAgentVersion"
        }

        It 'When skipping Get-SSMAgentVersion' {
            $output = Get-SSMAgentVersion -Skip
            
            $output.Check | Should -Be "SSMAgent Version"
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the SSM Agent is not installed."
        }
    } 
    AfterAll {
        
    }
}