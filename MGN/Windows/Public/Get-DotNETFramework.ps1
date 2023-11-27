<#
  .Synopsis
    Check installed .NET Framework versions.
  .Description
    This function checks if the .NET Framework is installed on the source server and displays the installed versions on the output log.
  .Example
    Get-DotNetFrameworkVersion
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-DotNETFramework {
  # Based on Microsoft doc - https://learn.microsoft.com/en-us/dotnet/framework/migration-guide/how-to-determine-which-versions-are-installed
  # If the Full subkey is missing here - HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full
  # Then this means .NET Framework 4.5 or above isn't installed.

  $check = ".NET Framework Version"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  try {

    $ServerVersion = Get-CimInstance -ClassName win32_OperatingSystem | Select-Object -ExpandProperty Version


    if ($ServerVersion -clike "6.0*" -or $ServerVersion -clike "5.2*") {


      $checkpath35 = Test-Path -Path Registry::"HKLM\Software\Microsoft\NET Framework Setup\NDP\v3.5"
      $checkpath4 = Test-Path -Path Registry::"HKLM\Software\Microsoft\NET Framework Setup\NDP\v4\Full"
      Write-Log -Message "Checking for .NET Framework Verison 4..." -LogLevel "INFO"
      if ($checkpath4 -eq "True") {
        if ((Get-ItemProperty -Path Registry::"HKLM\Software\Microsoft\NET Framework Setup\NDP\v4\Full" | Select-Object -ExpandProperty "Install") -eq "1") {
          $version = Get-ItemProperty -Path Registry::"HKLM\Software\Microsoft\NET Framework Setup\NDP\v4\Full" | Select-Object -ExpandProperty "Version"
          $value = "[GREEN]"
          $Action = "No action required. .NET Framework $version is installed"
          Write-Log -Message $Action -LogLevel "INFO"
          break
        }
        else {
          Write-Log -Message ".NET Framework Version 4 is not installed" -LogLevel "WARN"
          Write-Log -Message "Checking for .NET Framework Version 3.5" -LogLevel "INFO"
          if ($checkpath35 -eq "True") {
            if ((Get-ItemProperty -Path Registry::"HKLM\Software\Microsoft\NET Framework Setup\NDP\v3.5" | Select-Object -ExpandProperty "Install") -eq "1") {
              $version = Get-ItemProperty -Path Registry::"HKLM\Software\Microsoft\NET Framework Setup\NDP\v3.5" | Select-Object -ExpandProperty "Version"
              $value = "[GREEN]"
              $Action = "No action needed. .NET Framework $version is installed"
              Write-Log -Message $Action -LogLevel "INFO"
            }
            else {
              $value = "[RED]"
              $Action = "Please ensure you have the necessary .NET Framework Version installed - https://docs.aws.amazon.com/mgn/latest/ug/Supported-Operating-Systems.html#Supported-OS-Considerations"
              Write-Log -Message $Action -LogLevel "ERROR"
            }
          }
        }
      }
      else {
        $value = "[RED]"
        $Action = "Please ensure you have the necessary .NET Framework Version installed - https://docs.aws.amazon.com/mgn/latest/ug/Supported-Operating-Systems.html#Supported-OS-Considerations"
        Write-Log -Message $Action  -LogLevel "ERROR"
      }
    }
    else {
      $release = Get-ItemProperty -Path Registry::"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" | Select-Object -ExpandProperty Release
      switch ($release) {
        { $_ -ge 378389 } { $version = Get-ItemProperty -Path Registry::"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" | Select-Object -ExpandProperty Version; break }
        default { $version = $null; break }
      }

      if ($version) {
        $value = "[GREEN]"
        $Action = "No action required. .NET Framework $version is installed"
        Write-Log -Message $Action -LogLevel "INFO"
      }
      else {
        $value = "[RED]"
        $Action = "Please ensure you have the necessary .NET Framework Version installed - https://docs.aws.amazon.com/mgn/latest/ug/Supported-Operating-Systems.html#Supported-OS-Considerations"
        Write-Log -Message $Action -LogLevel "ERROR"
      }
    }
  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    $Action = "An error occurred when running Get-DotNETFramework."
    Write-Log -Message $Action -LogLevel "ERROR"
    Write-Log -Message "$($_)" -LogLevel "ERROR"
    $value = "[RED]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
  }

  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}

