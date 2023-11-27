# Get public and private function definition files.
$Public = @( Get-ChildItem -Path $PSScriptRoot\Public\*.ps1 -ErrorAction SilentlyContinue )
$Private = @( Get-ChildItem -Path $PSScriptRoot\Private\*.ps1 -ErrorAction SilentlyContinue )

# Dot source the files
Foreach ($import in @($Public + $Private )) {
    Try {
        . $import.FullName
        # Write-host "Importing $($import.FullName)" -ForegroundColor [YELLOW]
        Export-ModuleMember -Function $Public.Basename
        #Export-ModuleMember -Variable "script:defaultfilepath", "script:loglocation"
    }
    Catch {
        Write-Error -Message "Failed to import function $($import.fullname): $_"
    }
}