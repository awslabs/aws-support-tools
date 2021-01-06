<#
  .Synopsis
    Write a log output 
  .Description
    This is a helper function to write a log output 
  .Example
    Write-Log -Message "info message"
    Write-Log -Message "Error message" -LogLevel "ERROR"
  .INPUTS
	  Message = Message 
	  LogLevel = default as "INFO"
  .OUTPUTS                                                                            
    Write-host the message with LogLevel and timestamp
    [2020-10-19T17:48:21.9656326-04:00] [INFO] amazonssmagent service is available.
#>

function Write-Log {
  [CmdletBinding()]
  param (
    [Parameter(Mandatory = $true)]
    $Message,
    [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG')]
    $LogLevel = 'INFO'
  )
    
  $timestamp = Get-Date -Format o
  Write-Host "[$($timestamp)] [$($LogLevel)] $($Message) "

}