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
    Write-output the message with LogLevel and timestamp
    [2020-10-19T17:48:21.9656326-04:00] [INFO] amazonssmagent service is available.
#>

function Write-Log {
  [CmdletBinding()]
  param (
    [Parameter(Mandatory = $true)]
    $Message,
    [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG')]
    $LogLevel = 'INFO',
    [Switch]$ConsoleOutput,
    [Switch]$All,
    [Switch]$forTesting = $false
  )

  $timestamp = Get-Date -Format o
  if ($ConsoleOutput -or $forTesting -or -not $LogsDestination) {
    Write-output "[$($timestamp)] [$($LogLevel)] $($Message)"
  }
  elseif ($All) {
    Write-output "[$($timestamp)] [$($LogLevel)] $($Message)"
    Write-output "[$($timestamp)] [$($LogLevel)] $($Message) " | out-file $LogsDestination -Append -Encoding utf8 -ErrorAction Continue
  }
  elseif ($Message.GetType().Name -ne "String") {
    Write-output "[$($timestamp)] [$($LogLevel)]"$($Message) | out-file $LogsDestination -Append -Encoding utf8 -ErrorAction Continue
  }
  else {
    Write-output "[$($timestamp)] [$($LogLevel)] $($Message) " | out-file $LogsDestination -Append -Encoding utf8 -ErrorAction Continue
  }
}