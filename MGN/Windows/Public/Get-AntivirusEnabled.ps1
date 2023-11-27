<#
  .Synopsis
    Check antivirus status.
  .Description
    This function checks if an antivirus software is enabled on the system by querying the Windows Security Center and the AntiVirusProduct class. It warns about enabled antivirus software.
    In the context of Windows Security Center and the AntiVirusProduct class, we check the productState property which indicates the status of an antivirus product.
    In this function I used the most common productState values that indicate an antivirus product is enabled:
    262144: Antivirus is up to date and functioning properly.
    266240: Antivirus is out of date but still functioning.
    393472: Antivirus is up to date but is not currently scanning for malware.
    397312: Antivirus is out of date and is not scanning for malware.
    These values used represent different states of the antivirus product based on the Windows Security Center status. Note: The specific values may vary depending on the antivirus software and the implementation of the AntiVirusProduct class by the antivirus vendors.
    Ref: https://mcpforlife.com/2020/04/14/how-to-resolve-this-state-value-of-av-providers/
    Ref: https://www.nextofwindows.com/how-to-tell-what-antivirus-software-installed-on-a-remote-windows-computer
  .Example
    Get-AntivirusEnabled
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-AntivirusEnabled {
    # [CmdletBinding()]
    # param (
    #     [String]$Token
    # )

    $check = "Antivirus"
    Write-Log -Message "___________________________________________________________________"
    Write-Log -Message "New check....."
    Write-Log -Message "$check"

    $wmiPath1 = "root/SecurityCenter"
    $wmiClass1 = "AntiVirusProduct"

    $wmiPath2 = "root/SecurityCenter2"
    $wmiClass2 = "AntiVirusProduct"

    $antivirusEnabled = $false
    $displayName = ""

    try {
        # Check in root/SecurityCenter (older OS versions: Windows 2003/2008/XP/Vista)
        $wmi1 = Get-CimInstance -Namespace $wmiPath1 -ClassName $wmiClass1 -ErrorAction Stop

        if ($wmi1) {
            $antivirusProducts1 = $wmi1 | Where-Object { $null -ne $_.displayName }

            foreach ($product1 in $antivirusProducts1) {
                $productState1 = $product1.productState

                if (($productState1 -eq 266240) -or ($productState1 -eq 393472) -or ($productState1 -eq 397312)) {
                    $antivirusEnabled = $true
                    $displayName = $product1.displayName
                    break
                }
            }
        }

        # Check in root/SecurityCenter2 (newer OS versions: Windows 2008R2/Windows7 and later)
        $wmi2 = Get-CimInstance -Namespace $wmiPath2 -ClassName $wmiClass2 -ErrorAction Stop

        if ($wmi2) {
            $antivirusProducts2 = $wmi2 | Where-Object { $null -ne $_.displayName }

            foreach ($product2 in $antivirusProducts2) {
                $productState2 = $product2.productState

                if (($productState2 -eq 266240) -or ($productState2 -eq 393472) -or ($productState2 -eq 397312)) {
                    $antivirusEnabled = $true
                    $displayName = $product2.displayName
                    break
                }
            }
        }


        if ($antivirusEnabled) {
            $value = "[YELLOW]"
            Write-Log -Message "The check ""$check"" output is $value"
            $Action = "Antivirus is enabled: $displayName. Make sure the security software is allowing access to the MGN required endpoints and add the replication agent directory [64-bit - C:\Program Files(x86)\AWS Replication Agent][32-bit - C:\Program Files\AWS Replication Agent] to the allow-list."
            Write-Log -Message $Action -LogLevel "WARN"
            Write-Log -Message "Antivirus is enabled: $displayName." -LogLevel "WARN"
        }
        else {
            $value = "[YELLOW]"
            Write-Log -Message "The check ""$check"" output is $value"
            $Action = "We are unable to identify an Anti-virus software. If there is one installed, make sure the security software is allowing access to the MGN required endpoints and add the replication agent directory [64-bit - C:\Program Files(x86)\AWS Replication Agent][32-bit - C:\Program Files\AWS Replication Agent] to the allow-list."
            Write-Log -Message $Action
        }
    }
    catch {
        Write-Log -Message "Failed..." -LogLevel "ERROR"
        $Action = "The script failed or we are unable to identify an Anti-virus software. If there is one installed, make sure the security software is allowing access to the MGN required endpoints and add the replication agent directory [64-bit - C:\Program Files(x86)\AWS Replication Agent][32-bit - C:\Program Files\AWS Replication Agent] to the allow-list."
        Write-Log -Message $Action -LogLevel "ERROR"
        Write-Log -Message "$($_)" -LogLevel "ERROR"
        $value = "[YELLOW]"
        Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
    }
    $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}
