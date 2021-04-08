<#
  .Synopsis
    Check the value of Local System Account Environment Variables proxy value configured under registry.
  .Description
    This is a public function used to check the value of Local System Account Environment Variables proxy value configured under registry path "HKEY_USERS\.DEFAULT\Environments".
  .Example
    Get-LocalSystemAccountEnvironmentVariablesProxy
  .INPUTS
    Skip = Default is false. This script will be skipped if the agent is not installed.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-LocalSystemAccountEnvironmentVariablesProxy {
    param (
        [String]$Key = "Registry::HKEY_USERS\.DEFAULT\Environment", #https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables
        [String]$Skip = $false
    )
    
    $check = "LocalSystem account user environment variable proxy"
    Write-Log -Message "New check....."
    Write-Log -Message "$check"

    Write-Log -Message "Checking LocalSystem account user environment variable proxy settings from registry location $key."
    Write-Log -Message "For more information check - https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables."
    Write-Log -Message "LocalSystem account user environment variable proxy mainly used by SSM Agent to connect to the endpoints"

    if ($Skip -ne $true) {
        $http_proxy_check = New-ProxyOutput -Path $Key -Value 'http_proxy' -SettingName $check
        $https_proxy_check = New-ProxyOutput -Path $Key -Value 'https_proxy' -SettingName $check
        $no_proxy_check = New-ProxyOutput -Path $Key -Value 'no_proxy' -SettingName $check

        If (($no_proxy_check[0] -eq $false) -and ($https_proxy_check[0] -eq $false) -and ($http_proxy_check[0] -eq $false)) {
            $value = "N/A"
            $note = "There is no http_proxy, https_proxy or no_proxy configured."
        }
        else {
            $value = $http_proxy_check[1] + " " + $https_proxy_check[1] + " " + $no_proxy_check[1]
            $note = $http_proxy_check[2] + " " + $https_proxy_check[2] + " " + $no_proxy_check[2]
        }
    }
    else {
        $value = "Skip"
        $note = "This test skipped since the service is not available"
        Write-Log -Message "The LocalSystem account user environment variable proxy check skipped since the service is not available" -LogLevel "WARN"
    }
    return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}