<#
  .Synopsis
    Check the value of agent proxy value configured under registry
  .Description
    This is a public function used to check the value of agent proxy value configured under registry and return the value.
  .Example
    Get-AgentProxySettings -Message "Error message" -Key "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\AmazonSSMAgent"
  .INPUTS
    Key = The registry path.
    Skip = Default is false. This script will be skipped if the agent is not installed.
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-AgentProxySettings {
  [CmdletBinding()]
  param (
    [String]$Key = "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\AmazonSSMAgent",
    [String]$Skip = $false
  )
  $check = "SSM Agent Proxy Setting"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if ($Skip -ne $true) {
    If (-not (Test-RegistryValue -Path $Key -Value 'Environment')) {
      $value = "N/A"
      $note = "There is no proxy setting for SSM Agent"
      Write-Log -Message "There is no proxy setting for SSM Agent"
    }
    else {
      $value = (Get-Item -Path $Key).GetValue("Environment")
      $note = "SSM Agent configured with proxy settings"
      Write-Log -Message "SSM Agent configured with proxy settings: $value" -LogLevel "WARN"
    }
  }
  else {
    $value = "Skip"
    $note = "This test skipped since the service is not available"
    Write-Log -Message "The SSM Agent Proxy Setting check skipped since the service is not available" -LogLevel "WARN"
  }
  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}