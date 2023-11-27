<#
  .Synopsis
    Check if the source machine is a domain controller or not.
  .Description
    Check if Active Directory Domain Services feature is installed and the source machine is promoted to domain controller.
  .Example
    Get-DomainControllerStatus -product $token
  .INPUTS
	  $product = String
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-DomainControllerStatus {
  [CmdletBinding()]
  param (
    [String]$product
  )

  $check = "AD Domain Controller"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if ($product -gt "1") {
    Write-Log -Message "Check if the AD-Domain-Services role is installed and if the source machine is a Domain Controller."

    try {
      $adFeature = Get-WindowsFeature -Name "AD-Domain-Services"

      Write-Log -Message "The output of Get-WindowsFeature for AD-Domain-Services role is: "
      Write-Log -Message $adFeature

      if ($adFeature.InstallState -eq "Installed" -and $product -eq "2") {
        $value = "[YELLOW]"
        Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
        $Action = "The source machine is AD Domain Controller. Please check Active Directory considration - https://docs.aws.amazon.com/mgn/latest/ug/General-Questions-FAQ.html#What-Active-Directory."
        Write-Log -Message $Action -LogLevel "WARN"
      }
      elseif ($adFeature.InstallState -eq "Installed" -and $product -eq "3") {
        $value = "[GREEN]"
        Write-Log -Message "The output of the ""$check"" check is $value"
        $Action = "No action required. The Active directory role is installed but the source machine is not a Domain Controller."
        Write-Log -Message $Action
      }
      else {
        $value = "[GREEN]"
        Write-Log -Message "The output of the ""$check"" check is $value"
        $Action = "No action required. The Active directory role can not be found."
        Write-Log -Message $Action
      }
    }
    catch {
      Write-Log -Message "Failed..." -LogLevel "ERROR"
      $Action = "An error occurred when running Get-DomainControllerStatus."
      Write-Log -Message $Action -LogLevel "ERROR"
      Write-Log -Message "$($_)" -LogLevel "ERROR"
      $value = "[RED]"
      Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
    }
  }
  else {
    $value = "[GREEN]"
    Write-Log -Message "The check ""$check"" output is $value"
    $Action = "No action required. The Active directory role can not be found."
    Write-Log -Message $Action
  }
  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}