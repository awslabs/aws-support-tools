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
Function Get-ProxySetting {
  [CmdletBinding()]
  param (
    [String]$ieProxySettingsKey = "Registry::HKEY_USERS\.DEFAULT\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings",
    [String]$LocalSysAccountEnvVarProxyKey = "Registry::HKEY_USERS\.DEFAULT\Environment", #https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables
    [String]$sysWideEnvVarProxyKey = "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment", #https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables
    [Switch]$Skip
  )

  if (-not ($Skip)) {
    $outputIEProxySettings = Get-IEProxySetting -ProxySettingsKey $ieProxySettingsKey
    $outputSystemWideProxy = Get-SystemWideProxy
    $outputSystemWideEnvironmentVariablesProxy = Get-SystemWideEnvironmentVariablesProxy -ProxyKey $sysWideEnvVarProxyKey
    $outputLocalSystemAccountEnvironmentVariablesProxy = Get-LocalSystemAccountEnvironmentVariablesProxy -ProxyKey $LocalSysAccountEnvVarProxyKey
    if (($outputIEProxySettings.value -eq "[GREEN]") -and ($outputSystemWideProxy.value -eq "[GREEN]") -and ($outputSystemWideEnvironmentVariablesProxy.value -eq "[GREEN]") -and ($outputLocalSystemAccountEnvironmentVariablesProxy.value -eq "[GREEN]")) {
      $check = "Proxy Settings"
      $value = "[GREEN]"
      Write-Log -Message "The check ""$check"" output is $value"
      $Action = "No action required. There is no proxy settings configured."
      Write-Log -Message $Action
      $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
    }
  }
  else {
    $check = "Proxy Settings"
    $value = "[GREEN]"
    Write-Log -Message "The check ""$check"" output is $value"
    $Action = "No action required. Skipped."
    Write-Log -Message $Action
    $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
  }
}