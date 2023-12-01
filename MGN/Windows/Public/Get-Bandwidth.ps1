<#
  .Synopsis
    Check the available bandwidth for the Source Server.
  .Description
    This function will run a bandwidth test using librespeed-cli (same utility as the ce-ssl-speedtest AMI) - https://github.com/librespeed/speedtest-cli.
  .Example
    Check-Bandwidth -SpeedTestIP 10.20.30.40
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>



Function Get-Bandwidth {
  param (
    # Test server IP address
    [IPAddress]$SpeedTestIP
  )
  if (!($SpeedTestIP)) {
    $SpeedTestIP = Read-Host -Prompt 'Enter the IP Address of the Speed Test Instance'
  }

  $check = "Upload Bandwidth"
  Write-Log -Message "___________________________________________________________________"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  try {
    ## Check bandwidth ##
    Write-Log -Message "Downloading librespeed-cli utility..."
    $BandwidthOutput = (New-Item -Path "$tempDirectory\Bandwidth Checker" -ItemType Directory -Force).FullName
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "https://github.com/librespeed/speedtest-cli/releases/download/v1.0.10/librespeed-cli_1.0.10_windows_amd64.zip" -OutFile "$BandwidthOutput\librespeed-cli_1.0.10_windows_amd64.zip"
    Add-Type -Assembly "system.io.compression.filesystem"
    [System.IO.Compression.ZipFile]::ExtractToDirectory("$BandwidthOutput\librespeed-cli_1.0.10_windows_amd64.zip", "$BandwidthOutput\librespeed-cli_1.0.10_windows_amd64")
    Remove-Item "$BandwidthOutput\librespeed-cli_1.0.10_windows_amd64.zip"
    Write-Log -Message "Creating 'servers.json' file..."
    [object[]]$object = [pscustomobject]@{id = 1; name = "SpeedTest-Instance"; server = "https://" + $SpeedTestIP + ":1500/speedtest/"; dlURL = "garbage.php"; ulURL = "empty.php"; pingURL = "empty.php"; getIpURL = "getIP.php" }
    ConvertTo-Json -InputObject $object | Out-File "$BandwidthOutput\servers.json" -Encoding ascii
    Write-Log -Message "'servers.json' file was created successfully."
    Write-Log -Message "Running bandwidth test..."
    & $BandwidthOutput\librespeed-cli_1.0.10_windows_amd64\librespeed-cli.exe --local-json "$BandwidthOutput\servers.json" --server 1 --skip-cert-verify --share --simple --concurrent 5 --chunks 20 2>&1 | ForEach-Object ToString > $BandwidthOutput\bandwidth_results.txt
    $bandwidthresults = Get-content $BandwidthOutput\bandwidth_results.txt
    Write-Log -Message "Getting Bandwidth Results..."
    Write-Log -Message "$bandwidthresults"
    Remove-Item "$BandwidthOutput\librespeed-cli_1.0.10_windows_amd64"-Force -Recurse
    $cleanlines = $bandwidthresults | ForEach-Object {
      $line = $_ -replace '^\s*'
      $line = $line -replace '[^\x20-\x7E]', ''
      $line
    }
    $bandwidthresults = $cleanlines[2]
    $value = "[YELLOW]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "WARN"
    $Action = "The Bandwidth Upload speed is $bandwidthresults. Compare this Bandwidth result with the results from the ""Disk Write Activity Average"" cmdlet during a time of high disk activity to ensure the bandwidth is sufficient."
    Write-Log -Message $Action -LogLevel "WARN"
  }
  catch {
    Write-Log -Message "Failed..." -LogLevel "ERROR"
    $Action = "An error occurred when running Get-Bandwidth."
    Write-Log -Message $Action -LogLevel "ERROR"
    Write-Log -Message "$($_)" -LogLevel "ERROR"
    $value = "[RED]"
    Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
  }
  $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}
