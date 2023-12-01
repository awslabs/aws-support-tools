<#
  .Synopsis
    Check the Boot Mode and Boot Disk Type of the source machine.
  .Description
    Check the boot mode of the source machine (Legacy BIOS or UEFI) and the Boot Disk Type (Basic or Dynamic) and provide a status message.
  .Example
    Get-BootMode
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-BootMode {

  $check = "Boot Mode"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  try {
    # Here we are getting the Boot Disk number in the format of "Disk 0" which we will use to parse the diskpart output below.
    Write-Log -Message "Getting the Boot Partition..."
    $bootpartition = Get-CimInstance Win32_DiskPartition | Where-Object { $_.BootPartition -eq "True" }
    Write-Log -Message $bootpartition
    $bootdisk = ($bootpartition.Name)
    $bootdisk = $bootdisk.Substring(0, $bootdisk.IndexOf(','))
    $bootdisk = $bootdisk.Replace('#', '')
    Write-Log -Message "The Boot Disk is: $bootdisk"
    # Here we are taking the boot disk number ("Disk 0") and iterating through the text file created from the diskpart output,
    # and then checking for a "*"" in the DYN and GPT column.
    New-Item -ItemType File -Path "$tempDirectory\diskpart_commands.txt" -Value "list disk" -Force | Out-Null
    $diskPartOutput = diskpart /s $tempDirectory\diskpart_commands.txt
    write-log -Message "The output of diskpart is: "
    Write-Log -Message $diskPartOutput
    diskpart /s $tempDirectory\diskpart_commands.txt > $tempDirectory\DiskPartOutput.txt
    (Get-Content $tempDirectory\DiskPartOutput.txt) | Where-Object { $_.trim() -ne "" } | Select-Object -skip 5 | Set-Content $tempDirectory\DiskPartOutput.txt
    $listdisk = (Get-Content $tempDirectory\DiskPartOutput.txt)
    Write-Log -Message $listdisk
    ForEach ($disk in $listdisk) {
      If ($disk -like "  $bootdisk *") {
        Set-Content $tempDirectory\DiskPartOutput.txt $disk
        $listdisk = (Get-Content $tempDirectory\DiskPartOutput.txt)
        break
      }
    }
    $isdynamic = $listdisk.substring(46, 1)
    $isgpt = $listdisk.substring(51, 1)
    write-log "The boot disk partition table output"
    Write-Log -Message "DYN: $isdynamic"
    Write-Log -Message "GPT: $isgpt"

    If (($isdynamic -eq " ") -and ($isgpt -eq " ")) {
      $value = "[YELLOW]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
      $Action = "The Boot Disk is Basic, and the Boot Mode is Legacy BIOS. Select the Legacy BIOS option for Boot Mode during Target Launch - https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ami-boot.html"
      Write-Log -Message $Action -LogLevel "WARN"
    }
    elseif (($isdynamic -eq "*") -and ($isgpt -eq " ")) {
      $value = "[YELLOW]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
      $Action = "The Boot Disk is Dynamic, and the Boot Mode is Legacy BIOS. Select the Legacy BIOS option for Boot Mode during Target Launch - https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ami-boot.html"
      Write-Log -Message $Action -LogLevel "WARN"
    }
    elseif (($isdynamic -eq " ") -and ($isgpt -eq "*")) {
      $value = "[YELLOW]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
      $Action = "The Boot Disk is Basic, and the Boot Mode is UEFI. We recommend selecting the UEFI Boot Mode option to keep the same settings as the source machine https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ami-boot.html"
      Write-Log -Message $Action -LogLevel "WARN"
    }
    elseif (($isdynamic -eq "*") -and ($isgpt -eq "*")) {
      $value = "[YELLOW]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
      $Action = "The Boot Disk is Dynamic, and the Boot Mode is UEFI. Select the UEFI option for Boot Mode during Target Launch, as Legacy BIOS is unsupported for Dynamic + UEFI disks - https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ami-boot.html"
      Write-Log -Message $Action -LogLevel "WARN"
    }
    else {
      $value = "[RED]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
      $Action = "The Boot Disk and Boot Mode of the source machine is unknown. Please check the Disk Management properties of the boot disk, as well as the bcdedit output to get the Disk Type and Boot Mode."
      Write-Log -Message $Action -LogLevel "ERROR"
    }
  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    $Action = "An error occurred when running Get-BootMode."
    Write-Log -Message $Action -LogLevel "ERROR"
    Write-Log -Message "$($_)" -LogLevel "ERROR"
    $value = "[RED]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
  }
  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}