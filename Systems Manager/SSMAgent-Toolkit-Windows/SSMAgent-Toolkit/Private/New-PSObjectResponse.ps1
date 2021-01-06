<#
  .Synopsis
    Create a standard object
  .Description
    This is a helper function to create a standard object for each check
  .Example
    New-PSObjectResponse -Check "$check" -Status "$value" -Note "$note"
#>
Function New-PSObjectResponse {
  [CmdletBinding()]
  param (
    [String]$Check,
    [String]$Status,
    [String]$Note
  )    
  return [PSCustomObject]@{
    "Check" = $Check;
    "Value" = $Status;
    "Note"  = $Note
  }
}