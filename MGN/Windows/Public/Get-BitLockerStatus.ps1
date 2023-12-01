<#
  .Synopsis
    Check BitLocker status.
  .Description
    This function checks the status of BitLocker disk encryption. MGN does not support OS-based disk encryption features such as BitLocker. This should be disabled before using our services. https://docs.aws.amazon.com/mgn/latest/ug/FAQ.html#does-mgn-bitlocker
  .Example
    Get-BitLockerStatus
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-BitLockerStatus {
  # [CmdletBinding()]
  # param (
  #     [String]$Token
  # )

  $check = "BitLocker"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  try {
    # Check BitLocker status
    $bitLockerCmdlet = Get-Command -Name "Get-BitLockerVolume" -ErrorAction SilentlyContinue

    if ($bitLockerCmdlet) {
      $encryptionStatus = Get-BitLockerVolume | Select-Object -ExpandProperty EncryptionPercentage -First 1 -ErrorAction SilentlyContinue

      if ($null -ne $encryptionStatus) {
        $value = "[RED]"
        Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
        $Action = "BitLocker is enabled on the source machine. AWS MGN does not support OS-based disk encryption features. These should be deactivated before using AWS MGN. Please see https://docs.aws.amazon.com/mgn/latest/ug/FAQ.html#does-mgn-bitlocker"
        Write-Log -Message $Action -LogLevel "ERROR"
      }
      else {
        $value = "[GREEN]"
        Write-Log -Message "The check ""$check"" output is $value"
        $Action = "No action required. BitLocker is not enabled on the source machine."
        Write-Log -Message $Action
      }
    }
    else {
      $value = "[GREEN]"
      Write-Log -Message "The check ""$check"" output is $value"
      $Action = "No action required. BitLocker is not available on this source machine."
      Write-Log -Message $Action
    }
  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    $Action = "An error occurred when running Get-BitLockerStatus."
    Write-Log -Message $Action -LogLevel "ERROR"
    Write-Log -Message "$($_)" -LogLevel "ERROR"
    $value = "[RED]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
  }
  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}
