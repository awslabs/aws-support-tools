<#
  .Synopsis
    Get the application version number
  .Description
    This is a helper function to get the application version number.
  .Example
    Get-AppVersionNumber -Path 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall' -Value 'Environment'
  .INPUTS
    Path = The registry path 
    AppName = The name of the application under the DisplayName under the registry
  .OUTPUTS                                                                            
    Return the version number under the registry
#>
function Get-AppVersionNumber {
  [CmdletBinding()]
  param (
    [String]$RegHive = "LocalMachine",
    [String]$Path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall", #Define the variable to hold the location of Currently Installed Programs
    [parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]$AppName
  )
  
  if ((Get-WmiObject -Class Win32_ComputerSystem).SystemType -match 'x64') {
    $RegView = [Microsoft.Win32.RegistryView]::Registry64
  }
  else {
    $RegView = [Microsoft.Win32.RegistryView]::Registry32
  }

  #Create an instance of the Registry Object and open the HKLM base key
  $reg = [microsoft.win32.registrykey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::$RegHive, $RegView) 

  #Drill down into the Uninstall key using the OpenSubKey Method
  $regkey = $reg.OpenSubKey($Path) 

  #Retrieve an array of string that contain all the subkey names
  $subkeys = $regkey.GetSubKeyNames() 

  #Open each Subkey and use GetValue Method to check the match values for AppName
  foreach ($key in $subkeys) {
    $thisKey = $Path + "\\" + $key 
    $thisSubKey = $reg.OpenSubKey($thisKey) 
    if ($($thisSubKey.GetValue("DisplayName")) -eq $AppName) {
      write-host $($thisSubKey.GetValue("DisplayVersion"))
      return [System.Version]$($thisSubKey.GetValue("DisplayVersion"))
      break
    }
    else {
      continue
    }
  } 
}