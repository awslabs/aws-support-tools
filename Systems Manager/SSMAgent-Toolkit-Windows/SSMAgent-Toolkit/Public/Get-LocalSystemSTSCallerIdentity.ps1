<#
  .Synopsis
    Create a schedule task under system account to make GetCallerIdentity api call.
  .Description
    This is a public function will create a schedule task under system account to make GetCallerIdentity api call - https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html. This to returns the IAM user or role arn whose credentials are used to call the operation under LocalSystem account.
  .Example
    Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation "C:\SSMAgent-Toolkit"
    Get-LocalSystemAccountSTSCallerIdentity -ParentDirectoryLocation "C:\SSMAgent-Toolkit" -Skip $true
  .INPUTS
    $ParentDirectoryLocation - The location of the current module
    $Skip - If this test would be skipped
  .OUTPUTS                                                                            
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function Get-LocalSystemAccountSTSCallerIdentity {
  [CmdletBinding()]
  param (
    [String]$ParentDirectoryLocation,
    [String]$Skip = $false
  )
    
  $check = "LocalSystem account user API assume role"
  Write-Log -Message "New check....."
  Write-Log -Message "$check"

  if ($Skip -ne $true) {
    try {
      $OutputPath = "$ParentDirectoryLocation\temp\STSCallerIdentity.xml"

      $ScheduledTaskName = "Get-LocalSystemAccountSTSCallerIdentityTask"
      $ScheduledTaskNameDescription = "Run Get-STSCallerIdentity under LocalSystem Account as part of SSMAgent-Toolkit"

      $ScheduledTaskCommand = '$STSOutput = Get-STSCallerIdentity;$xml = $STSOutput | Export-Clixml  -ErrorAction Ignore -Path ' + $OutputPath
        
      $ScheduledTaskAction = New-ScheduledTaskAction -Execute 'Powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -command `"$ScheduledTaskCommand`""
      $ScheduledTaskSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
        
      Register-ScheduledTask -Action $ScheduledTaskAction -TaskName $ScheduledTaskName -Description $ScheduledTaskNameDescription -Settings $ScheduledTaskSettings -User "System" -ErrorAction Stop > $null
      Start-ScheduledTask -TaskName $ScheduledTaskName

      While ((Get-ScheduledTask -TaskName $ScheduledTaskName).State -ne 'Ready') {}

      Unregister-ScheduledTask -TaskName $ScheduledTaskName -Confirm:$false

      $STSCallerIdentityARN = (Import-Clixml -Path $OutputPath).arn

      $value = $STSCallerIdentityARN
      $note = "The role and the instance in the ARN should match the role in the metadata and the current instanceID"
      Write-Log -Message "The output of Get-STSCallerIdentity under the system account is $STSCallerIdentityARN."
    }
    catch {
      Write-Log -Message "Failed..." -LogLevel "ERROR"
      Write-Log -Message "$($_)" -LogLevel "ERROR"
      $value = "Fail"
      $note = "The process of creating and running the scheduled task failed. Please check the logs for more information."
    }
  }
  else {
    $value = "Skip"
    $note = "This test skipped since there is no IAM instance profile attached to the instance or EC2 instance metadata is not accessible"
    Write-Log -Message $note -LogLevel "WARN"
  }

  return New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
}