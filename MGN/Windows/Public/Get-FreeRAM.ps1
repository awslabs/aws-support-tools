<#
  .Synopsis
    Check available free RAM.
  .Description
    This function checks the amount of free RAM on the system and verifies if it meets the minimum requirement of 300 MB.
  .Example
    Get-FreeRAM
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-FreeRAM {

  $check = "Free RAM"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  try {
    # Check available free RAM
    $freePhysicalMemory = (Get-CimInstance -ClassName Win32_OperatingSystem).FreePhysicalMemory / 1KB
    $roundedMemoryInMB = [Math]::Round($freePhysicalMemory)

    if ($freePhysicalMemory -gt 300) {
      $value = "[GREEN]"
      Write-Log -Message "The check ""$check"" output is $value"
      $Action = "No action required. The system has $roundedMemoryInMB MB of RAM free RAM"
      Write-Log -Message $Action
    }
    else {
      $value = "[RED]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
      $Action = "The source machine has $roundedMemoryInMB MB of RAM free. Verify that at least 300 MB of free RAM to run the AWS Replication Agent https://docs.aws.amazon.com/mgn/latest/ug/installation-requirements.html#general-requirements2."
      Write-Log -Message $Action -LogLevel "ERROR"
    }
  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    $Action = "An error occurred when running Get-FreeRAM."
    Write-Log -Message $Action -LogLevel "ERROR"
    Write-Log -Message "$($_)" -LogLevel "ERROR"
    $value = "[RED]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
  }

  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}