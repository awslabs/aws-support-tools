<#
  .Synopsis
    Check the value of System wide proxy settings.
  .Description
    This is a public function used to check the value of System wide proxy settings using netsh winhttp show proxy.
  .Example
    Get-SystemWideProxy
  .INPUTS
    Skip = Switch to skip this function if the agent is not installed.
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Note "$Action"
#>
Function Get-SystemWideProxy {
  [CmdletBinding()]
  param (
    [Switch]$Skip
  )

  $check = "WinHTTP system-wide proxy"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  Write-Log -Message "This proxy settings mainly used to by Windows Update service"

  if (-not ($Skip)) {
    try {
      # based on https://gist.github.com/itn3000/b414da5337b7d229d812ec3ddcffb446
      $MethodDefinition = @'
using System.Runtime.InteropServices;
public enum AccessType
{
    DefaultProxy = 0,
    NamedProxy = 3,
    NoProxy = 1
}
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct WINHTTP_PROXY_INFO
{
    public AccessType AccessType;
    public string Proxy;
    public string Bypass;
}
public class WinHttp
{
    [DllImport("winhttp.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool WinHttpGetDefaultProxyConfiguration(ref WINHTTP_PROXY_INFO config);
}
'@
      $Assembly = Add-Type -TypeDefinition $MethodDefinition -PassThru
      $object = New-Object WINHTTP_PROXY_INFO
      $object.AccessType = [AccessType]::DefaultProxy
      $ret = [WinHttp]::WinHttpGetDefaultProxyConfiguration([ref]$object)
      if ($object.AccessType -eq "NoProxy") {
        $value = "[GREEN]"
        Write-Log -Message "The check ""$check"" output is $value"
        $Action = "No action required. There is no ProxyServer(s) configured for WinHTTP system-wide proxy."
        Write-Log -Message $Action
      }
      else {
        $value = "[YELLOW]"
        Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
        $Action = "Current WinHTTP system-wide proxy settings for LocalSystem account is " + $object.Proxy + " as ProxyServer(s), and " + $object.Bypass + " as Bypass list. Windows Update service would use these settings"
        Write-Log -Message $Action -LogLevel "WARN"
      }
    }
    catch {
      Write-Log -Message "Failed..." -LogLevel "ERROR"
      $Action = "An error occurred when running Get-SystemWideProxy."
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