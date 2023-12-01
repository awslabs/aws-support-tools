<#
  .Synopsis
    Check the value of Internet Explorer proxy value configured under registry.
  .Description
    This is a public function used to check the value of Internet Explorer proxy value configured under registry path "KEY_USERS\S-1-5-18\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings".
  .Example
    Get-IEProxySetting
  .INPUTS
    Key = The path for the Internet Explorer proxy in the registry. Default value: "Registry::HKEY_USERS\.DEFAULT\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings".
    Skip = Switch to skip this function if the agent is not installed.
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Note "$Action"
#>
Function Get-IEProxySetting {
  [CmdletBinding()]
  param (
    [String]$ProxySettingsKey = "Registry::HKEY_USERS\.DEFAULT\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings",
    [Switch]$Skip
  )

  $check = "LocalSystem account user Internet Explorer proxy"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  Write-Log -Message "Checking IE proxy settings from registry location $ProxySettingsKey."
  Write-Log -Message "For more information check - https://docs.microsoft.com/en-us/troubleshoot/windows-server/identity/security-identifiers-in-windows."
  Write-Log -Message "IE proxy settings mainly used to enable PowerShell to have access to the internet (not Windows Update service)"
  Write-Log -Message "If the server behind a proxy and PowerShell via run command has a command which needs access to the internet would fail if there are no Internet Explorer proxy settings"

  if (-not ($Skip)) {
    try {
      If (((Get-Item -Path $ProxySettingsKey).GetValue("ProxyEnable") -eq 0) -Or (-not (Test-RegistryValue -Path $ProxySettingsKey -Value 'ProxyEnable'))) {
        $value = "[GREEN]"
        Write-Log -Message "The check ""$check"" output is $value"
        $Action = "No action required. there is no ProxyServer configured."
        Write-Log -Message $Action
      }
      else {
        $value = "[YELLOW]"
        Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
        $Action = "Current IE proxy settings for LocalSystem account is " + (Get-Item -Path $ProxySettingsKey).GetValue("ProxyServer") + " ProxyServer, and " + (Get-Item -Path $ProxySettingsKey).GetValue("ProxyOverride") + " as ProxyOverride list. PowerShell would use these settings"
        Write-Log -Message $Action -LogLevel "WARN"
      }
    }
    catch {
      Write-Log -Message "Failed..." -LogLevel "ERROR"
      $Action = "An error occurred when running Get-IEProxySetting."
      Write-Log -Message $Action -LogLevel "ERROR"
      Write-Log -Message "$($_)" -LogLevel "ERROR"
      $value = "[RED]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
    }
  }
  else {
    $value = "[GREEN]"
    Write-Log -Message "The check ""$check"" output is $value"
    $Action = "No action required. Skipped."
    Write-Log -Message $Action
  }
  if ($value -ne "[GREEN]") {
    $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
  }
  return Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
}
