<#
  .Synopsis
    Check the value of System Environment Variables proxy value configured under registry.
  .Description
    This is a public function used to check the value of System Environment Variables proxy value configured under registry path "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment".
  .Example
    Get-SystemWideEnvironmentVariablesProxy
  .INPUTS
    Skip = Default is false. This script will be skipped if the agent is not installed.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-SystemWideEnvironmentVariablesProxy {
    [CmdletBinding()]
    param (
        [String]$Skip = $false
    )
    $check = "System-wide environment variable proxy"
    Write-Log -Message "New check....."
    Write-Log -Message "$check"

    $key = "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" #https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables

    
    Write-Log -Message "Checking System-wide environment variable proxy settings from registry location $key."
    Write-Log -Message "For more information check - https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables."
    Write-Log -Message "System-wide environment variable proxy mainly used by SSM Agent to connect to the endpoints"
    if ($Skip -ne $true) {
        #Check if there is a http_proxy value
        If (-not (Test-RegistryValue -Path $key -Value 'http_proxy')) {
            $http_proxy_check = 0
            $note = "There is no http_proxy configured for System-wide environment variable proxy."
            Write-Log -Message "There is no http_proxy configured for System-wide environment variable proxy."
        }
        else {
            $http_proxy_value = (Get-Item -Path $key).GetValue("http_proxy")
            $note = "http_proxy = $http_proxy_value."
            $value = "http_proxy = $http_proxy_value."
            Write-Log -Message "Checking System-wide environment variable proxy.http_proxy = $http_proxy_value." -LogLevel "WARN"
        }

        #Check if there is a https_proxy value
        If (-not (Test-RegistryValue -Path $key -Value 'https_proxy')) {
            $https_proxy_check = 0
            $note += " There is no https_proxy configured for System-wide environment variable proxy."
            Write-Log -Message "There is no https_proxy configured for System-wide environment variable proxy."
        }
        else {
            $https_proxy_value = (Get-Item -Path $key).GetValue("https_proxy")
            $note += " https_proxy = $https_proxy_value."
            $value += " https_proxy = $https_proxy_value."
            Write-Log -Message "Checking System-wide environment variable proxy.https_proxy = $https_proxy_value." -LogLevel "WARN"
        }

        #Check if there is a no_proxy value
        If (-not (Test-RegistryValue -Path $key -Value 'no_proxy')) {
            $no_proxy_check = 0
            $note += " There is no no_proxy configured for System-wide environment variable proxy."
            Write-Log -Message "There is no no_proxy configured for System-wide environment variable proxy."
        }
        else {
            $no_proxy_value = (Get-Item -Path $key).GetValue("no_proxy")
            $note += " no_proxy = $no_proxy_value."
            $value += " no_proxy = $no_proxy_value."
            Write-Log -Message "Checking System-wide environment variable proxy.no_proxy = $no_proxy_value." -LogLevel "WARN"
        }

        If (($no_proxy_check -eq 0) -and ($https_proxy_check -eq 0) -and ($http_proxy_check -eq 0)) {
            $value = "N/A"
            $note = "There is no http_proxy, https_proxy or no_proxy configured for System-wide environment variable proxy."
        }
    }
    else {
        $value = "Skip"
        $note = "This test skipped since the service is not available"
        Write-Log -Message "The System-wide environment variable proxy check skipped since the service is not available" -LogLevel "WARN"
    }

    return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}