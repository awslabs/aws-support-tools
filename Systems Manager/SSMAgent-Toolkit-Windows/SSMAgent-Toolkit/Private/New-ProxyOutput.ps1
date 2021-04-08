<#
  .Synopsis
    Test if the proxy exist or not in the registry. 
  .Description
    This is a helper function to test registry value and whater if the key is available or not. The provide an output based on that results.
  .Example
    New-ProxyOutput -Path 'Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\AmazonSSMAgent' -Value 'Environment' -SettingName 'System-wide environment variable proxy'
  .INPUTS
    Path = The registry path 
    Value = The key to check on that path
    SettingName = The name of the test.
  .OUTPUTS                                                                            
    Return the value of the check, note and $false, $true whater the value does exist or not.
#>
function New-ProxyOutput {
  [CmdletBinding()]
  param (
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$Path,
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$Value,
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$SettingName
  )
  
  If (-not (Test-RegistryValue -Path $Path -Value $Value)) {
    $Message = "$Value = N/A."
    $Note = "There is no $Value configured."
    Write-Log -Message "There is no http_proxy configured for $SettingName."
    return $false, $Message, $note
  }
  else {
    $Output = (Get-Item -Path $Path).GetValue($Value)
    $Note = "$Value = $output."
    $Message = $note
    Write-Log -Message "For $SettingName. $Value = $Output." -LogLevel "WARN"
    return $true, $Message, $note
  }
  
}