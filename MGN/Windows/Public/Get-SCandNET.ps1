<#
  .Synopsis
    Check existence of specific files.
  .Description
    This function checks if the sc.exe (service control executable) and net.exe (net command executable) files exist in the system32 directory.
  .Example
    Get-SCandNET
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-SCandNET {

  $check = "SC.exe and NET.exe"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  try {

    $netExePath = "$env:SystemRoot\System32\net.exe"
    $scExePath = "$env:SystemRoot\System32\sc.exe"

    $netExeExists = Test-Path $netExePath
    $scExeExists = Test-Path $scExePath
    $missing = @()

    if ($netExeExists -and $scExeExists) {
      $value = "[GREEN]"
      Write-Log -Message "The check ""$check"" output is $value"
      $Action = "No action required. Both sc.exe (service control executable) and net.exe (net command executable) exist in $env:SystemRoot\System32."
      Write-Log -Message $Action
    }
    else {
      if ($netExeExists -eq $False) {
        $missing += "net.exe"
      }
      if ($scExeExists -eq $False) {
        $missing += "sc.exe"
      }

      $missing = $missing -join " and "
      $value = "[RED]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
      $Action = "Unable to locate $missing in the $env:SystemRoot\System32 folder. Please see our documentation for further information - https://docs.aws.amazon.com/mgn/latest/ug/Troubleshooting-Agent-Issues.html#Installation-Failed-Windows"
      Write-Log -Message $Action -LogLevel "ERROR"
    }
  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    $Action = "An error occurred when running Get-SCandNET."
    Write-Log -Message $Action -LogLevel "ERROR"
    Write-Log -Message "$($_)" -LogLevel "ERROR"
    $value = "[RED]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
  }

  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}
