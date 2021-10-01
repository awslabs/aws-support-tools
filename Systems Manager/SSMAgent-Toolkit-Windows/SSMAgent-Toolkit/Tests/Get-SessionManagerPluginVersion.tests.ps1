# Pester

Describe "Get-SessionManagerPluginVersion" {
    BeforeAll {
        Write-Host 'This test assume the Session Manager Plugin install and the instance have access to the internet.' -BackgroundColor Yellow -ForegroundColor Black            
        $LatestVersionUrl = "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/VERSION"
        $ProgramFiles = [Environment]::GetEnvironmentVariable("ProgramFiles")
        $SessionManagerPluginVersionPath = "$ProgramFiles\Amazon\SessionManagerPlugin\VERSION"
        $CurrentSessionManagerPluginVersion = Get-Content $SessionManagerPluginVersionPath
        $LatestSessionManagerPluginVersion = Invoke-WebRequest -Uri $LatestVersionUrl

        #create a here-string and write the contents to the testdrive
        "1.1.26.0" | Set-Content -Path TestDrive:\testrandomversion
    }
    Context "Calling Get-SessionManagerPluginVersion" {
        It 'When both the Session Manager Plugin exist and the instance can reach the internet with latest version - Pass' {
            $output = Get-SessionManagerPluginVersion
                
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "The install and the latest Session Manager Plugin version is $LatestSessionManagerPluginVersion"
        }

        It 'When the install Session Manager Plugin and latest versions does not match - Pass' {
            $output = Get-SessionManagerPluginVersion -SessionManagerPluginVersionPath TestDrive:\testrandomversion
                
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "The install Session Manager Plugin version is 1.1.26.0, the latest is $LatestSessionManagerPluginVersion"
        }

        It 'With no internet access to check the latest version from the S3 bucket - Pass' {
            $output = Get-SessionManagerPluginVersion -LatestVersionUrl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/VERSIONx"
            
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "The install Session Manager Plugin version is $CurrentSessionManagerPluginVersion"
        }

        It 'When session manager plugin is not installed - Skip' {
            $output = Get-SessionManagerPluginVersion -SessionManagerPluginVersionPath "\Fakefolder\fakex\fake"
            
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the Session Manager Plugin is not is not installed"
        }

        It 'When skipping since the SSM Agent is not installed - Skip' {
            $output = Get-SessionManagerPluginVersion -Skip
            
            $output.Check | Should -Be "Session Manager Plugin version"
            $output.Value | Should -Be "Skip"
            $output.Note | Should -Be "This test skipped since the SSM Agent is not installed"
        }
    } 
    AfterAll {
        Remove-Item -Path TestDrive:\testrandomversion        
    }
}