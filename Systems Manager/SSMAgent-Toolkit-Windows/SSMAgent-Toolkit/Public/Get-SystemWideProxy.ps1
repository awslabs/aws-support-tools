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
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-SystemWideProxy {
  [CmdletBinding()]
  param (
    [Switch]$Skip
  )
    
  $check = "WinHTTP system-wide proxy"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"
  
  if (-not ($Skip)) {
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
      $value = "N/A"
      $note = "There is no ProxyServer(s) configured for WinHTTP system-wide proxy. Note: This proxy settings mainly used to by Windows Update service"
      Write-Log -Message "$note. Note: This proxy settings mainly used to by Windows Update service"
    }
    else {
      $value = "ProxyServer(s) = " + $object.Proxy + ". Bypass list = " + $object.Bypass
      $note = "Current WinHTTP system-wide proxy settings for LocalSystem account is " + $object.Proxy + " as ProxyServer(s), and " + $object.Bypass + " as Bypass list. Windows Update service would use these settings."
      Write-Log -Message $note -LogLevel "WARN"
    }
  }
  else {
    $value = "Skip"
    $note = "This test skipped since the service is not available"
    Write-Log -Message "The WinHTTP system-wide proxy check skipped since the service is not available" -LogLevel "WARN"
  }

  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}