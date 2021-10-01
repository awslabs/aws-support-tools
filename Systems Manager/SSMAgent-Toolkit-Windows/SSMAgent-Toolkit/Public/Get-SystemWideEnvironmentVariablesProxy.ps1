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
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-SystemWideEnvironmentVariablesProxy {
    [CmdletBinding()]
    param (
        [String]$Key = "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment", #https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables
        [Switch]$Skip
    )
    $check = "System-wide environment variable proxy"
    Write-Log -Message "New check....."
    Write-Log -Message "$check"
    
    Write-Log -Message "Checking System-wide environment variable proxy settings from registry location $Key."
    Write-Log -Message "For more information check - https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables."
    Write-Log -Message "System-wide environment variable proxy mainly used by SSM Agent to connect to the endpoints"
    if (-not ($Skip)) { 
        $http_proxy_check = New-ProxyOutput -Path $Key -Value 'http_proxy' -SettingName $check
        $https_proxy_check = New-ProxyOutput -Path $Key -Value 'https_proxy' -SettingName $check
        $no_proxy_check = New-ProxyOutput -Path $Key -Value 'no_proxy' -SettingName $check

        If (($no_proxy_check[0] -eq $false) -and ($https_proxy_check[0] -eq $false) -and ($http_proxy_check[0] -eq $false)) {
            $value = "N/A"
            $note = "There is no http_proxy, https_proxy or no_proxy configured"
        }
        else {
            $value = $http_proxy_check[1] + ". " + $https_proxy_check[1] + ". " + $no_proxy_check[1]
            $note = $http_proxy_check[2] + ". " + $https_proxy_check[2] + ". " + $no_proxy_check[2]
        }
    }
    else {
        $value = "Skip"
        $note = "This test skipped since the service is not available"
        Write-Log -Message "The System-wide environment variable proxy check skipped since the service is not available" -LogLevel "WARN"
    }

    return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}