<#
  .Synopsis
    Check WMI service status.
  .Description
    This function checks the status of the WMI (Windows Management Instrumentation) service on the source server.
  .Example
    Get-WMIServiceStatus
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-WMIServiceStatus {

  $check = "WMI Service Status"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"
  try {
    # Check WMI service status
    $GetWMIService = (Get-Service "Winmgmt").Status

    if ($GetWMIService -eq 'Running') {
      $value = "[GREEN]"
      Write-Log -Message "The check ""$check"" output is $value"
      $Action = "No action required. WMI Service is running."
      Write-Log -Message $Action
    }
    else {
      $value = "[RED]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
      $Action = "WMI Service is not running."
      Write-Log -Message $Action -LogLevel "ERROR"
    }
  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    $Action = "An error occurred when running Get-WMIServiceStatus."
    Write-Log -Message $Action -LogLevel "ERROR"
    Write-Log -Message "$($_)" -LogLevel "ERROR"
    $value = "[RED]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
  }
  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}
