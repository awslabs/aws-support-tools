# Pester

Describe "Get-SessionManagerPluginVersion" {
    BeforeAll {
        $LatestVersionUrl = "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/VERSION"
        $ProgramFiles = [Environment]::GetEnvironmentVariable("ProgramFiles")
        $SessionManagerPluginVersionPath = "$ProgramFiles\Amazon\SessionManagerPlugin\VERSION"
        $CurrentSessionManagerPluginVersion = Get-Content $SessionManagerPluginVersionPath
        $LatestSessionManagerPluginVersion = Invoke-WebRequest -Uri $LatestVersionUrl
        Write-Host 'This test assume the Session Manager Plugin install and the instance have access to the internet.' -BackgroundColor Yellow -ForegroundColor Black            
    }
    Context "Calling Get-SessionManagerPluginVersion" {
        It 'When both the Session Manager Plugin and the instance can reach the internet - Pass' {
            $output = Get-SessionManagerPluginVersion
                
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "Session Manager Plugin version is $CurrentSessionManagerPluginVersion, the latest Session Manager Plugin version is $LatestSessionManagerPluginVersion."
        }

        It 'With no internet access to check the latest version from the S3 bucket - Pass' {
            $output = Get-SessionManagerPluginVersion -LatestVersionUrl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/VERSIONx"
            
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "Session Manager Plugin version is $CurrentSessionManagerPluginVersion"
        }

        It 'When session manager plugin is not installed' {
            $output = Get-SessionManagerPluginVersion -SessionManagerPluginVersionPath "\Fakefolder\fakex\fake"
            
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the Session Manager Plugin is not is not installed."
        }

        It 'When skipping since the SSM Agent is not installed' {
            $output = Get-SessionManagerPluginVersion -Skip
            
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the SSM Agent is not installed."
        }
    } 
    AfterAll {
        
    }
}