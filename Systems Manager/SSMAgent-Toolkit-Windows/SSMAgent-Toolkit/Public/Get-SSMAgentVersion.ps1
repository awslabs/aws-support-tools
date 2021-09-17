<#
  .Synopsis
    Check the installed and latest version of SSM Agent.
  .Description
    This is a public function used to check the SSM Agent version values for both installed and publically available.
  .Example
    Get-SSMAgentVersion
  .INPUTS
    N/A
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-SSMAgentVersion {
    [CmdletBinding()]
    param (
        [String]$Region,
        [Switch]$Skip
    ) 
  
    $check = "SSMAgent version"
    Write-Log -Message "New check....."
    Write-Log -Message "$check"

    if (-not ($Skip)) {
        $LatestVersionUrl = "https://s3.$Region.amazonaws.com/amazon-ssm-$Region/latest/VERSION"
        $ProgramFiles = [Environment]::GetEnvironmentVariable("ProgramFiles")
        $SSMAgentPath = "$ProgramFiles\Amazon\SSM\amazon-ssm-agent.exe"
        $CurrentSSMAgentVersion = Invoke-Expression "& `"$SSMAgentPath`" -version"
    
        Write-Log -Message "Checking the latest SSM agent from $LatestVersionUrl."
        Write-Log -Message "Checking the current agent version from $SSMAgentPath"
        Write-Log -Message "Current $CurrentSSMAgentVersion"
        $value = "Pass"
        $note = "$CurrentSSMAgentVersion"

        try {
            $LatestSSMAgentVersion = Invoke-WebRequest -Uri $LatestVersionUrl
            $note += ", the latest agent version in $Region is $LatestSSMAgentVersion."
        }
        catch {
            Write-Log -Message ("Unable to retrieve the latest SSM Agent version from $LatestVersionUrl. " + $($PSitem.ToString())) -LogLevel "ERROR"
        }
    }

    else {
        $value = "Skip"
        $note = "This test skipped since the SSM Agent is not installed."
        Write-Log -Message "The SSMAgent Version check skipped since the SSM Agent is not installed" -LogLevel "ERROR"
        Write-Log -Message "Installing and configuring SSM Agent on EC2 instances for Windows Server - https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-install-ssm-win.html" -LogLevel "INFO"
    }

    return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}