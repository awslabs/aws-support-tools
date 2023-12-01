<#
  .Synopsis
    Checks the Write Disk Activity on the source server to determine if it is sufficient with the bandwidth results.
  .Description
    This function will check the performance counters for the disks to calculate if the disk activity will cause any issues with replication speed.
  .Example
    Check-DiskActivity -WriteOpsTimer 30
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-DiskActivity {

  param (
    # Seconds for how long to run the disk write activity check for
    [String]$WriteOpsTimer
  )
  if (!($WriteOpsTimer)) {
    $WriteOpsTimer = Read-Host -Prompt 'Enter the amount of Seconds to check for Disk Write Activity'
  }
  $check = "Disk Write Activity Average"
  $check2 = "Disk Write Activity Maximum"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"
  Write-Log -Message "$check2"

  try {
    ## Check Write Activity for intervals set in inputs ##
    Write-Log -Message "Collecting write activity for $WriteOpsTimer seconds..."
    $totalwrites = (Get-Counter -Counter "\PhysicalDisk(_Total)\Disk Write Bytes/sec" -SampleInterval 1 -MaxSamples $WriteOpsTimer).CounterSamples.CookedValue
    Write-Log -Message "Listing the output of the PhysicalDisk(_Total)\Disk Write Bytes/sec counter:"
    Write-Log -Message $totalwrites
    $averagebytes = $totalwrites | Measure-Object -Average | Select-Object -ExpandProperty Average
    $maxbytes = $totalwrites | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum
    $averageMbps = [math]::Round($averagebytes * 8 / [Math]::Pow(1000, 2), 4)
    $maxMbits = [math]::Round($maxbytes * 8 / [Math]::Pow(1000, 2), 4)
    Write-Log -Message @"
Average (Mbps) = $averageMbps Mbps
Maximum (Mbits) = $maxMbits Mbps
"@
    Write-Log -Message  "To see each interval individually, please see $DiskActivityOutput\WriteBytes-$WriteOpsTimer-Seconds.txt (values are in Bytes)"

    $value = "[YELLOW]"
    $value2 = "[YELLOW]"
    Write-Log -Message "The results for the Disk Activity check: $value" -LogLevel "WARN"
    $Action = "The average for Disk Write Activity was $averageMbps Mbps. Compare this result with the Upload results from the Check-Bandwidth function to ensure it is sufficient."
    Write-Log -Message $Action -LogLevel "WARN"
    $Action2 = "The Max for Disk Write Activity was $maxMbits Mbps. Ensure your Staging Area disk settings will be sufficient if there are frequent maximum spikes of this value, to avoid Replication Backlog"
    Write-Log -Message $Action2 -LogLevel "WARN"
  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    $Action = "An error occurred when running Get-DiskActivity."
    Write-Log -Message $Action -LogLevel "ERROR"
    Write-Log -Message "$($_)" -LogLevel "ERROR"
    $value = "[RED]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
  }
  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
  $Output.Add((Set-PSObjectResponse -Check "$check2" -Status "$value2" -Action "$Action2"))
}
