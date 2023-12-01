<#
  .Synopsis
    Test if the proxy exist or not in the registry.
  .Description
    This is a helper function to test registry value and whether if the key is available or not. The provide an output based on that results.
  .Example
    Set-ProxyOutput -Path 'Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\AmazonSSMAgent' -Value 'Environment' -SettingName 'System-wide environment variable proxy'
  .INPUTS
    Path = The registry path
    Value = The key to check on that path
    SettingName = The name of the test.
  .OUTPUTS
    Return the value of the check, note and $false, $true whether the value does exist or not.
#>
function Set-ProxyOutput {
  [CmdletBinding()]
  param (
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$Path,
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$Value,
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$SettingName
  )

  $returnValue = Test-RegistryValue -Path $Path -Value $Value

   If ($returnValue[0]) {
    $output = (Get-Item -Path $Path).GetValue($Value)
    $Note = "$Value = $output"
    $Message = $note
    Write-Log -Message "For $SettingName. $Value = $output." -LogLevel "WARN" | Out-Null
    return $true, $Message, $Note
  }
  else {
    $Message = "$Value = N/A"
    $Note = "There is no $Value configured"
    Write-Log -Message "There is no $Value configured for $SettingName." | Out-Null
    return $false, $Message, $Note
  }
}