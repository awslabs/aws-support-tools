<#
  .Synopsis
    Check the value of System Environment Variables proxy value configured under registry.
  .Description
    This is a public function used to check the value of System Environment Variables proxy value configured under registry path "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment".
  .Example
    Get-SystemWideEnvironmentVariablesProxy
  .INPUTS
    Key = The path for the System Environment Variables proxy in the registry. Default value: "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment". Ref: https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables
    Skip = Switch to skip this function if the agent is not installed.
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Note "$Action"
#>
Function Get-SystemWideEnvironmentVariablesProxy {
  [CmdletBinding()]
  param (
    [String]$ProxyKey = "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment", #https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables
    [Switch]$Skip
  )
  $check = "System-wide environment variable proxy"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  Write-Log -Message "Checking System-wide environment variable proxy settings from registry location $ProxyKey."
  Write-Log -Message "For more information check - https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables."
  Write-Log -Message "System-wide environment variable proxy mainly used by MGN Agent to connect to the endpoints"
  if (-not ($Skip)) {
    try {
      $http_proxy_check = Set-ProxyOutput -Path $ProxyKey -Value 'http_proxy' -SettingName $check
      $https_proxy_check = Set-ProxyOutput -Path $ProxyKey -Value 'https_proxy' -SettingName $check
      $no_proxy_check = Set-ProxyOutput -Path $ProxyKey -Value 'no_proxy' -SettingName $check

      If (($no_proxy_check[0] -eq $false) -and ($https_proxy_check[0] -eq $false) -and ($http_proxy_check[0] -eq $false)) {
        $value = "[GREEN]"
        Write-Log -Message "The check ""$check"" output is $value"
        $Action = "No action required. There is no http_proxy, https_proxy or no_proxy configured."
        Write-Log -Message $Action
      }
      else {
        $value = "[YELLOW]"
        Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
        $Action = $http_proxy_check[1] + ". " + $https_proxy_check[1] + ". " + $no_proxy_check[1] + "."
        Write-Log -Message $Action -LogLevel "WARN"
      }
    }
    catch {
      Write-Log -Message "Failed..." -LogLevel "ERROR"
      $Action = "An error occurred when running Get-SystemWideEnvironmentVariablesProxy."
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