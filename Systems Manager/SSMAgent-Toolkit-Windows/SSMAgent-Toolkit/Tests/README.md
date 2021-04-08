# SSM Agent Toolkit - Test

This test is based on [Pester](https://github.com/pester/Pester). The test will go through invoking all the functions with different inputs to test all possible scenarios.

## Output

Sample output in [Output.txt](https://github.com/awslabs/aws-support-tools/raw/master/Systems%20Manager/SSMAgent-Toolkit-Windows/SSMAgent-Toolkit/Tests/Output.txt)

## Usage

After downloading the ZIP file and extract for SSMAgent-Toolkit. Run the followings as administrator in PowerShell.

```powershell
Import-Module .\SSMAgent-Toolkit.psm1;Invoke-SSMChecks
Invoke-Pester -Output Detailed
```

### Prerequisites

Get the latest version of Pester 

### Installing

No installation is required on Windows systems.

## Authors

* Ali Alzand