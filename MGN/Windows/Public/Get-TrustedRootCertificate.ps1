<#
  .Synopsis
    Check Trusted Root Certificates installed
  .Description
    This will check to make sure the required Trusted Root Certificates are installed for Agent installation requirements.
  .Example
    Get-TrustedRootCertificate
  .OUTPUTS
    Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"
#>
Function Get-TrustedRootCertificate {

    $check = "Trusted Root Certificates"
    Write-Log -Message "___________________________________________________________________"
    Write-Log -Message "New check....."
    Write-Log -Message "$check"

    try {
        $amazoncerts = @(
            "CN=Amazon Root CA 1, O=Amazon, C=US",
            "CN=Amazon Root CA 2, O=Amazon, C=US",
            "CN=Amazon Root CA 3, O=Amazon, C=US",
            "CN=Amazon Root CA 4, O=Amazon, C=US"
        )
        $starfieldcert = @(
            "CN=Starfield Services Root Certificate Authority - G2, O=`"Starfield Technologies, Inc.`", L=Scottsdale, S=Arizona, C=US"
        )
        $store = (Get-ChildItem -Path cert:\LocalMachine\Root).Subject

        $amazoncertstatus = $False
        $starfieldcertstatus = $False

        ForEach ($amazoncert in $amazoncerts) {
            ForEach ($cert in $store) {
                if ($amazoncert -eq $cert) {
                    Write-Log -Message "The following certificate is installed: $amazoncert"  -LogLevel "INFO"
                    $amazoncertstatus = $True
                    break
                }
                else {
                    continue
                }
            }
        }


        ForEach ($sfcert in $starfieldcert) {
            ForEach ($cert in $store) {
                if ($sfcert -eq $cert) {
                    Write-Log -Message "The following certificate is installed: $sfcert"  -LogLevel "INFO"
                    $starfieldcertstatus = $True
                    break
                }
                else {
                    continue
                }
            }
        }

        Write-Log -Message "Amazon Certificate installation status is: $amazoncertstatus" -LogLevel "INFO"
        Write-Log -Message "Starfield Certificate installation status is: $starfieldcertstatus" -LogLevel "INFO"

        if ($amazoncertstatus -and $starfieldcertstatus -eq $True) {
            $value = "[GREEN]"
            Write-Log -Message "The check ""$check"" output is $value"
            $Action = "No action required. All required certificates are installed."
            Write-Log -Message $Action -LogLevel "INFO"
        }
        else {
            $missingcertificates = @()
            if ($amazoncertstatus -eq $False) {
                $missingcertificates += "Amazon Certificate"
            }
            if ($starfieldcertstatus -eq $False) {
                $missingcertificates += "Starfield Certificate"
            }

            $missingcertificates = $missingcertificates -join " and "


            $value = "[RED]"
            Write-Log -Message "Amazon Certificate installation status is: $amazoncertstatus" -LogLevel "ERROR"
            Write-Log -Message "Starfield Certificate installation status is: $starfieldcertstatus" -LogLevel "ERROR"
            Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
            $Action = "Please ensure the $missingcertificates is installed by following our documentation here - https://docs.aws.amazon.com/mgn/latest/ug/Troubleshooting-Agent-Issues.html#error-certificate-verify-failed"
            Write-Log -Message $Action -LogLevel "ERROR"
        }
    }
    catch {
        Write-Log -Message "Failed..." -LogLevel "ERROR"
        $Action = "An error occurred when running Get-TrustedRootCertificate."
        Write-Log -Message $Action -LogLevel "ERROR"
        Write-Log -Message "$($_)" -LogLevel "ERROR"
        $value = "[RED]"
        Write-Log -Message "The check ""$check"" output is $value" -LogLevel "ERROR"
    }

    $Output.Add((Set-PSObjectResponse -Check "$check" -Status "$value" -Action "$Action"))
}

