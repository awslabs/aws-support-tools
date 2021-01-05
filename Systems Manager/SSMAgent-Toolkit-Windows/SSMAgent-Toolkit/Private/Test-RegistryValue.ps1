<#
  .Synopsis
    Test registry value 
  .Description
    This is a helper function to test registry value and whater if the key is available or not.
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
    if (Test-Path -Path "$Path\$Value") {
      Get-ItemProperty -Path $Path | Select-Object -ExpandProperty $Value -ErrorAction Stop | Out-Null
      return $true
    }
    else {
      Write-Log -Message "Registry key $Path\$Value does not exist" -LogLevel "INFO"
      return $false
    }

  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    Write-Log -Message $($PSitem) -LogLevel "ERROR"
    return $false
  }

}