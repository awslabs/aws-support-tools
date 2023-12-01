<#
  .Synopsis
    Test registry value
  .Description
    This is a helper function to test registry value and whether if the key is available or not.
  .Example
    Test-RegistryValue -Path 'Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\AmazonSSMAgent' -Value 'Environment'
  .INPUTS
    Path = The registry path
    Value = The key to check on that path
  .OUTPUTS
    Return $true if exist or $false if not
#>
function Test-RegistryValue {
  [CmdletBinding()]
  param (
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$Path,
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$Value
  )

  try {
    if (-not [string]::IsNullOrEmpty((Get-ItemProperty -Path "$Path").$Value)) {
      Write-Log -Message "Registery Path =" -LogLevel "INFO" | Out-Null
      Write-Log -Message $(Get-ItemProperty -Path "$Path") | Out-Null
      Write-Log -Message "Registery Key =" -LogLevel "INFO" | Out-Null
      Write-Log -Message $(Get-ItemProperty -Path "$Path" | Select-Object "$Value") | Out-Null
      Write-Log -Message "Registery Key Value =" -LogLevel "INFO" | Out-Null
      Write-Log -Message ($(Get-ItemProperty -Path "$Path" | Select-Object "$Value" | Select-Object -ExpandProperty "$Value")).gettype() | Out-Null
      return $true
    }
    else  {
      Write-Log -Message "Registry key $Path\$Value does not exist" -LogLevel "INFO" | Out-Null
      return $false
    }

  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR" | Out-Null
    Write-Log -Message $($PSitem) -LogLevel "ERROR" | Out-Null
    return $false
  }
}